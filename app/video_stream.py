import cv2
import os
import time
import threading
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage


# --- ULTRA LOW LATENCY FFMPEG TUNING ---
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "protocol_whitelist;file,rtp,udp|"
    "fflags;nobuffer|"
    "flags;low_delay|"
    "probesize;32|"
    "analyzeduration:0|"
    "discard;corrupt|"
    "threads;auto|"
    "hwaccel;auto"
)


class TelloVideoThread(QThread):
    """
    Captures / decodes the Tello video stream at full speed.

    ML integration
    --------------
    Set self.ml_worker to an MLWorker instance and toggle self.ml_enabled
    to start/stop inference. Frames are submitted non-blocking — this thread
    is NEVER delayed by inference. The latest predictions are stored and drawn
    onto every outgoing frame as an overlay, so the video feed always runs at
    full speed while labels update at the model's own pace.
    """

    frame_received = pyqtSignal(QImage)
    recording_state_changed = pyqtSignal(bool, str)
    video_stats_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self.cap = None
        self.video_url = 'udp://@0.0.0.0:11111?overrun_nonfatal=1&fifo_size=5000000'

        # ML state
        self.ml_enabled: bool = False
        self.ml_worker = None               # injected by main.py

        # Video enhancement state
        self.filter_mode = "normal"
        self.capture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "captures"))
        self._state_lock = threading.Lock()
        self._last_frame = None
        self._recording_requested = False
        self._recording_path = ""
        self._writer = None
        self._fps_counter = 0
        self._fps_started_at = time.time()

    # ------------------------------------------------------------------
    # Public controls
    # ------------------------------------------------------------------

    def set_filter_mode(self, mode: str) -> None:
        with self._state_lock:
            self.filter_mode = mode

    def save_snapshot(self) -> str:
        with self._state_lock:
            frame = None if self._last_frame is None else self._last_frame.copy()

        if frame is None:
            return ""

        os.makedirs(self.capture_dir, exist_ok=True)
        path = os.path.join(self.capture_dir, f"snapshot_{datetime.now():%Y%m%d_%H%M%S}.jpg")
        return path if cv2.imwrite(path, frame) else ""

    def start_recording(self) -> str:
        os.makedirs(self.capture_dir, exist_ok=True)
        path = os.path.join(self.capture_dir, f"recording_{datetime.now():%Y%m%d_%H%M%S}.mp4")
        with self._state_lock:
            self._recording_requested = True
            self._recording_path = path
        return path

    def stop_recording(self) -> None:
        with self._state_lock:
            self._recording_requested = False
        if not self.isRunning():
            self._release_writer()

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def _apply_filter(self, frame, mode: str):
        if mode == "grayscale":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        if mode == "edges":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 70, 140)
            return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        if mode == "thermal":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)

        if mode == "night":
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_l = clahe.apply(l_channel)
            enhanced = cv2.merge((enhanced_l, a_channel, b_channel))
            return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        return frame

    def _ensure_writer(self, frame) -> None:
        if self._writer is not None:
            return

        with self._state_lock:
            path = self._recording_path

        h, w, _ = frame.shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(path, fourcc, 30.0, (w, h))

        if writer.isOpened():
            self._writer = writer
            self.recording_state_changed.emit(True, path)
        else:
            with self._state_lock:
                self._recording_requested = False
            self.recording_state_changed.emit(False, "Could not start recording")

    def _release_writer(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None
            self.recording_state_changed.emit(False, self._recording_path)

    def _update_fps(self) -> None:
        self._fps_counter += 1
        now = time.time()
        elapsed = now - self._fps_started_at
        if elapsed >= 1.0:
            self.video_stats_updated.emit({"fps": round(self._fps_counter / elapsed, 1)})
            self._fps_counter = 0
            self._fps_started_at = now

    # ------------------------------------------------------------------
    # Thread body
    # ------------------------------------------------------------------

    def run(self):
        self._stop_event.clear()

        self.cap = cv2.VideoCapture(self.video_url, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        while not self._stop_event.is_set():
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.1)
                continue

            try:
                ret, frame = self.cap.read()

                if self._stop_event.is_set():
                    break

                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                with self._state_lock:
                    filter_mode = self.filter_mode
                    recording_requested = self._recording_requested

                display_frame = self._apply_filter(frame, filter_mode)

                with self._state_lock:
                    self._last_frame = display_frame.copy()

                if recording_requested:
                    self._ensure_writer(display_frame)
                    if self._writer is not None:
                        self._writer.write(display_frame)
                elif self._writer is not None:
                    self._release_writer()

                # --- Submit to ML worker (non-blocking, never waits) ---
                if self.ml_enabled and self.ml_worker is not None:
                    self.ml_worker.submit_frame(frame)

                # --- Convert BGR → QImage and emit ---
                h, w, _ = display_frame.shape
                q_img = QImage(
                    display_frame.data, w, h, 3 * w,
                    QImage.Format.Format_RGB888
                ).rgbSwapped().copy()

                self.frame_received.emit(q_img)
                self._update_fps()

            except Exception as e:
                print(f"[VideoThread] Error: {e}")
                time.sleep(0.1)

        if self.cap:
            self.cap.release()
            self.cap = None
        self._release_writer()

    def stop(self):
        self._stop_event.set()
        self.stop_recording()

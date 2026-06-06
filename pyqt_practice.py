import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QGridLayout, 
                             QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, 
                             QSlider, QFrame, QLabel, QSizePolicy)
from PyQt6.QtCore import Qt

class TelloFullPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Tello Command Center')
        self.setMinimumWidth(800) # Increased minimum width for better spreading
        
        self.setStyleSheet("""
            QWidget { 
                background-color: #1a2a44; 
            }
            QPushButton { 
                background-color: #e0e0e0; 
                border: 1px solid #999; 
                font-weight: bold; 
                min-height: 50px;
                border-radius: 4px;
                color: #333;
                font-size: 14px;
            }
            QPushButton:pressed { 
                background-color: #bbbbbb; 
            }
            QLineEdit { 
                background-color: white; 
                border-radius: 2px; 
                padding: 5px; 
                color: black;
                font-weight: bold;
                min-height: 40px;
            }
            QCheckBox { 
                color: black; 
                font-weight: bold; 
                background-color: white; 
                padding: 5px;
                border-radius: 4px;
                min-height: 50px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 8px;
                background: white;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #334466;
                border: 1px solid #555;
                width: 14px;
                height: 18px;
                margin: -6px 0;
                border-radius: 4px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- SECTION 1: FLIGHT CONTROLS ---
        section1 = QGridLayout()
        self.setup_grid_columns(section1, 3)
        
        btn_data1 = [
            ('🚁 Takeoff 🚁', 0, 0), ('⬆️ Forward ⬆️', 0, 1), ('🅿️ Land 🅿️', 0, 2),
            ('⬅️ Left ⬅️', 1, 0), ('🚦 Command 🚦', 1, 1), ('➡️ Right ➡️', 1, 2),
            ('👆 Up 👆', 2, 0), ('⬇️ Back ⬇️', 2, 1), ('👇 Down 👇', 2, 2),
            ('🔄 Rotate ccw 🔄', 3, 0), ('🔄 Rotate cw 🔄', 3, 2)
        ]
        self.populate_grid(section1, btn_data1)

        emergency_ml_container = QWidget()
        emergency_ml_layout = QHBoxLayout(emergency_ml_container)
        emergency_ml_layout.setContentsMargins(0, 0, 0, 0)
        emergency_ml_layout.setSpacing(10)
        
        btn_emergency = QPushButton('🚨 EMERGENCY 🚨')
        btn_ml = QPushButton('Start ML Model')
        
        # Ensure buttons inside sub-containers also expand
        btn_emergency.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_ml.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        emergency_ml_layout.addWidget(btn_emergency)
        emergency_ml_layout.addWidget(btn_ml)
        section1.addWidget(emergency_ml_container, 3, 1)

        main_layout.addLayout(section1)
        main_layout.addWidget(self.create_separator())

        # --- SECTION 2: ACROBATICS & SETTINGS ---
        section2 = QGridLayout()
        self.setup_grid_columns(section2, 3)
        
        motor_container = QWidget()
        motor_lay = QHBoxLayout(motor_container)
        motor_lay.setContentsMargins(0, 0, 0, 0)
        motor_lay.setSpacing(5)
        
        btn_on = QPushButton("🥶 Motor ON 🥶")
        btn_off = QPushButton("📴 Motor OFF 📴")
        btn_on.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_off.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        motor_lay.addWidget(btn_on)
        motor_lay.addWidget(btn_off)
        section2.addWidget(motor_container, 0, 0)

        section2.addWidget(self.create_expanding_btn("⬆️ Flip forward ⬆️"), 0, 1)
        
        chk_joy = QCheckBox("Enter joysticks control")
        chk_joy.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        section2.addWidget(chk_joy, 0, 2)

        section2.addWidget(self.create_expanding_btn("⬅️ Flip left ⬅️"), 1, 0)
        section2.addWidget(self.create_expanding_btn("🏈 Throw&Fly 🏈"), 1, 1)
        section2.addWidget(self.create_expanding_btn("➡️ Flip right ➡️"), 1, 2)

        section2.addWidget(self.create_expanding_btn("📸 Take photo 📸"), 2, 0)
        section2.addWidget(self.create_expanding_btn("⬇️ Flip back ⬇️"), 2, 1)
        
        speed_container = QFrame()
        speed_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        speed_container.setStyleSheet("background-color: #e0e0e0; border-radius: 4px; border: 1px solid #999;")
        speed_layout = QHBoxLayout(speed_container)
        speed_layout.setContentsMargins(15, 2, 15, 2)
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("color: black; border: none; font-weight: bold; font-size: 11px;")
        speed_slider = QSlider(Qt.Orientation.Horizontal)
        speed_slider.setMinimum(10)
        speed_slider.setMaximum(100)
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(speed_slider)
        section2.addWidget(speed_container, 2, 2)

        main_layout.addLayout(section2)
        main_layout.addWidget(self.create_separator())

        # --- SECTION 3: LED & TEXT ---
        section3 = QGridLayout()
        self.setup_grid_columns(section3, 3)
        
        led_data = [
            ('🔴 Red LED 🔴', 0, 0), ('🟢 Green LED 🟢', 0, 1), ('🔵 Blue LED 🔵', 0, 2),
            ('🔵 Pulse Blue 🔵', 1, 0), ('⚫ Turn OFF LED ⚫', 1, 1), ('🚔 POLICE! 🚔', 1, 2)
        ]
        self.populate_grid(section3, led_data)

        # Text Input Group
        text_display_container = QWidget()
        text_display_layout = QHBoxLayout(text_display_container)
        text_display_layout.setContentsMargins(0, 0, 0, 0)
        input_name = QLineEdit("Mykola")
        btn_text = QPushButton("Display text")
        btn_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_display_layout.addWidget(input_name, 2) # Give line edit more stretch
        text_display_layout.addWidget(btn_text, 3)
        section3.addWidget(text_display_container, 2, 0)
        
        section3.addWidget(self.create_expanding_btn("Display pattern"), 2, 1)
        
        # Char Input Group
        char_input_container = QWidget()
        char_input_layout = QHBoxLayout(char_input_container)
        char_input_layout.setContentsMargins(0, 0, 0, 0)
        input_char = QLineEdit("M")
        btn_char = QPushButton("Display char")
        btn_char.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        char_input_layout.addWidget(input_char, 1)
        char_input_layout.addWidget(btn_char, 2)
        section3.addWidget(char_input_container, 2, 2)

        main_layout.addLayout(section3)
        self.setLayout(main_layout)

    def setup_grid_columns(self, grid, count=3):
        """Forces columns to stretch and fill the container width."""
        for i in range(count):
            grid.setColumnStretch(i, 1)
            grid.setColumnMinimumWidth(i, 50)

    def create_expanding_btn(self, label):
        btn = QPushButton(label)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn.setMinimumWidth(0)
        return btn

    def populate_grid(self, grid, data):
        for label, row, col in data:
            btn = self.create_expanding_btn(label)
            grid.addWidget(btn, row, col)

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #334466; max-height: 2px; border: none;")
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return line

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TelloFullPanel()
    window.show()
    sys.exit(app.exec())
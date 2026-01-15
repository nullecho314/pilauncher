import sys, json, subprocess, os
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QStackedWidget, QVBoxLayout, QHBoxLayout, QToolButton, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QBrush
from PyQt5.QtCore import Qt, QSize

VERSION = "1.0.0"  # sabit sürüm numarası

class Launcher(QWidget):
    def __init__(self, config_file="config.json"):
        super().__init__()
        self.config_file = config_file
        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.setWindowTitle("PiLauncher")
        if self.config.get("fullscreen", True):
            self.showFullScreen()

        # Arkaplan
        bg = self.config.get("background", None)
        if bg:
            palette = QPalette()
            if os.path.isabs(bg) or os.path.exists(bg):
                palette.setBrush(QPalette.Window, QBrush(QPixmap(bg)))
            else:
                palette.setColor(QPalette.Window, Qt.black)
            self.setPalette(palette)

        # Sayfa sistemi
        self.stack = QStackedWidget(self)
        self.pages = []

        for page in self.config["pages"]:
            layout = QGridLayout()
            layout.setSpacing(self.config.get("spacing", 20))
            cols = self.config.get("columns", 3)

            row, col = 0, 0
            container = QWidget()

            for app in page["apps"]:
                btn = QToolButton()
                btn.setText(app["name"])

                # ikon
                icon_value = app["icon"]
                icon_size = self.config.get("icon_size", 64)
                if os.path.isabs(icon_value) or os.path.exists(icon_value):
                    btn.setIcon(QIcon(icon_value))
                else:
                    btn.setIcon(QIcon.fromTheme(icon_value))
                btn.setIconSize(QSize(icon_size, icon_size))

                # ikon ortada, yazı altında
                btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
                btn.setFixedSize(self.config.get("button_size", 110), self.config.get("button_size", 110))

                # şeffaf buton desteği
                if self.config.get("transparent_button", False):
                    btn.setStyleSheet(f"""
                        font-size: {self.config.get('font_size', 16)}px;
                        background: transparent;
                        border: none;
                    """)
                else:
                    btn.setStyleSheet(f"font-size: {self.config.get('font_size', 16)}px;")

                btn.clicked.connect(lambda _, c=app["cmd"]: subprocess.Popen(c, shell=True))
                layout.addWidget(btn, row, col, Qt.AlignCenter)

                col += 1
                if col >= cols:
                    col = 0
                    row += 1

            container.setLayout(layout)
            self.stack.addWidget(container)
            self.pages.append(container)

        self.current_page = 0
        self.stack.setCurrentIndex(self.current_page)

        # Nokta göstergesi
        self.dots_layout = QHBoxLayout()
        self.dots_layout.setAlignment(Qt.AlignCenter)
        self.dot_buttons = []
        dot_size = self.config.get("dot_size", 10)

        for i in range(len(self.pages)):
            dot_btn = QToolButton()
            dot_btn.setText("●")
            dot_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
            dot_btn.setStyleSheet(f"font-size: {dot_size}px; color: gray; background: transparent; border: none;")
            dot_btn.clicked.connect(lambda _, idx=i: self.go_to_page(idx))
            self.dots_layout.addWidget(dot_btn)
            self.dot_buttons.append(dot_btn)

        self.update_dots()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stack)
        main_layout.addLayout(self.dots_layout)
        self.setLayout(main_layout)

        self.start_x = None

    # Sağ tık menüsü
    def contextMenuEvent(self, event):
        menu = QMenu("PiLauncher", self)

        # Launch terminal
        terminal_cmd = self.config.get("terminal", "x-terminal-emulator")
        launch_terminal = QAction("Launch terminal", self)
        launch_terminal.triggered.connect(lambda: subprocess.Popen(terminal_cmd, shell=True))
        menu.addAction(launch_terminal)

        # Open config file
        open_config = QAction("Open config file", self)
        open_config.triggered.connect(lambda: subprocess.Popen(f"xdg-open {self.config_file}", shell=True))
        menu.addAction(open_config)

        # About
        about_action = QAction("About", self)
        about_action.triggered.connect(lambda: QMessageBox.information(
            self, "About PiLauncher", f"PiLauncher v{VERSION}\n\nMinimal launcher for Raspberry Pi"
        ))
        menu.addAction(about_action)

        # Quit
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(lambda: QApplication.quit())
        menu.addAction(quit_action)

        menu.exec_(event.globalPos())

    def update_dots(self):
        dot_size = self.config.get("dot_size", 10)
        for i, dot in enumerate(self.dot_buttons):
            if i == self.current_page:
                dot.setStyleSheet(f"font-size: {dot_size}px; color: white; background: transparent; border: none;")
            else:
                dot.setStyleSheet(f"font-size: {dot_size}px; color: gray; background: transparent; border: none;")

    def mousePressEvent(self, event):
        self.start_x = event.x()

    def mouseReleaseEvent(self, event):
        if self.start_x is None:
            return
        delta = event.x() - self.start_x
        if delta > 100:
            self.prev_page()
        elif delta < -100:
            self.next_page()
        self.start_x = None

    def keyPressEvent(self, event):
        if Qt.Key_0 <= event.key() <= Qt.Key_9:
            page_num = event.key() - Qt.Key_0
            if 0 <= page_num < len(self.pages):
                self.go_to_page(page_num)

    def go_to_page(self, idx):
        self.stack.setCurrentIndex(idx)
        self.current_page = idx
        self.update_dots()

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.stack.setCurrentIndex(self.current_page)
            self.update_dots()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.stack.setCurrentIndex(self.current_page)
            self.update_dots()

app = QApplication(sys.argv)
window = Launcher()
window.show()
sys.exit(app.exec_())

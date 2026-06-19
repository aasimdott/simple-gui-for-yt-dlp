import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QFileDialog, QListWidget,
    QProgressBar, QLabel, QCheckBox, QListWidgetItem
)
from PyQt6.QtCore import QThread, pyqtSignal, QObject, Qt

class DownloadWorker(QObject):
    progress = pyqtSignal(float, str)  # Percentage, Status text
    finished = pyqtSignal(bool)        # Success status

    def __init__(self, url, resolution, save_dir, use_tor):
        super().__init__()
        self.url = url
        self.resolution = resolution
        self.save_dir = save_dir
        self.use_tor = use_tor
        self._is_killed = False
        self.process = None

    def run(self):
        res_map = {
            "4K (2160p)": "bestvideo[height<=2160]+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best",
            "720p": "bestvideo[height<=720]+bestaudio/best",
            "Best Quality": "bestvideo+bestaudio/best"
        }
        fmt = res_map.get(self.resolution, "best")

        cmd = [
            "yt-dlp",
            "-f", fmt,
            "--merge-output-format", "mp4",
            "-P", self.save_dir,
            "--newline",
            "--continue"
        ]

        if self.use_tor:
            cmd.extend(["--proxy", "socks5://127.0.0.1:9050"])

        cmd.append(self.url)

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=startupinfo
            )

            for line in self.process.stdout:
                if self._is_killed:
                    break

                line = line.strip()
                if "[download]" in line and "%" in line:
                    try:
                        parts = line.split()
                        pct_str = [p for p in parts if "%" in p][0].replace("%", "")
                        pct = float(pct_str)

                        speed = "Downloading..."
                        if "at" in parts:
                            speed_idx = parts.index("at") + 1
                            if speed_idx < len(parts):
                                speed = f"{parts[speed_idx]}"

                        self.progress.emit(pct, speed)
                    except Exception:
                        pass
                elif "[Merger]" in line:
                    self.progress.emit(99.0, "Merging 4K...")

            self.process.wait()

            if self._is_killed:
                self.finished.emit(False)
            else:
                self.progress.emit(100.0, "Finished")
                self.finished.emit(True)

        except Exception as e:
            self.progress.emit(0.0, f"Error")
            self.finished.emit(False)

    def terminate_download(self):
        self._is_killed = True
        if self.process:
            self.process.terminate()


# Individual GUI Widget for a single item row in the list
class QueueItemWidget(QWidget):
    def __init__(self, url, resolution, save_dir, use_tor):
        super().__init__()
        self.url = url
        self.resolution = resolution
        self.save_dir = save_dir
        self.use_tor = use_tor

        self.thread = None
        self.worker = None
        self.is_running = False

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Truncate URL display text for clean columns
        short_url = self.url[:30] + "..." if len(self.url) > 30 else self.url
        tor_tag = "🔒 " if self.use_tor else ""
        self.info_label = QLabel(f"{tor_tag}[{self.resolution}] {short_url}")
        self.info_label.setFixedWidth(220)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("Idle")
        self.status_label.setFixedWidth(100)

        self.action_btn = QPushButton("Start")
        self.action_btn.setFixedWidth(70)
        self.action_btn.clicked.connect(self.toggle_download)

        layout.addWidget(self.info_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.action_btn)

        self.setLayout(layout)

    def toggle_download(self):
        if not self.is_running:
            # Action: START / RESUME
            self.is_running = True
            self.action_btn.setText("Pause")
            self.status_label.setText("Connecting...")

            self.thread = QThread()
            self.worker = DownloadWorker(self.url, self.resolution, self.save_dir, self.use_tor)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.progress.connect(self.update_row_progress)
            self.worker.finished.connect(self.handle_row_finished)

            self.thread.start()
        else:
            # Action: PAUSE
            self.status_label.setText("Stopping...")
            self.cleanup_worker()
            self.status_label.setText("Paused")
            self.action_btn.setText("Resume")

    def update_row_progress(self, percent, speed_text):
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(speed_text)

    def handle_row_finished(self, success):
        self.cleanup_worker()
        if success:
            self.status_label.setText("Finished")
            self.action_btn.setText("Done")
            self.action_btn.setEnabled(False)
        else:
            if self.status_label.text() != "Paused":
                self.status_label.setText("Failed")
                self.action_btn.setText("Retry")

    def cleanup_worker(self):
        self.is_running = False
        if self.worker:
            self.worker.terminate_download()
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        self.worker = None
        self.thread = None


class YtdlpGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Download Module")
        self.setMinimumSize(750, 500)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Input Row
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste link here...")
        self.add_btn = QPushButton("Add to Download Queue")
        self.add_btn.clicked.connect(self.add_to_queue)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.add_btn)
        main_layout.addLayout(url_layout)

        # configurations box
        settings_layout = QHBoxLayout()
        self.res_combo = QComboBox()
        self.res_combo.addItems(["Best Quality", "4K (2160p)", "1080p", "720p"])

        self.folder_btn = QPushButton("Select Folder")
        self.folder_btn.clicked.connect(self.select_folder)
        self.folder_label = QLabel(os.path.expanduser("~"))

        self.tor_checkbox = QCheckBox("Tor Proxy")

        settings_layout.addWidget(QLabel("Resolution:"))
        settings_layout.addWidget(self.res_combo)
        settings_layout.addWidget(self.folder_btn)
        settings_layout.addWidget(self.folder_label, 1)
        settings_layout.addWidget(self.tor_checkbox)
        main_layout.addLayout(settings_layout)

        # Multi-Item List Frame
        main_layout.addWidget(QLabel("Active Downloads:"))
        self.queue_widget = QListWidget()
        main_layout.addWidget(self.queue_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def select_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.folder_label.text())
        if directory:
            self.folder_label.setText(directory)

    def add_to_queue(self):
        url = self.url_input.text().strip()
        if not url:
            return

        res = self.res_combo.currentText()
        folder = self.folder_label.text()
        use_tor = self.tor_checkbox.isChecked()

        # 1. Create custom row widget
        row_widget = QueueItemWidget(url, res, folder, use_tor)

        # 2. Inject it cleanly inside a QListWidget container item row
        list_item = QListWidgetItem(self.queue_widget)
        list_item.setSizeHint(row_widget.sizeHint())

        self.queue_widget.addItem(list_item)
        self.queue_widget.setItemWidget(list_item, row_widget)

        self.url_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = YtdlpGUI()
    gui.show()
    sys.exit(app.exec())

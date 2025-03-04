import sys
import socket
import cv2
import numpy as np
import struct
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

class CameraReceiver(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Camera Feed")
        self.setGeometry(100, 100, 640, 480)

        # QLabel to show the camera feed
        self.image_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # Setup the TCP/IP connection
        self.HOST = '100.94.211.35'  # Raspberry Pi IP address
        self.PORT = 8081  # Same port number as the sender

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.HOST, self.PORT))
        
        # Set up the QTimer to periodically fetch the new frame
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.receive_frame)
        self.timer.start(30)  # roughly 30 FPS

    def receive_frame(self):
        try:
            # Receive the size of the incoming frame
            frame_size_data = self.client_socket.recv(4)
            if not frame_size_data:
                return
            
            frame_size = struct.unpack("!I", frame_size_data)[0]

            # Receive the frame data
            frame_data = b""
            while len(frame_data) < frame_size:
                frame_data += self.client_socket.recv(4096)

            # Convert to a NumPy array and decode the image
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            # Convert frame to QImage for PyQt
            height, width, channels = frame.shape
            bytes_per_line = channels * width
            qimage = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            # Set the QPixmap on the label to display the image
            self.image_label.setPixmap(pixmap)

        except Exception as e:
            print(f"Error receiving frame: {e}")
    
    def closeEvent(self, event):
        self.client_socket.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CameraReceiver()
    window.show()
    sys.exit(app.exec_())
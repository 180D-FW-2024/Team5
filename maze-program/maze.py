from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtGui import QPainter, QPen, QImage, QPixmap
from PyQt5.QtCore import Qt, QPoint
from enum import Enum
import sys
import random
import socket
import threading
import time
import difflib
import speech_recognition as sr
import multiprocessing
# import struct
# import pickle

# Universal directions
class Dir(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

# Maze generation function
def generate_maze(n, m):
    """Generates an N x M maze using recursive backtracking."""
    maze = [[{'visited': False, 'walls': [True, True, True, True]} for _ in range(m)] for _ in range(n)]
    # directions = [((0, -1), 0), ((0, 1), 1), ((-1, 0), 2), ((1, 0), 3)]  # [Top, Bottom, Left, Right]
    directions = [((-1, 0), 0), ((0, 1), 1), ((1, 0), 2), ((0, -1), 3)]  # [Top, Right, Bottom, Left]

    def remove_wall(x, y, nx, ny, wall_idx):
        """Remove walls between (x, y) and (nx, ny)."""
        maze[x][y]['walls'][wall_idx] = False
        maze[nx][ny]['walls'][(wall_idx + 2) % 4] = False
        # print("(" + str(x) + ", " + str(y) + "): connected to (" + str(nx) + ", " + str(ny) + ") in direction " + str(wall_idx))

    def visit_cell(x, y):
        """Main recursive function for traversing the maze."""
        maze[x][y]['visited'] = True
        random.shuffle(directions)  # Shuffle directions for randomness
        for (dx, dy), wall_idx in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and not maze[nx][ny]['visited']:
                remove_wall(x, y, nx, ny, wall_idx)
                visit_cell(nx, ny)

    visit_cell(0, 0)  # Start at the top-left corner
    return maze

# Main window class
class MazeWindow(QMainWindow):
    def __init__(self, n, m):
        super().__init__()
        self.setWindowTitle("Maze Generator")
        self.setGeometry(100, 100, 800, 900)
        self.n, self.m = n, m  # Maze dimensions
        self.cell_size = min(700 // n, 700 // m)  # Fit the maze into the window

        # Initial maze
        self.maze = generate_maze(n, m)

        # Initial player position
        self.player_x, self.player_y = 0, 0
        self.player_dir = Dir.UP.value

        # Add a cooldown attribute
        self.last_keypress_time = 0  # Timestamp of the last key press
        self.keypress_cooldown = 0.3  # Cooldown period in seconds

        # Controller server details
        self.controller_host = '100.122.70.122'  # Maze Controller Tailscale IP
        self.controller_port = 9090
        self.controller_client = self.setup_controller_client()

        # Start listening for commands from `controller.py`
        if self.controller_client:
            self.controller_thread = threading.Thread(target=self.listen_to_controller, daemon=True)
            self.controller_thread.start()

        # Socket connection setup for Maze Navigator
        self.server_host = '100.94.211.35' # Maze Navigator Tailscale IP
        self.server_port = 8080
        # self.camera_port = 8081
        self.socket_client = self.setup_socket_client()

        # Add the regenerate button
        self.regenerate_button = QPushButton("Regenerate Maze", self)
        self.regenerate_button.setGeometry(50, 800, 200, 40)  # Position at bottom-left
        self.regenerate_button.clicked.connect(self.regenerate_maze)

        # Add IMU Data Label
        # self.imu_label = QLabel("IMU Data: N/A", self)
        # self.imu_label.setGeometry(775, 650, 640, 200)  # Centered below the camera feed
        # self.imu_label.setAlignment(Qt.AlignCenter)
        # self.imu_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        # Add Camera Feed Label
        # self.camera_feed_label = QLabel("Camera Feed", self)
        # self.camera_feed_label.setGeometry(775, 75, 640, 20)  # Positioned above the camera feed
        # self.camera_feed_label.setAlignment(Qt.AlignCenter)
        # self.camera_feed_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Add Camera Label
        # self.camera_label = QLabel(self)
        # self.camera_label.setGeometry(775, 100, 640, 480)
        # self.camera_label.setStyleSheet("border: 1px solid black;")

        # Add on-screen D-Pad buttons
        self.setup_dpad()

        # Start a background thread to listen for IMU data
        # self.imu_data_thread = threading.Thread(target=self.receive_imu_data, daemon=True)
        # self.imu_data_thread.start()

        # Start thread for camera
        # self.camera_thread = threading.Thread(target=self.receive_camera_data, daemon=True)
        # self.camera_thread.start()

        # Add voice command listener
        self.voice_thread = threading.Thread(target=self.listen, daemon=True)
        self.voice_thread.start()

        # Voice command toggle
        self.is_listening = False

        # Add a voice toggle button
        self.voice_toggle_button = QPushButton("Enable Voice Commands", self)
        self.voice_toggle_button.setGeometry(300, 800, 200, 40)  # Position at bottom-center
        self.voice_toggle_button.setCheckable(True)
        self.voice_toggle_button.clicked.connect(self.toggle_voice_commands)

    def setup_controller_client(self):
        """Set up a client socket to connect to 'controller.py'."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)  # Timeout after 5 seconds
            client_socket.connect((self.controller_host, self.controller_port))
            print(f"Connected to Controller at {self.controller_host}:{self.controller_port}")
            return client_socket
        except socket.timeout:
            print("Controller connection timed out.")
            return None
        except Exception as e:
            print(f"Failed to connect to Controller: {e}")
            return None
        
    def listen_to_controller(self):
        """Continuously listen for commands from 'controller.py'."""
        try:
            while True:
                data = self.controller_client.recv(1024).decode().strip()
                if not data:
                    break  # Connection closed
                if data == "heartbeat":
                    continue  # Ignore heartbeat messages
                print(f"Received command from Controller: {data}")

                # Map commands to actions
                if data == 'w':
                    self.movePlayer()
                elif data == 'a':
                    self.rotatePlayer(0)
                elif data == 'd':
                    self.rotatePlayer(1)
                else:
                    print(f"Unknown command: {data}")
        except Exception as e:
            print(f"Error receiving data from Controller: {e}")
        finally:
            self.controller_client.close()

    def setup_socket_client(self):
        """Set up the socket client for communication with the Maze Navigator"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)  # Timeout after 5 seconds
            client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to Maze Navigator at {self.server_host}:{self.server_port}")
            return client_socket
        except socket.timeout:
            print("Maze Navigator connection timed out.")
            return None
        except Exception as e:
            print(f"Failed to connect to Maze Navigator: {e}")
            return None

    def setup_dpad(self):
        """Set up D-Pad buttons for on-screen control"""
        dpad_center_x = 650
        dpad_center_y = 825
        dpad_button_width = 50
        dpad_button_height = 30
        dpad_button_margin = 10   # extra space between buttons

        self.left_button = QPushButton("↺", self)
        self.left_button.setGeometry(dpad_center_x - int(1.5 * dpad_button_width) - dpad_button_margin, dpad_center_y - int(0.5 * dpad_button_height), dpad_button_width, dpad_button_height)
        self.left_button.clicked.connect(lambda: self.rotatePlayer(0))

        self.up_button = QPushButton("↑", self)
        self.up_button.setGeometry(dpad_center_x - int(0.5 * dpad_button_width), dpad_center_y - int(1.5 * dpad_button_height) - dpad_button_margin, dpad_button_width, dpad_button_height)
        self.up_button.clicked.connect(lambda: self.movePlayer())

        self.right_button = QPushButton("↻", self)
        self.right_button.setGeometry(dpad_center_x + int(0.5 * dpad_button_width) + dpad_button_margin, dpad_center_y - int(0.5 * dpad_button_height), dpad_button_width, dpad_button_height)
        self.right_button.clicked.connect(lambda: self.rotatePlayer(1))

        """self.down_button = QPushButton("↓", self)
        self.down_button.setGeometry(dpad_center_x - int(0.5 * dpad_button_width), dpad_center_y + int(0.5 * dpad_button_height + dpad_button_margin), dpad_button_width, dpad_button_height)
        self.down_button.clicked.connect(lambda: self.movePlayer(2))"""

    # def receive_imu_data(self):
    #     """Continuously receive IMU data from the RPi"""
    #    if self.socket_client:
    #        buffer = ""
    #        while True:
    #            try:
    #                # Read data from the socket
    #                data = self.socket_client.recv(2048).decode()
    #                if not data:
    #                    break  # Connection closed

                    # Add data to buffer and process complete messages
    #                buffer += data
    #                while "\n" in buffer:
    #                    message, buffer = buffer.split("\n", 1)  # Split at the first newline
    #                    self.process_imu_message(message.strip())
    #            except Exception as e:
    #                print(f"Failed to receive data: {e}")
    #                break

    # def process_imu_message(self, message):
    #     """Process a single IMU message."""
    #    if message.startswith("imu_data"):
    #        try:
    #            _, acc_data, gyro_data, mag_data = message.split("|")
    #            acc_values = acc_data.replace("acc:", "")
    #            gyro_values = gyro_data.replace("gyro:", "")
    #            mag_values = mag_data.replace("mag:", "")
    #            self.imu_label.setText(f"IMU Data\nAcc: {acc_values}\nGyro: {gyro_values}\nMag: {mag_values}")
    #        except ValueError:
    #            print("Malformed IMU data received:", message)


#    def receive_camera_data(self):
#       try:
#            camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#            camera_socket.connect((self.server_host, self.camera_port))
#            data = b""

#            while True:
                # Receive frame length
#                while len(data) < struct.calcsize("L"):
#                    data += camera_socket.recv(4096)
#                packed_len = data[:struct.calcsize("L")]
#                data = data[struct.calcsize("L"):]
#                frame_len = struct.unpack("L", packed_len)[0]

                # Receive frame data
#                while len(data) < frame_len:
#                    data += camera_socket.recv(4096)
#                frame_data = data[:frame_len]
#                data = data[frame_len:]

                # Deserialize frame
#                frame = pickle.loads(frame_data)

                # Convert to QImage and display
#                height, width, channel = frame.shape
#                bytes_per_line = channel * width
#                qimg = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
#                pixmap = QPixmap.fromImage(qimg)

#                self.camera_label.setPixmap(pixmap)
#        except Exception as e:
#            print(f"Failed to receive camera data: {e}")
    
    def send_command_to_rpi(self, command):
        """Send command to the Maze Navigator."""
        if self.socket_client:
            try:
                self.socket_client.sendall(f"{command}\n".encode())
                print(f"Send command: {command}")
            except Exception as e:
                print(f"Failed to send command: {e}")

    def listen(self):
        r = sr.Recognizer()
        m = sr.Microphone()

        # Define allowed keywords
        allowed_keywords = ["forward", "left", "right"]

        with m as source:
            print("Calibrating microphone for background noise...")
            r.adjust_for_ambient_noise(source)
            print(f"Minimum energy threshold set to: {r.energy_threshold}")

            while True:
                try:
                    if not self.is_listening:
                        time.sleep(0.1)
                        continue

                    print("Listening for command...")
                    audio = r.listen(source)
                    command = r.recognize_whisper(audio, model="tiny.en").lower().strip()
                    print(f"Recognized voice command: {command}")

                    # Split the command into words and analyze each one
                    words = command.split()
                    for word in words:
                        # Match each word to allowed keywords
                        closest_match = difflib.get_close_matches(word, allowed_keywords, n=1, cutoff=0.6)
                        if closest_match:
                            matched_command = closest_match[0]
                            print(f"Matched command: {matched_command}")

                            if matched_command == "forward":
                                self.movePlayer()
                            elif matched_command == "left":
                                self.rotatePlayer(0)
                            elif matched_command == "right":
                                self.rotatePlayer(1)
                        else:
                            print(f"No valid command recognized")
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print(f"Speech recognition error: {e}")
                except Exception as e:
                    print(f"Unexpected error in listen thread: {e}")

    def toggle_voice_commands(self):
        """Enable or disable voice commands."""
        if self.voice_toggle_button.isChecked():
            self.is_listening = True
            self.voice_toggle_button.setText("Disable Voice Commands")
            print("Voice commands enabled")
        else:
            self.is_listening = False
            self.voice_toggle_button.setText("Enable Voice Commands")
            print("Voice commands disabled")

    def regenerate_maze(self):
        """Regenerate the maze and refresh the display."""
        self.maze = generate_maze(self.n, self.m)
        self.update()  # Refresh the GUI

    def movePlayer(self):
        """Update player position by moving forward"""

        px, py = self.player_x, self.player_y
        pcell = self.maze[py][px]

        direction = self.player_dir

        match direction:
            case Dir.UP.value:      # 0
                if not pcell['walls'][0]:
                    self.send_command_to_rpi("forward")
                    self.player_y -= 1
            case Dir.RIGHT.value:   # 1 
                if not pcell['walls'][1]:
                    self.send_command_to_rpi("forward")
                    self.player_x += 1
            case Dir.DOWN.value:    # 2
                if not pcell['walls'][2]:
                    self.send_command_to_rpi("forward")
                    self.player_y += 1
            case Dir.LEFT.value:    # 3
                if not pcell['walls'][3]:
                    self.send_command_to_rpi("forward")
                    self.player_x -= 1
            case _:
                print("Car is facing an invalid direction")

        self.update()

    def rotatePlayer(self, direction):
        """Update player status by rotating left or right"""
        """0 = Rotate Left, 1 = Rotate Right"""
        if direction == 0:      # Rotate left
            self.send_command_to_rpi("left")
            self.player_dir = (self.player_dir - 1) % 4
        elif direction == 1:    # Rotate right\
            self.send_command_to_rpi("right")
            self.player_dir = (self.player_dir + 1) % 4
        else:
            print("Invalid rotation direction")
        self.update()


    def keyPressEvent(self, event):
        """Handles keyboard inputs with cooldown."""
        current_time = time.time()  # Get the current timestamp

        # Check if enough time has passed since the last key press
        if current_time - self.last_keypress_time < self.keypress_cooldown:
            return  # Ignore the key press if it's within the cooldown period

        # Update the last key press time
        self.last_keypress_time = current_time

        # Handle the key press
        if event.key() == Qt.Key_W:
            self.movePlayer() # Up
        elif event.key() == Qt.Key_D:
            self.rotatePlayer(1) # Right
        elif event.key() == Qt.Key_S:
            pass  # Backward movement disabled
        elif event.key() == Qt.Key_A:
            self.rotatePlayer(0) # Left
        elif event.key() == Qt.Key_Q: # Quit
            self.send_command_to_rpi("stop")
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 2))

        for x in range(self.n):
            for y in range(self.m):
                cell = self.maze[x][y]
                cx, cy = 50 + y * self.cell_size, 50 + x * self.cell_size       # UI Padding to top and left
                # cx, cy = y * self.cell_size, x * self.cell_size
                if cell['walls'][0]:  # Top wall
                    painter.drawLine(cx, cy, cx + self.cell_size, cy)
                if cell['walls'][1]:  # Right wall
                    painter.drawLine(cx + self.cell_size, cy, cx + self.cell_size, cy + self.cell_size)
                if cell['walls'][2]:  # Bottom wall
                    painter.drawLine(cx, cy + self.cell_size, cx + self.cell_size, cy + self.cell_size)
                if cell['walls'][3]:  # Left wall
                    painter.drawLine(cx, cy, cx, cy + self.cell_size)

        painter.setBrush(Qt.red)
        player_pos = QPoint(50 + int(self.cell_size * (self.player_x + 0.5)), 50 + int(self.cell_size * (self.player_y + 0.5)))

        """Delete below when we have a better shape"""
        test_x_offset, test_y_offset = 0, 0

        if self.player_dir == Dir.UP.value:
            test_y_offset = -30
        elif self.player_dir == Dir.RIGHT.value:
            test_x_offset = 30
        elif self.player_dir == Dir.DOWN.value:
            test_y_offset = 30
        elif self.player_dir == Dir.LEFT.value:
            test_x_offset = -30

        player_face = QPoint(player_pos.x() + test_x_offset, player_pos.y() + test_y_offset)
        painter.drawEllipse(player_face, 10, 10)
        """Delete above whne we have a better shape"""

        painter.drawEllipse(player_pos, 25, 25)
        

        # painter.setBrush(Qt.NoBrush)

# Running the application
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Fix for PyInstaller multi-threading issue

    app = QApplication(sys.argv)
    n, m = 7, 7  # Dimensions of the maze (N x M)
    window = MazeWindow(n, m)
    window.show()
    sys.exit(app.exec_())
    
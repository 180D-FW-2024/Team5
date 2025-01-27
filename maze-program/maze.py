from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtGui import QPainter, QPen, QImage, QPixmap
from PyQt5.QtCore import Qt, QPoint
from enum import Enum
import sys
import random
import socket
import threading
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

        # initialize socket connection
        self.socket_client = None

        # Start Button server
        self.server_host = '0.0.0.0'  # Listen on all interfaces
        self.button_server_thread = threading.Thread(target=self.start_button_server, daemon=True)
        self.button_server_thread.start()

    def start_button_server(self):
        """Start a server to handle persistent connections from RPi Controller."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind((self.server_host, 9090))  # Port for RPi Controller
                server_socket.listen(5)
                print(f"Button server listening on {self.server_host}:9090")

                while True:
                    conn, addr = server_socket.accept()
                    print(f"Connected to Button RPi: {addr}")
                    threading.Thread(target=self.handle_button_commands, args=(conn,), daemon=True).start()
        except Exception as e:
            print(f"Button server error: {e}")

    def handle_button_commands(self, conn):
        """Handle incoming commands from RPi Controller."""
        try:
            while True:
                data = conn.recv(1024).decode().strip()  # Receive data
                if not data:
                    break  # Connection closed
                print(f"Received button command: {data}")

                # Map commands to actions
                if data == 'w':
                    self.movePlayer()
                elif data == 'a':
                    self.rotatePlayer(0)
                elif data == 'd':
                    self.rotatePlayer(1)
                else:
                    print(f"Unknown button command: {data}")
        except Exception as e:
            print(f"Error handling button commands: {e}")
        finally:
            conn.close()
            print("Connection with Button RPi closed.")

        # Socket connection setup
        self.server_host = '172.20.10.6' # Maze Navigator Tailscale IP
        self.server_port = 8080
        # self.camera_port = 8081
        self.socket_client = self.setup_socket_client()

        # Add the regenerate button
        self.regenerate_button = QPushButton("Regenerate Maze", self)
        self.regenerate_button.setGeometry(50, 800, 200, 40)  # Position at bottom-left
        self.regenerate_button.clicked.connect(self.regenerate_maze)

        # Add IMU Data Label
        self.imu_label = QLabel("IMU Data: N/A", self)
        self.imu_label.setGeometry(775, 650, 640, 200)  # Centered below the camera feed
        self.imu_label.setAlignment(Qt.AlignCenter)
        self.imu_label.setStyleSheet("font-size: 14px; font-weight: bold;")

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
        self.imu_data_thread = threading.Thread(target=self.receive_imu_data, daemon=True)
        self.imu_data_thread.start()

        # Start thread for camera
        # self.camera_thread = threading.Thread(target=self.receive_camera_data, daemon=True)
        # self.camera_thread.start()

    def setup_socket_client(self):
        """Set up the socket client for communication with the RPi"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to server at {self.server_host}:{self.server_port}")
            return client_socket
        except Exception as e:
            print(f"Failed to connect to server: {e}")
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

    def receive_imu_data(self):
        """Continuously receive IMU data from the RPi"""
        if self.socket_client:
            buffer = ""
            while True:
                try:
                    # Read data from the socket
                    data = self.socket_client.recv(2048).decode()
                    if not data:
                        break  # Connection closed

                    # Add data to buffer and process complete messages
                    buffer += data
                    while "\n" in buffer:
                        message, buffer = buffer.split("\n", 1)  # Split at the first newline
                        self.process_imu_message(message.strip())
                except Exception as e:
                    print(f"Failed to receive data: {e}")
                    break

    def process_imu_message(self, message):
        """Process a single IMU message."""
        if message.startswith("imu_data"):
            try:
                _, acc_data, gyro_data, mag_data = message.split("|")
                acc_values = acc_data.replace("acc:", "")
                gyro_values = gyro_data.replace("gyro:", "")
                mag_values = mag_data.replace("mag:", "")
                self.imu_label.setText(f"IMU Data\nAcc: {acc_values}\nGyro: {gyro_values}\nMag: {mag_values}")
            except ValueError:
                print("Malformed IMU data received:", message)


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
        """Send command to RPi"""
        if self.socket_client:
            try:
                self.socket_client.sendall(command.encode())
                print(f"Send command: {command}")
            except Exception as e:
                print(f"Failed to send command: {e}")

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
        """Handles keyboard inputs"""
        if event.key() == Qt.Key_W:
            self.movePlayer() # Up
        elif event.key() == Qt.Key_D:
            self.rotatePlayer(1) # Right
        elif event.key() == Qt.Key_S:
            pass    # We are removing backwards movement
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
    app = QApplication(sys.argv)
    n, m = 7, 7  # Dimensions of the maze (N x M)
    window = MazeWindow(n, m)
    window.show()
    sys.exit(app.exec_())
    
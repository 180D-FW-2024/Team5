from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QPoint
import sys
import random
import socket

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

        # Socket connection setup
        self.server_host = '127.0.0.1' # Replace with RPi's IP address
        self.server_port = 8080
        self.socket_client = self.setup_socket_client()

        # Add the regenerate button
        self.regenerate_button = QPushButton("Regenerate Maze", self)
        self.regenerate_button.setGeometry(50, 800, 200, 40)  # Position at bottom-left
        self.regenerate_button.clicked.connect(self.regenerate_maze)

        # Add on-screen D-Pad buttons
        self.setup_dpad()

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

        self.left_button = QPushButton("←", self)
        self.left_button.setGeometry(dpad_center_x - int(1.5 * dpad_button_width) - dpad_button_margin, dpad_center_y - int(0.5 * dpad_button_height), dpad_button_width, dpad_button_height)
        self.left_button.clicked.connect(lambda: self.movePlayer(3))

        self.up_button = QPushButton("↑", self)
        self.up_button.setGeometry(dpad_center_x - int(0.5 * dpad_button_width), dpad_center_y - int(1.5 * dpad_button_height) - dpad_button_margin, dpad_button_width, dpad_button_height)
        self.up_button.clicked.connect(lambda: self.movePlayer(0))

        self.right_button = QPushButton("→", self)
        self.right_button.setGeometry(dpad_center_x + int(0.5 * dpad_button_width) + dpad_button_margin, dpad_center_y - int(0.5 * dpad_button_height), dpad_button_width, dpad_button_height)
        self.right_button.clicked.connect(lambda: self.movePlayer(1))

        self.down_button = QPushButton("↓", self)
        self.down_button.setGeometry(dpad_center_x - int(0.5 * dpad_button_width), dpad_center_y + int(0.5 * dpad_button_height + dpad_button_margin), dpad_button_width, dpad_button_height)
        self.down_button.clicked.connect(lambda: self.movePlayer(2))

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

    def movePlayer(self, direction):
        """Update player position and sent movement commands"""
        commands = ["up", "right", "down", "left"]
        if 0 <= direction < len(commands):
            self.send_command_to_rpi(commands[direction])
        
        px, py = self.player_x, self.player_y
        pcell = self.maze[py][px]

        match direction:
            case 0: # Up (Forward)
                if not pcell['walls'][0]:
                    self.player_y -= 1
            case 1: # Right
                if not pcell['walls'][1]:
                    self.player_x += 1
            case 2: # Down (Backward)
                if not pcell['walls'][2]:
                    self.player_y += 1
            case 3: # Left
                if not pcell['walls'][3]:
                    self.player_x -= 1
            case _:
                print("Invalid direction")
        
        self.update()
        # print("(" + str(self.player_x) + ", " + str(self.player_y) + ")")   

    def keyPressEvent(self, event):
        """Handles keyboard inputs"""
        if event.key() == Qt.Key_W:
            self.movePlayer(0) # Up
        elif event.key() == Qt.Key_D:
            self.movePlayer(1) # Right
        elif event.key() == Qt.Key_S:
            self.movePlayer(2) # Down
        elif event.key() == Qt.Key_A:
            self.movePlayer(3) # Left
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
        painter.drawEllipse(player_pos, 25, 25)

        # painter.setBrush(Qt.NoBrush)

# Running the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    n, m = 7, 7  # Dimensions of the maze (N x M)
    window = MazeWindow(n, m)
    window.show()
    sys.exit(app.exec_())
    
import RPi.GPIO as GPIO
import socket
import threading
import time

# Button GPIO pins
BUTTONS = {
    27: 'w',  # Forward
    22: 'a',  # Left
    17: 'd',  # Right
}

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in BUTTONS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Pull-up resistor

# Server setup
HOST = ''  # Listen on all interfaces
PORT = 9090  # Port to communicate with maze.py

running = True

def listen_for_buttons(conn):
    """Listen for GPIO button presses and send commands to maze.py."""
    try:
        print("Listening for button presses...")
        while running:
            for pin, command in BUTTONS.items():
                if GPIO.input(pin) == GPIO.LOW:  # Button pressed
                    print(f"Button {pin} pressed, sending '{command}'")
                    conn.sendall(command.encode())  # Send the command
                    time.sleep(0.3)  # Debounce delay
    except Exception as e:
        print(f"Error sending GPIO commands: {e}")
    finally:
        GPIO.cleanup()

def start_controller_server():
    """Start the controller server to handle connections from maze.py."""
    global running
    try:
        # Set up the server socket
        print("Waiting for connection from maze.py...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)
            conn, addr = server_socket.accept()
            print(f"Connected to maze.py: {addr}")

            # Start listening for button presses
            listen_for_buttons(conn)
    except KeyboardInterrupt:
        print("Exiting server...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        running = False
        server_socket.close()
        GPIO.cleanup()
        print("Controller server closed.")
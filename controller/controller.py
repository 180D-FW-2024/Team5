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
    global running
    try:
        print("Listening for button presses...")
        while running:
            for pin, command in BUTTONS.items():
                if GPIO.input(pin) == GPIO.LOW:  # Button pressed
                    print(f"Button {pin} pressed, sending '{command}'")
                    conn.sendall(command.encode())  # Send the command
                    time.sleep(0.3)  # Debounce delay
    except (ConnectionResetError, BrokenPipeError):
        print("Connection to maze.py lost.")
        running = False
    except Exception as e:
        print(f"Error in button listener: {e}")
        running = False
    finally:
        print("Stopping button listener...")

def send_heartbeat(conn):
    """Send periodic heartbeat messages to maze.py."""
    global running
    try:
        while running:
            conn.sendall("heartbeat\n".encode())  # Send a heartbeat message
            time.sleep(2)  # Wait 2 seconds before sending the next heartbeat
    except (ConnectionResetError, BrokenPipeError):
        print("Connection to maze.py lost during heartbeat.")
        running = False
    except Exception as e:
        print(f"Error sending heartbeat: {e}")
        running = False
    finally:
        print("Heartbeat thread stopped.")

def monitor_connection(conn):
    """Monitor the connection to maze.py and stop if it's lost."""
    global running
    try:
        while running:
            try:
                conn.settimeout(2.0)  # Set a timeout for receiving data
                data = conn.recv(1024)  # Attempt to receive data
                if not data:
                    print("Maze.py has closed the connection.")
                    running = False  # Stop the main loop
                    break
            except socket.timeout:
                # No data received within the timeout, assume connection is still alive
                continue
            except (ConnectionResetError, BrokenPipeError):
                print("Maze.py connection lost.")
                running = False
                break
    except Exception as e:
        print(f"Error monitoring connection: {e}")
    finally:
        print("Connection monitoring stopped.")
        running = False

# Controller server setup
print("Waiting for connection...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)

try:
    conn, addr = sock.accept()
    print(f"Connected by {addr}")

    # Start a thread to send heartbeats
    heartbeat_thread = threading.Thread(target=send_heartbeat, args=(conn,), daemon=True)
    heartbeat_thread.start()

    # Start a thread to monitor the connection
    monitor_thread = threading.Thread(target=monitor_connection, args=(conn,), daemon=True)
    monitor_thread.start()

    # Start listening for button presses
    listen_for_buttons(conn)

    # Wait for the monitor thread to finish
    monitor_thread.join()
    heartbeat_thread.join()  # Wait for the heartbeat thread to finish

except KeyboardInterrupt:
    print("Exiting server...")
except Exception as e:
    print(f"Server error: {e}")
finally:
    running = False  # Stop the main loop
    if conn:
        conn.close()  # Close the connection
    sock.close()  # Close the server socket
    GPIO.cleanup()  # Clean up GPIO resources
    print("Controller server closed.")
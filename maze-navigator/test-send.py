import socket
import cv2
import numpy as np
import time
from picamera2 import Picamera2
import io
import struct

# Initialize Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())

# Start camera preview (optional, to check if it's working)
picam2.start()

# Set up the server (SENDER)
HOST = '0.0.0.0'  # Accept connections from any IP address
PORT = 8081        # Arbitrary port
BUFFER_SIZE = 4096 # Size of the buffer to send

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print(f"Waiting for a connection on {HOST}:{PORT}...")

# Wait for the receiver to connect
client_socket, client_address = server_socket.accept()
print(f"Connected by {client_address}")

# Stream video frames to the receiver
try:
    while True:
        # Capture a frame from the camera
        frame = picam2.capture_array()
        
        # Convert to JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()
        
        # Send the size of the frame first
        frame_size = len(frame_bytes)
        client_socket.sendall(struct.pack("!I", frame_size))  # Send the size of the image
        
        # Send the actual image data
        client_socket.sendall(frame_bytes)

        # Wait a little before sending the next frame
        time.sleep(0.03)  # Roughly 30 FPS
        
except KeyboardInterrupt:
    print("Connection closed by user.")
finally:
    # Clean up
    client_socket.close()
    server_socket.close()
    picam2.close()
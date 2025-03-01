import socket
import RPi.GPIO as GPIO
import time
import threading
import IMU
import cv2
import struct
from picamera2 import Picamera2
import numpy as np

# Motor pins
in1 = 17
in2 = 22
enA = 27

in3 = 23
in4 = 24
enB = 25

# ROI constants, the top of the frame is 0 and the bottom is 1
roi_start = 0 
roi_end = 1/3
threshold = 0.3 # Threshold for black line detection

# GPIO Setup
def init_GPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(enA, GPIO.OUT)
    GPIO.setup(in3, GPIO.OUT)
    GPIO.setup(in4, GPIO.OUT)
    GPIO.setup(enB, GPIO.OUT)
    
    # Create PWM objects for both motors
    global pwm_a, pwm_b
    pwm_a = GPIO.PWM(enA, 1000)  # 1000 Hz frequency
    pwm_b = GPIO.PWM(enB, 1000)
    
    # Start PWM with 50% duty cycle
    pwm_a.start(75)
    pwm_b.start(75)

def backward():
    GPIO.output(in1, True)
    GPIO.output(in2, False)
    GPIO.output(in3, False)
    GPIO.output(in4, True)

def forward():
    """Move forward while checking for line"""
    set_speed(75)
    GPIO.output(in1, False)
    GPIO.output(in2, True)
    GPIO.output(in3, True)
    GPIO.output(in4, False)
    
    try:
        # Capture frame
        frame = picam2.capture_array()
        
        # Check for line
        if detect_line(frame):
            print("Line detected - stopping")
            stop()
            return True
    except Exception as e:
        print(f"Error in line detection: {e}")
    
    return False

def left_turn():
    set_speed(75)
    GPIO.output(in1, True)
    GPIO.output(in2, False)
    GPIO.output(in3, True)
    GPIO.output(in4, False)

def right_turn():
    set_speed(75)
    GPIO.output(in1, False)
    GPIO.output(in2, True)
    GPIO.output(in3, False)
    GPIO.output(in4, True)

def stop():
    GPIO.output(in1, False)
    GPIO.output(in2, False)
    GPIO.output(in3, False)
    GPIO.output(in4, False)

def process_imu_data():
    acc_x = IMU.readACCx()
    acc_y = IMU.readACCy()
    acc_z = IMU.readACCz()
    gyr_x = IMU.readGYRx()
    gyr_y = IMU.readGYRy()
    gyr_z = IMU.readGYRz()
    mag_x = IMU.readMAGx()
    mag_y = IMU.readMAGy()
    mag_z = IMU.readMAGz()

    imu_data = {
        "acc": {"x": acc_x, "y": acc_y, "z": acc_z},
        "gyro": {"x": gyr_x, "y": gyr_y, "z": gyr_z},
        "mag": {"x": mag_x, "y": mag_y, "z": mag_z}
    }
    return imu_data

def set_speed(speed):
    """
    Set speed for both motors
    speed: 0-100 (percent of max speed)
    """
    pwm_a.ChangeDutyCycle(speed)
    pwm_b.ChangeDutyCycle(speed)

def setup_camera():
    """Initialize and configure the PiCamera"""
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(
        main={"format": 'RGB888',
              "size": (640, 480)}
    )
    picam2.configure(preview_config)
    picam2.start()
    return picam2

def detect_line(frame):
    """
    Detect black line in the frame
    Returns True if a black line is detected
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    
    # Define region of interest (ROI)
    height = gray.shape[0]
    roi = gray[int(height * roi_start):int(height * roi_end), :]
    
    # Apply threshold to detect black line
    _, thresh = cv2.threshold(roi, 50, 255, cv2.THRESH_BINARY_INV)
    
    # Calculate percentage of black pixels in ROI
    black_pixel_percentage = np.sum(thresh == 255) / thresh.size
    
    return black_pixel_percentage > threshold

# Server Setup
HOST = ''  # Listen on all available interfaces
PORT = 8080  # Port for commands
CAMERA_PORT = 7070  # Port for camera stream
running = True

# Camera stream
def start_camera_stream():
    """Stream camera frames to GUI with ROI."""
    global running
    camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    camera_socket.bind((HOST, CAMERA_PORT))
    camera_socket.listen(1)
    print("Waiting for camera connection...")
    conn, addr = camera_socket.accept()
    print(f"Camera connected by {addr}")

    try:
        while running:
            # Capture and process frame
            frame = picam2.capture_array()
            
            # Line detection logic and visualization
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            height = gray.shape[0]
            roi = gray[int(height * roi_start):int(height * roi_end), :]
            _, thresh = cv2.threshold(roi, 50, 255, cv2.THRESH_BINARY_INV)
            black_pixel_percentage = np.sum(thresh == 255) / thresh.size
            
            # Draw ROI and text
            cv2.rectangle(frame, (0, int(height * roi_start)), (frame.shape[1], int(height * roi_end)), (0, 255, 0), 2)
            cv2.putText(frame, f"Black: {black_pixel_percentage:.3f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # JPEG compression
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_data = jpeg.tobytes()
            
            # Send frame size followed by frame data
            try:
                size = len(frame_data)
                conn.sendall(struct.pack('<L', size) + frame_data)
            except ConnectionError:
                break
            
            time.sleep(0.03)  # ~30 fps
            
    except Exception as e:
        print(f"Camera stream error: {e}")
    finally:
        conn.close()
        camera_socket.close()

try:
    # GPIO Initialization
    init_GPIO()

    # Camera Initialization
    print("Setting up camera...")
    picam2 = setup_camera()
    print("Camera initialized.")

    # IMU Initialization
    print("Detecting IMU...")
    IMU.detectIMU()
    IMU.initIMU()
    print("IMU Initialized.")

    # Start camera stream thread
    camera_thread = threading.Thread(target=start_camera_stream, daemon=True)
    camera_thread.start()

    # Command server setup
    print("Waiting for connection...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    conn, addr = sock.accept()
    print(f"Connected by {addr}")

    # Command handling loop
    try:
        while True:
            try:
                data = conn.recv(1024).decode().strip()
                if not data:
                    print("Client disconnected.")
                    break

                print(f"Received command: {data}")
                
                # Parameters
                time_interval = 0.005  # Time interval between readings in seconds
                turning_radius = 400
                current_dir = 0  # Current direction (angle)

                if data == 'forward':
                    forward()
                    time.sleep(1)
                    stop()
                elif data == 'left':
                    left_turn()
                    final_dir = turning_radius

                    # Track the angular rotation using integration & stop when you finished your turn
                    while current_dir < final_dir:
                        angular_velocity = process_imu_data()["gyro"]["z"]

                        # Integrate angular velocity to calculate angle
                        current_dir += angular_velocity * time_interval
                        time.sleep(time_interval)  # Wait for the next reading

                    stop()

                elif data == 'right':
                    right_turn()
                    final_dir = -turning_radius

                    # Track the angular rotation using integration
                    while current_dir > final_dir:
                        angular_velocity = process_imu_data()["gyro"]["z"]

                        # Integrate angular velocity to calculate angle
                        current_dir += angular_velocity * time_interval
                        time.sleep(time_interval)  # Wait for the next reading

                    stop()

                elif data == 'stop':
                    stop()
                else:
                    print(f"Unknown command: {data}")
            except ConnectionResetError:
                print("Connection reset by peer. Closing connection.")
                break
    except Exception as e:
        print(f"Unexpected error: {e}")


finally:
    running = False  # Stop the camera thread
    if camera_thread.is_alive():
        camera_thread.join()
    stop()
    pwm_a.stop()
    pwm_b.stop()
    GPIO.cleanup()
    sock.close()
    print("Server closed.")

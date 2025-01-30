import socket
import RPi.GPIO as GPIO
import time
import threading
import IMU
import cv2
#import struct
#import pickle
#from picamera2 import Picamera2

# Motor pins
in1 = 17
in2 = 22
in3 = 23
in4 = 24

# GPIO Setup
def init_GPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(in3, GPIO.OUT)
    GPIO.setup(in4, GPIO.OUT)

def backward():
    GPIO.output(in1, False)
    GPIO.output(in2, True)
    GPIO.output(in3, True)
    GPIO.output(in4, False)

def forward():
    GPIO.output(in1, True)
    GPIO.output(in2, False)
    GPIO.output(in3, False)
    GPIO.output(in4, True)

def left_turn():
    GPIO.output(in1, True)
    GPIO.output(in2, False)
    GPIO.output(in3, True)
    GPIO.output(in4, False)

def right_turn():
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
        "gyro": {"x": gyr_x, "y": gyr_y, "z": acc_z},
        "mag": {"x": mag_x, "y": mag_y, "z": mag_z}
    }
    return imu_data

# Server Setup
HOST = ''  # Listen on all available interfaces
PORT = 8080  # Port for commands
# CAMERA_PORT = 8081  # Port for camera stream

running = True

# def imu_data_sender(conn):
#    """Send IMU data continuously to the client."""
#    global running
#    while running:
#        imu_data = process_imu_data()
#        imu_message = f"imu_data|acc:{imu_data['acc']}|gyro:{imu_data['gyro']}|mag:{imu_data['mag']}\n"
#        try:
#            conn.sendall(imu_message.encode())
#        except Exception as e:
#            print(f"Error sending IMU data: {e}")
#            break
#        time.sleep(0.1)  # Send data every 100ms

# def start_camera_stream():
#    """Stream camera frames to the client."""
#    global running
#    picam2 = Picamera2()
#    picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
#    picam2.start()

#    camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    camera_socket.bind((HOST, CAMERA_PORT))
#    camera_socket.listen(1)
#    print("Waiting for camera connection...")
#    conn, addr = camera_socket.accept()
#    print(f"Camera connected by {addr}")

#    try:
#        while running:
#            frame = picam2.capture_array()
#            # Convert frame to RGB
#            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Serialize and send the frame
#           data = pickle.dumps(frame)
#            conn.sendall(struct.pack("L", len(data)) + data)
#    except Exception as e:
#        print(f"Camera stream error: {e}")
#    finally:
#        picam2.stop()
#        conn.close()
#        camera_socket.close()

try:
    # GPIO Initialization
    init_GPIO()

    # IMU Initialization
    print("Detecting IMU...")
    IMU.detectIMU()  # Detect BerryIMU version
    IMU.initIMU()    # Initialize IMU sensors
    print("IMU Initialized.")

    # Start camera stream thread
    # camera_thread = threading.Thread(target=start_camera_stream, daemon=True)
    # camera_thread.start()

    # Command server setup
    print("Waiting for connection...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    conn, addr = sock.accept()
    print(f"Connected by {addr}")

    # Start IMU data thread
    # imu_thread = threading.Thread(target=imu_data_sender, args=(conn,), daemon=True)
    # imu_thread.start()

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
                    time.sleep(0.55)
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
    running = False  # Stop the IMU thread
    # if imu_thread.is_alive():
        # imu_thread.join()
#     if camera_thread.is_alive():
#        camera_thread.join()
    stop()
    GPIO.cleanup()
    sock.close()
    print("Server closed.")
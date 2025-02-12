import cv2
import numpy as np

def detectLines(image):
    # BGR to Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Gaussian Blur
    #blur = cv2.GaussianBlur(gray, (5, 5), 0)

    _, binary = cv2.threshold(gray, 63, 255, cv2.THRESH_BINARY)

    # Apply Gaussian Adaptive Thresholding
    #gaussian = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 0)

    # Canny Edge Detector
    edges = cv2.Canny(binary, 50, 150)

    # Detect line segments
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=50)

    #checkImage = binary

    #return lines, checkImage
    #return binary
    return lines

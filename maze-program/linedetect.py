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

    #checkImage = gray

    #return lines, checkImage
    #return binary
    return lines

def is_point_inside_square(px, py, square):
    """Check if a point (px, py) is inside the square.
    The square is given as a list of four corner coordinates [(x1, y1), (x2, y2), (x3, y3), (x4, y4)].
    """
    x_min = min(p[0] for p in square)
    x_max = max(p[0] for p in square)
    y_min = min(p[1] for p in square)
    y_max = max(p[1] for p in square)

    return x_min < px < x_max and y_min < py < y_max  # Strict inequality to avoid touching edges

def line_intersects(p1, p2, q1, q2):
    """Check if line segment (p1, p2) intersects with (q1, q2) using cross products."""
    def ccw(a, b, c):
        """Check if three points are counter-clockwise."""
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)

def line_intersects_square(x1, y1, x2, y2, square):
    """Check if a line segment (x1, y1) -> (x2, y2) intersects the square."""
    if is_point_inside_square(x1, y1, square) or is_point_inside_square(x2, y2, square):
        return True  # One of the endpoints is inside the square

    # Extract square edges
    edges = [
        (square[0], square[1]),
        (square[1], square[2]),
        (square[2], square[3]),
        (square[3], square[0])
    ]

    # Check if the line intersects any of the square's edges
    for edge in edges:
        if line_intersects((x1, y1), (x2, y2), edge[0], edge[1]):
            return True

    return False
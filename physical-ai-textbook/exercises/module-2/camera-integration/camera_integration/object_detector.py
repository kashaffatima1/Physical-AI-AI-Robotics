import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
import cv2
import numpy as np


class ObjectDetector(Node):
    """
    A ROS 2 node that performs object detection on camera images.
    This simulates basic object detection for Physical AI systems.
    """

    def __init__(self):
        super().__init__('object_detector')

        # Create subscriber for camera images
        self.subscription = self.create_subscription(
            Image,
            'camera/image_raw',
            self.image_callback,
            10
        )
        self.subscription  # prevent unused variable warning

        # Create publisher for detections
        self.detection_publisher = self.create_publisher(
            Detection2DArray,
            'camera/detections',
            10
        )

        # Initialize OpenCV bridge
        self.bridge = CvBridge()

        # Counter for processing frames
        self.frame_count = 0

        self.get_logger().info('Object Detector initialized')

    def image_callback(self, msg):
        """Process incoming camera image and detect objects"""
        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # Perform object detection
            detections = self.detect_objects(cv_image)

            # Create Detection2DArray message
            detection_array = Detection2DArray()
            detection_array.header = msg.header  # Use same header as image
            detection_array.detections = detections

            # Publish detections
            self.detection_publisher.publish(detection_array)

            self.get_logger().info(
                f'Detected {len(detections)} objects in frame {self.frame_count}'
            )

            # Increment frame counter
            self.frame_count += 1

        except Exception as e:
            self.get_logger().error(f'Error in object detection: {str(e)}')

    def detect_objects(self, image):
        """Detect objects in the image using color-based segmentation"""
        detections = []

        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define color ranges for different objects
        color_ranges = [
            # Blue objects (BGR: [255, 0, 0])
            ([100, 50, 50], [130, 255, 255], 'blue_object'),
            # Green objects (BGR: [0, 255, 0])
            ([40, 50, 50], [80, 255, 255], 'green_object'),
            # Red objects (BGR: [0, 0, 255])
            ([0, 50, 50], [10, 255, 255], 'red_object'),
            ([170, 50, 50], [180, 255, 255], 'red_object'),
        ]

        for lower, upper, label in color_ranges:
            # Create mask for the color range
            lower = np.array(lower, dtype="uint8")
            upper = np.array(upper, dtype="uint8")
            mask = cv2.inRange(hsv, lower, upper)

            # Find contours in the mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Process each contour
            for contour in contours:
                # Filter by size to avoid tiny detections
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)

                    # Create detection message
                    detection = Detection2D()
                    detection.header = self.get_clock().now().to_msg()

                    # Set bounding box
                    detection.bbox.size_x = float(w)
                    detection.bbox.size_y = float(h)

                    # Set center position
                    detection.bbox.center.x = float(x + w // 2)
                    detection.bbox.center.y = float(y + h // 2)

                    # Set confidence score based on area
                    confidence = min(0.95, area / 10000.0)  # Normalize confidence

                    # Create object hypothesis
                    hypothesis = ObjectHypothesisWithPose()
                    hypothesis.hypothesis.class_id = label
                    hypothesis.hypothesis.score = confidence

                    detection.results.append(hypothesis)

                    detections.append(detection)

        # Also detect circular objects using HoughCircles
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2)

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=100
        )

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                # Create detection for the circle
                detection = Detection2D()
                detection.header = self.get_clock().now().to_msg()

                # Set bounding box (square around the circle)
                detection.bbox.size_x = float(2 * r)
                detection.bbox.size_y = float(2 * r)

                # Set center position
                detection.bbox.center.x = float(x)
                detection.bbox.center.y = float(y)

                # Create object hypothesis for circular object
                hypothesis = ObjectHypothesisWithPose()
                hypothesis.hypothesis.class_id = 'circular_object'
                hypothesis.hypothesis.score = 0.8  # High confidence for circular detection

                detection.results.append(hypothesis)
                detections.append(detection)

        return detections


def main(args=None):
    rclpy.init(args=args)

    object_detector = ObjectDetector()

    try:
        rclpy.spin(object_detector)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        object_detector.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
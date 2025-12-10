import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class CameraSubscriber(Node):
    """
    A ROS 2 node that subscribes to camera images for Physical AI systems.
    This processes incoming camera data and performs basic operations.
    """

    def __init__(self):
        super().__init__('camera_subscriber')

        # Create subscriber for camera images
        self.subscription = self.create_subscription(
            Image,
            'camera/image_raw',
            self.image_callback,
            10
        )
        self.subscription  # prevent unused variable warning

        # Initialize OpenCV bridge
        self.bridge = CvBridge()

        # Counter for processing frames
        self.frame_count = 0

        self.get_logger().info('Camera Subscriber initialized')

    def image_callback(self, msg):
        """Process incoming camera image messages"""
        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # Process the image
            processed_image = self.process_image(cv_image)

            # Log some information about the frame
            self.get_logger().info(
                f'Received image: {cv_image.shape[1]}x{cv_image.shape[0]} '
                f'Frame #{self.frame_count}'
            )

            # Increment frame counter
            self.frame_count += 1

            # For simulation purposes, we could save processed images occasionally
            if self.frame_count % 100 == 0:  # Save every 100 frames
                filename = f'processed_frame_{self.frame_count:04d}.jpg'
                cv2.imwrite(filename, processed_image)
                self.get_logger().info(f'Saved processed frame to {filename}')

        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

    def process_image(self, image):
        """Apply basic image processing operations"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        # Apply edge detection
        gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray_blur, 50, 150)

        # Combine original with edges overlay
        edge_overlay = image.copy()
        edge_overlay[:, :, 0] = np.where(edges > 0, 255, edge_overlay[:, :, 0])  # Red edges

        # Apply basic thresholding to segment objects
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw contours on the original image
        contour_image = image.copy()
        cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)

        # For this example, return the contour image
        return contour_image


def main(args=None):
    rclpy.init(args=args)

    camera_subscriber = CameraSubscriber()

    try:
        rclpy.spin(camera_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        camera_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
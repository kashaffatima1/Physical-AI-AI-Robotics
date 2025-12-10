import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import os


class CameraPublisher(Node):
    """
    A ROS 2 node that publishes camera images for Physical AI systems.
    This simulates camera data acquisition from real or simulated cameras.
    """

    def __init__(self):
        super().__init__('camera_publisher')

        # Create publisher for camera images
        self.publisher_ = self.create_publisher(Image, 'camera/image_raw', 10)

        # Initialize OpenCV bridge
        self.bridge = CvBridge()

        # Timer to publish images at a consistent rate
        timer_period = 0.033  # ~30 FPS
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Counter for generating different test images
        self.i = 0

        # Load a test image if available, otherwise generate synthetic images
        self.test_image_path = os.getenv('TEST_IMAGE_PATH', None)
        if self.test_image_path and os.path.exists(self.test_image_path):
            self.test_image = cv2.imread(self.test_image_path)
        else:
            self.test_image = None

        self.get_logger().info('Camera Publisher initialized')

    def timer_callback(self):
        # Create or get image
        if self.test_image is not None:
            # Use test image and add some variation
            img = self.test_image.copy()
            # Add some random noise or changes to simulate camera movement
            noise = np.random.randint(0, 20, img.shape, dtype=np.uint8)
            img = cv2.add(img, noise)
        else:
            # Generate a synthetic test image
            img = self.generate_test_image()

        # Convert OpenCV image to ROS Image message
        try:
            msg = self.bridge.cv2_to_imgmsg(img, encoding='bgr8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'camera_frame'

            # Publish the image
            self.publisher_.publish(msg)
            self.get_logger().info(f'Published image {self.i}')

        except Exception as e:
            self.get_logger().error(f'Error converting image: {str(e)}')

        self.i += 1

    def generate_test_image(self):
        """Generate a synthetic test image for camera simulation"""
        # Create a synthetic image with shapes and colors
        img = np.zeros((480, 640, 3), dtype=np.uint8)

        # Add some colored shapes to simulate objects
        cv2.rectangle(img, (100, 100), (200, 200), (255, 0, 0), -1)  # Blue rectangle
        cv2.circle(img, (300, 300), 50, (0, 255, 0), -1)  # Green circle
        cv2.circle(img, (400, 200), 30, (0, 0, 255), -1)  # Red circle

        # Add some text
        cv2.putText(img, f'Frame: {self.i}', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Add some random variations to simulate real camera input
        img = cv2.GaussianBlur(img, (3, 3), 0)

        return img


def main(args=None):
    rclpy.init(args=args)

    camera_publisher = CameraPublisher()

    try:
        rclpy.spin(camera_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        camera_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
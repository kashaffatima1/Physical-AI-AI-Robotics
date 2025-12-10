import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan, Imu
from geometry_msgs.msg import PointStamped, Vector3
from cv_bridge import CvBridge
import cv2
import numpy as np
from collections import deque


class CameraFusionNode(Node):
    """
    A ROS 2 node that fuses camera data with other sensors for Physical AI systems.
    This demonstrates basic sensor fusion techniques combining vision with other modalities.
    """

    def __init__(self):
        super().__init__('camera_fusion')

        # Create subscriber for camera images
        self.camera_subscription = self.create_subscription(
            Image,
            'camera/image_raw',
            self.camera_callback,
            10
        )

        # Create subscriber for LIDAR data (simulating range sensor)
        self.lidar_subscription = self.create_subscription(
            LaserScan,
            'scan',
            self.lidar_callback,
            10
        )

        # Create subscriber for IMU data (simulating inertial sensor)
        self.imu_subscription = self.create_subscription(
            Imu,
            'imu/data',
            self.imu_callback,
            10
        )

        # Create publisher for fused results
        self.fused_publisher = self.create_publisher(
            PointStamped,
            'fused_detection',
            10
        )

        # Initialize OpenCV bridge
        self.bridge = CvBridge()

        # Buffers for temporal synchronization
        self.camera_buffer = deque(maxlen=10)
        self.lidar_buffer = deque(maxlen=10)
        self.imu_buffer = deque(maxlen=10)

        # Latest sensor data
        self.latest_lidar = None
        self.latest_imu = None

        # Counter for processing
        self.process_count = 0

        self.get_logger().info('Camera Fusion Node initialized')

    def camera_callback(self, msg):
        """Process incoming camera image and fuse with other sensors"""
        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # Store camera data with timestamp
            camera_data = {
                'timestamp': msg.header.stamp,
                'image': cv_image,
                'frame_id': msg.header.frame_id
            }

            # Process the image to extract features
            features = self.extract_features(cv_image)

            # Attempt to fuse with other sensors
            if self.latest_lidar is not None and self.latest_imu is not None:
                fused_result = self.fuse_sensors(
                    features,
                    self.latest_lidar,
                    self.latest_imu,
                    msg.header.stamp
                )

                if fused_result is not None:
                    self.fused_publisher.publish(fused_result)
                    self.get_logger().info(
                        f'Published fused detection {self.process_count}'
                    )
                    self.process_count += 1

        except Exception as e:
            self.get_logger().error(f'Error in camera callback: {str(e)}')

    def lidar_callback(self, msg):
        """Process incoming LIDAR data"""
        self.latest_lidar = msg

    def imu_callback(self, msg):
        """Process incoming IMU data"""
        self.latest_imu = msg

    def extract_features(self, image):
        """Extract relevant features from camera image"""
        features = {}

        # Convert to grayscale for processing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect edges
        edges = cv2.Canny(gray, 50, 150)

        # Find contours (potential objects)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Extract features for each contour
        features['contours'] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small contours
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                contour_info = {
                    'area': area,
                    'center': (x + w//2, y + h//2),
                    'bbox': (x, y, w, h),
                    'contour': contour
                }
                features['contours'].append(contour_info)

        # Detect circles
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
            features['circles'] = circles
        else:
            features['circles'] = []

        return features

    def fuse_sensors(self, vision_features, lidar_data, imu_data, timestamp):
        """Fuse vision, LIDAR, and IMU data"""
        try:
            # For demonstration, let's create a fused detection based on:
            # 1. Vision detects an object in the image
            # 2. LIDAR confirms there's something at that bearing
            # 3. IMU provides robot orientation for coordinate transformation

            # Get the first detected contour as an example
            if vision_features['contours']:
                vision_obj = vision_features['contours'][0]

                # Convert image coordinates to bearing angle
                img_width = 640  # Assuming 640px width
                center_x = vision_obj['center'][0]
                bearing = (center_x - img_width/2) / (img_width/2)  # Normalize to [-1, 1]

                # Convert to angle (assuming 60 degree FOV)
                fov_angle = 60.0 * np.pi / 180.0
                angle = bearing * fov_angle / 2

                # Get LIDAR data at the corresponding angle
                angle_increment = lidar_data.angle_increment
                angle_index = int(angle / angle_increment + len(lidar_data.ranges) / 2)

                if 0 <= angle_index < len(lidar_data.ranges):
                    distance = lidar_data.ranges[angle_index]

                    # Only create detection if distance is valid
                    if distance < lidar_data.range_max and distance > lidar_data.range_min:
                        # Create a PointStamped message with fused coordinates
                        point_stamped = PointStamped()
                        point_stamped.header.stamp = timestamp
                        point_stamped.header.frame_id = 'base_link'  # Robot frame

                        # Convert polar to Cartesian coordinates
                        point_stamped.point.x = distance * np.cos(angle)
                        point_stamped.point.y = distance * np.sin(angle)
                        point_stamped.point.z = 0.0  # Assuming ground level

                        # Include IMU data for orientation context
                        point_stamped.point.x += imu_data.linear_acceleration.x * 0.01  # Small offset based on IMU
                        point_stamped.point.y += imu_data.linear_acceleration.y * 0.01

                        return point_stamped

            return None

        except Exception as e:
            self.get_logger().error(f'Error in sensor fusion: {str(e)}')
            return None


def main(args=None):
    rclpy.init(args=args)

    camera_fusion = CameraFusionNode()

    try:
        rclpy.spin(camera_fusion)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        camera_fusion.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
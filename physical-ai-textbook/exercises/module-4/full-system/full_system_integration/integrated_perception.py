#!/usr/bin/env python3
"""
Integrated Perception System for Physical AI
This module implements the perception component of the integrated Physical AI system
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan, Imu, PointCloud2
from geometry_msgs.msg import Point
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import threading
import time
from collections import deque


class IntegratedPerception(Node):
    """
    Integrated Perception System for Physical AI
    Combines multiple sensor modalities for comprehensive environmental understanding
    """

    def __init__(self):
        super().__init__('integrated_perception')

        # Initialize OpenCV bridge
        self.bridge = CvBridge()

        # QoS profile for reliable communication
        from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
        qos_profile = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        # Publishers
        self.perception_status_publisher = self.create_publisher(String, 'perception/status', qos_profile)
        self.object_detections_publisher = self.create_publisher(String, 'perception/objects', qos_profile)

        # Subscribers
        self.image_subscription = self.create_subscription(
            Image, 'camera/image_raw', self.image_callback, qos_profile
        )
        self.lidar_subscription = self.create_subscription(
            LaserScan, 'scan', self.lidar_callback, qos_profile
        )
        self.imu_subscription = self.create_subscription(
            Imu, 'imu/data', self.imu_callback, qos_profile
        )

        # Sensor data buffers
        self.image_buffer = deque(maxlen=5)
        self.lidar_buffer = deque(maxlen=10)
        self.imu_buffer = deque(maxlen=50)

        # Latest sensor data
        self.latest_image = None
        self.latest_lidar = None
        self.latest_imu = None

        # Processing flags
        self.processing_enabled = True

        # Perception components
        self.object_detector = ObjectDetector()
        self.obstacle_detector = ObstacleDetector()
        self.slam_system = SLAMSystem()
        self.fusion_engine = SensorFusionEngine()

        # Perception results
        self.perception_results = {
            'objects': [],
            'obstacles': [],
            'environment_map': None,
            'robot_pose': None,
            'timestamp': None
        }

        # Threading for concurrent processing
        self.processing_thread = threading.Thread(target=self.processing_loop, daemon=True)
        self.processing_thread.start()

        # Timer for perception coordination
        self.perception_timer = self.create_timer(0.1, self.perception_coordination_callback)

        self.get_logger().info('Integrated Perception System initialized')

    def image_callback(self, msg):
        """Handle incoming camera images"""
        self.latest_image = msg
        self.image_buffer.append(msg)

    def lidar_callback(self, msg):
        """Handle incoming LIDAR data"""
        self.latest_lidar = msg
        self.lidar_buffer.append(msg)

    def imu_callback(self, msg):
        """Handle incoming IMU data"""
        self.latest_imu = msg
        self.imu_buffer.append(msg)

    def processing_loop(self):
        """Main processing loop for perception"""
        while rclpy.ok() and self.processing_enabled:
            # Process sensor data if available
            if self.latest_image is not None or self.latest_lidar is not None:
                self.process_sensor_data()

            # Sleep to control processing rate
            time.sleep(0.033)  # ~30 Hz

    def process_sensor_data(self):
        """Process available sensor data"""
        try:
            # Process image data
            if self.latest_image is not None:
                image_cv = self.bridge.imgmsg_to_cv2(self.latest_image, desired_encoding='bgr8')
                objects = self.object_detector.detect_objects(image_cv)
                self.perception_results['objects'] = objects

            # Process LIDAR data
            if self.latest_lidar is not None:
                obstacles = self.obstacle_detector.detect_obstacles(self.latest_lidar)
                self.perception_results['obstacles'] = obstacles

                # Update SLAM system
                self.slam_system.update_with_lidar(self.latest_lidar)

            # Perform sensor fusion
            if self.latest_image is not None and self.latest_lidar is not None:
                fused_data = self.fusion_engine.fuse_data(
                    self.latest_image,
                    self.latest_lidar,
                    self.latest_imu
                )
                self.perception_results.update(fused_data)

            # Update timestamp
            self.perception_results['timestamp'] = time.time()

        except Exception as e:
            self.get_logger().error(f'Error processing sensor data: {e}')

    def perception_coordination_callback(self):
        """Perception coordination callback"""
        # Publish perception status
        status_msg = String()
        status_msg.data = f"Objects: {len(self.perception_results['objects'])}, " \
                         f"Obstacles: {len(self.perception_results['obstacles'])}, " \
                         f"Last update: {self.perception_results['timestamp']}"
        self.perception_status_publisher.publish(status_msg)

        # Publish object detections
        if self.perception_results['objects']:
            objects_msg = String()
            objects_msg.data = str([obj['class'] for obj in self.perception_results['objects']])
            self.object_detections_publisher.publish(objects_msg)

    def get_perception_results(self) -> Dict:
        """Get current perception results"""
        return self.perception_results.copy()

    def enable_processing(self):
        """Enable perception processing"""
        self.processing_enabled = True

    def disable_processing(self):
        """Disable perception processing"""
        self.processing_enabled = False


class ObjectDetector:
    """Object detection component"""

    def __init__(self):
        # In a real system, this would load a trained model
        # For this example, we'll use simple color-based detection
        pass

    def detect_objects(self, image):
        """Detect objects in an image"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define color ranges for different objects
        color_ranges = [
            # Red objects
            (np.array([0, 50, 50]), np.array([10, 255, 255]), 'red_object'),
            (np.array([170, 50, 50]), np.array([180, 255, 255]), 'red_object'),
            # Green objects
            (np.array([40, 50, 50]), np.array([80, 255, 255]), 'green_object'),
            # Blue objects
            (np.array([100, 50, 50]), np.array([130, 255, 255]), 'blue_object'),
        ]

        detected_objects = []

        for lower, upper, obj_class in color_ranges:
            # Create mask
            mask = cv2.inRange(hsv, lower, upper)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Filter small detections
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)

                    detected_objects.append({
                        'class': obj_class,
                        'confidence': 0.8,  # Fixed confidence for this example
                        'bbox': [x, y, x+w, y+h],
                        'center': [x + w//2, y + h//2],
                        'area': area
                    })

        return detected_objects


class ObstacleDetector:
    """Obstacle detection component"""

    def __init__(self):
        self.min_obstacle_distance = 0.5  # meters
        self.max_detection_distance = 3.0  # meters

    def detect_obstacles(self, lidar_msg):
        """Detect obstacles from LIDAR data"""
        obstacles = []

        for i, range_val in enumerate(lidar_msg.ranges):
            if lidar_msg.range_min <= range_val <= lidar_msg.range_max:
                angle = lidar_msg.angle_min + i * lidar_msg.angle_increment
                distance = range_val

                if self.min_obstacle_distance <= distance <= self.max_detection_distance:
                    obstacle = {
                        'angle': angle,
                        'distance': distance,
                        'x': distance * np.cos(angle),
                        'y': distance * np.sin(angle),
                        'range_index': i
                    }
                    obstacles.append(obstacle)

        return obstacles


class SLAMSystem:
    """SLAM (Simultaneous Localization and Mapping) component"""

    def __init__(self):
        self.map = np.zeros((100, 100), dtype=np.uint8)  # Simple occupancy grid
        self.robot_pose = (50, 50, 0)  # x, y, theta

    def update_with_lidar(self, lidar_msg):
        """Update SLAM with LIDAR data"""
        # This is a simplified implementation
        # In a real system, this would perform full SLAM

        # Convert LIDAR data to map coordinates
        for i, range_val in enumerate(lidar_msg.ranges):
            if lidar_msg.range_min <= range_val <= lidar_msg.range_max:
                angle = lidar_msg.angle_min + i * lidar_msg.angle_increment

                # Convert to world coordinates relative to robot
                x_world = range_val * np.cos(angle)
                y_world = range_val * np.sin(angle)

                # Convert to map coordinates (simplified)
                map_x = int(x_world * 10 + 50)  # Scale and offset
                map_y = int(y_world * 10 + 50)

                # Update map if within bounds
                if 0 <= map_x < 100 and 0 <= map_y < 100:
                    self.map[map_y, map_x] = 255  # Mark as occupied


class SensorFusionEngine:
    """Sensor fusion component"""

    def __init__(self):
        self.fusion_method = 'early_fusion'  # Options: early_fusion, late_fusion, deep_fusion

    def fuse_data(self, image_msg, lidar_msg, imu_msg):
        """Fuse data from multiple sensors"""
        fused_results = {}

        # For this example, we'll create simple fused features
        if self.fusion_method == 'early_fusion':
            # Early fusion: combine raw data before processing
            fused_results = self.early_fusion(image_msg, lidar_msg, imu_msg)
        elif self.fusion_method == 'late_fusion':
            # Late fusion: combine processed results
            fused_results = self.late_fusion(image_msg, lidar_msg, imu_msg)
        else:
            # Default to late fusion
            fused_results = self.late_fusion(image_msg, lidar_msg, imu_msg)

        return fused_results

    def early_fusion(self, image_msg, lidar_msg, imu_msg):
        """Early fusion implementation"""
        # This would combine raw sensor data
        return {
            'early_fusion_result': True,
            'confidence': 0.9
        }

    def late_fusion(self, image_msg, lidar_msg, imu_msg):
        """Late fusion implementation"""
        # This would combine processed sensor results
        return {
            'late_fusion_result': True,
            'confidence': 0.95
        }


def main(args=None):
    rclpy.init(args=args)

    integrated_perception = IntegratedPerception()

    try:
        rclpy.spin(integrated_perception)
    except KeyboardInterrupt:
        pass
    finally:
        integrated_perception.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
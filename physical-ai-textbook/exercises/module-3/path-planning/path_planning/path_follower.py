import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped, Point
from nav_msgs.msg import Path, Odometry
from std_msgs.msg import Header
import numpy as np
from typing import List, Tuple
import math


class PathFollower(Node):
    """
    Path following controller for Physical AI systems.
    Follows a path using a simple pure pursuit algorithm.
    """

    def __init__(self):
        super().__init__('path_follower')

        # Create publisher for velocity commands
        self.cmd_vel_publisher = self.create_publisher(Twist, 'cmd_vel', 10)

        # Create subscriber for path
        self.path_subscription = self.create_subscription(
            Path,
            'path_planner/path',
            self.path_callback,
            10
        )

        # Create subscriber for robot odometry
        self.odom_subscription = self.create_subscription(
            Odometry,
            'odom',
            self.odom_callback,
            10
        )

        # Initialize variables
        self.path = []
        self.current_pose = None
        self.current_velocity = None
        self.path_index = 0
        self.lookahead_distance = 0.5  # meters
        self.linear_speed = 0.3  # m/s
        self.angular_speed_limit = 1.0  # rad/s
        self.path_completed = False

        # Timer for control loop
        self.control_timer = self.create_timer(0.05, self.control_loop)  # 20 Hz

        self.get_logger().info('Path Follower initialized')

    def path_callback(self, msg):
        """Callback to receive path"""
        self.path = [(pose.pose.position.x, pose.pose.position.y) for pose in msg.poses]
        self.path_index = 0
        self.path_completed = False
        self.get_logger().info(f'Received path with {len(self.path)} waypoints')

    def odom_callback(self, msg):
        """Callback to receive robot odometry"""
        self.current_pose = (
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            self.quaternion_to_yaw(msg.pose.pose.orientation)
        )
        self.current_velocity = math.sqrt(
            msg.twist.twist.linear.x**2 + msg.twist.twist.linear.y**2
        )

    def quaternion_to_yaw(self, orientation):
        """Convert quaternion to yaw angle"""
        siny_cosp = 2 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cosy_cosp = 1 - 2 * (orientation.y * orientation.y + orientation.z * orientation.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def control_loop(self):
        """Main control loop for path following"""
        if not self.path or self.path_completed or self.current_pose is None:
            # Stop the robot if no path or no pose
            self.stop_robot()
            return

        # Get current robot position
        robot_x, robot_y, robot_yaw = self.current_pose

        # Find next waypoint to track
        target_x, target_y = self.get_lookahead_point(robot_x, robot_y)

        if target_x is None or target_y is None:
            # Path completed
            self.path_completed = True
            self.stop_robot()
            self.get_logger().info('Path following completed')
            return

        # Calculate control commands
        linear_vel, angular_vel = self.pure_pursuit_control(
            robot_x, robot_y, robot_yaw, target_x, target_y
        )

        # Publish velocity command
        cmd_msg = Twist()
        cmd_msg.linear.x = linear_vel
        cmd_msg.angular.z = angular_vel
        self.cmd_vel_publisher.publish(cmd_msg)

        # Log current status
        distance_to_goal = math.sqrt(
            (self.path[-1][0] - robot_x)**2 + (self.path[-1][1] - robot_y)**2
        )
        self.get_logger().info(
            f'Following path: {self.path_index}/{len(self.path)} waypoints, '
            f'distance to goal: {distance_to_goal:.2f}m'
        )

    def get_lookahead_point(self, robot_x: float, robot_y: float) -> Tuple[float, float]:
        """Find the point on the path that is lookahead_distance away from the robot"""
        if self.path_index >= len(self.path):
            return None, None

        # Start from current path index
        for i in range(self.path_index, len(self.path)):
            waypoint_x, waypoint_y = self.path[i]

            # Calculate distance to this waypoint
            dist = math.sqrt((waypoint_x - robot_x)**2 + (waypoint_y - robot_y)**2)

            # If this waypoint is beyond lookahead distance, we need to interpolate
            if dist >= self.lookahead_distance:
                # Find the exact point at lookahead distance along the path
                if i > 0:
                    prev_x, prev_y = self.path[i-1]
                    # Interpolate between previous and current waypoint
                    direction_x = waypoint_x - prev_x
                    direction_y = waypoint_y - prev_y
                    direction_norm = math.sqrt(direction_x**2 + direction_y**2)

                    if direction_norm > 0:
                        # Normalize direction
                        direction_x /= direction_norm
                        direction_y /= direction_norm

                        # Find point at lookahead distance
                        target_x = robot_x + self.lookahead_distance * direction_x
                        target_y = robot_y + self.lookahead_distance * direction_y

                        return target_x, target_y
                else:
                    # First waypoint, just return it
                    return waypoint_x, waypoint_y

            # If we're close to the last waypoint, we've completed the path
            if i == len(self.path) - 1:
                # Check if we're close enough to the final waypoint
                if dist < 0.2:  # 20 cm tolerance
                    return None, None
                else:
                    # Return the final waypoint
                    return waypoint_x, waypoint_y

        # If we've exhausted the path without finding a lookahead point,
        # advance the path index and try again
        self.path_index = min(self.path_index + 1, len(self.path) - 1)
        return self.get_lookahead_point(robot_x, robot_y)

    def pure_pursuit_control(self, robot_x: float, robot_y: float, robot_yaw: float,
                           target_x: float, target_y: float) -> Tuple[float, float]:
        """Pure pursuit path following algorithm"""
        # Calculate relative position of target
        dx = target_x - robot_x
        dy = target_y - robot_y

        # Calculate distance to target
        distance_to_target = math.sqrt(dx**2 + dy**2)

        # Calculate angle to target relative to robot heading
        angle_to_target = math.atan2(dy, dx)
        angle_error = angle_to_target - robot_yaw

        # Normalize angle error to [-π, π]
        while angle_error > math.pi:
            angle_error -= 2 * math.pi
        while angle_error < -math.pi:
            angle_error += 2 * math.pi

        # Calculate angular velocity proportional to angle error
        angular_vel = 1.5 * angle_error  # Gain for angular velocity

        # Limit angular velocity
        angular_vel = max(-self.angular_speed_limit,
                         min(self.angular_speed_limit, angular_vel))

        # Calculate linear velocity based on angular error
        # Reduce linear speed when turning sharply
        linear_vel = self.linear_speed * math.cos(angle_error)
        linear_vel = max(0.1, linear_vel)  # Minimum speed to keep moving

        return linear_vel, angular_vel

    def stop_robot(self):
        """Stop the robot"""
        cmd_msg = Twist()
        cmd_msg.linear.x = 0.0
        cmd_msg.angular.z = 0.0
        self.cmd_vel_publisher.publish(cmd_msg)

    def follow_path(self, path: List[Tuple[float, float]]):
        """Set a path to follow"""
        self.path = path
        self.path_index = 0
        self.path_completed = False


def main(args=None):
    rclpy.init(args=args)

    path_follower = PathFollower()

    try:
        rclpy.spin(path_follower)
    except KeyboardInterrupt:
        pass
    finally:
        # Stop robot before shutting down
        path_follower.stop_robot()
        path_follower.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
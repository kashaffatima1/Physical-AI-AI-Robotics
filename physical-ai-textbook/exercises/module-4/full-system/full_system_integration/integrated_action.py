#!/usr/bin/env python3
"""
Integrated Action System for Physical AI
This module implements the action component of the integrated Physical AI system
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Point, Pose
from nav_msgs.msg import Path, Odometry
from std_msgs.msg import String, Bool
from builtin_interfaces.msg import Time
import numpy as np
import threading
import time
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
import math


class IntegratedAction(Node):
    """
    Integrated Action System for Physical AI
    Handles motion control, manipulation, and behavior execution
    """

    def __init__(self):
        super().__init__('integrated_action')

        # QoS profile for reliable communication
        from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
        qos_profile = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        # Publishers
        self.cmd_vel_publisher = self.create_publisher(Twist, 'cmd_vel', qos_profile)
        self.action_status_publisher = self.create_publisher(String, 'action/status', qos_profile)
        self.behavior_publisher = self.create_publisher(String, 'action/behavior', qos_profile)

        # Subscribers
        self.decision_subscription = self.create_subscription(
            String, 'cognition/decision', self.decision_callback, qos_profile
        )
        self.plan_subscription = self.create_subscription(
            Path, 'cognition/plan', self.plan_callback, qos_profile
        )
        self.odom_subscription = self.create_subscription(
            Odometry, 'odom', self.odom_callback, qos_profile
        )

        # System state
        self.current_decision = 'idle'
        self.current_plan = None
        self.current_behavior = 'idle'
        self.robot_pose = (0.0, 0.0, 0.0)  # x, y, theta
        self.robot_velocity = (0.0, 0.0)  # linear, angular
        self.system_active = True

        # Action components
        self.motion_controller = MotionController(self)
        self.behavior_executor = BehaviorExecutor(self)
        self.safety_monitor = SafetyMonitor(self)

        # Data buffers
        self.decision_buffer = deque(maxlen=5)
        self.plan_buffer = deque(maxlen=3)

        # Threading for concurrent processing
        self.execution_thread = threading.Thread(target=self.execution_loop, daemon=True)
        self.execution_thread.start()

        # Timer for action coordination
        self.action_timer = self.create_timer(0.05, self.action_coordination_callback)  # 20 Hz

        self.get_logger().info('Integrated Action System initialized')

    def decision_callback(self, msg):
        """Handle incoming decisions from cognition system"""
        self.current_decision = msg.data
        self.decision_buffer.append(msg.data)

    def plan_callback(self, msg):
        """Handle incoming plans from cognition system"""
        # Convert Path message to list of waypoints
        waypoints = []
        for pose_stamped in msg.poses:
            waypoints.append((
                pose_stamped.pose.position.x,
                pose_stamped.pose.position.y
            ))

        self.current_plan = waypoints
        self.plan_buffer.append(waypoints)

    def odom_callback(self, msg):
        """Handle incoming odometry data"""
        self.robot_pose = (
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            self.quaternion_to_yaw(msg.pose.pose.orientation)
        )
        self.robot_velocity = (
            msg.twist.twist.linear.x,
            msg.twist.twist.angular.z
        )

    def quaternion_to_yaw(self, orientation):
        """Convert quaternion to yaw angle"""
        siny_cosp = 2 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cosy_cosp = 1 - 2 * (orientation.y * orientation.y + orientation.z * orientation.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def execution_loop(self):
        """Action execution loop"""
        while rclpy.ok() and self.system_active:
            # Execute current behavior
            self.execute_current_behavior()

            # Sleep to control execution rate
            time.sleep(0.05)  # 20 Hz

    def execute_current_behavior(self):
        """Execute the current behavior based on decision"""
        try:
            if self.current_decision == 'safety_stop':
                self.behavior_executor.execute_safety_stop()
            elif self.current_decision.startswith('navigate'):
                self.behavior_executor.execute_navigation(self.current_plan)
            elif self.current_decision.startswith('cautious'):
                self.behavior_executor.execute_cautious_behavior(self.current_decision)
            elif self.current_decision == 'replan':
                self.behavior_executor.execute_replan_behavior()
            elif self.current_decision == 'wait':
                self.behavior_executor.execute_wait_behavior()
            else:
                # Default to idle
                self.behavior_executor.execute_idle()

        except Exception as e:
            self.get_logger().error(f'Error executing behavior: {e}')
            self.behavior_executor.execute_idle()

    def action_coordination_callback(self):
        """Action coordination callback"""
        # Monitor safety conditions
        safety_violation = self.safety_monitor.check_safety_conditions()

        if safety_violation:
            self.current_decision = 'safety_stop'
            self.get_logger().warn(f'Safety violation detected: {safety_violation}')

        # Update behavior status
        behavior_msg = String()
        behavior_msg.data = self.current_behavior
        self.behavior_publisher.publish(behavior_msg)

        # Update action status
        status_msg = String()
        status_msg.data = f"Behavior: {self.current_behavior}, Decision: {self.current_decision}, Pose: ({self.robot_pose[0]:.2f}, {self.robot_pose[1]:.2f}, {self.robot_pose[2]:.2f})"
        self.action_status_publisher.publish(status_msg)

    def get_robot_state(self) -> Dict:
        """Get current robot state"""
        return {
            'pose': self.robot_pose,
            'velocity': self.robot_velocity,
            'current_decision': self.current_decision,
            'current_behavior': self.current_behavior
        }


class MotionController:
    """Motion control component"""

    def __init__(self, node):
        self.node = node
        self.max_linear_speed = 0.5  # m/s
        self.max_angular_speed = 1.0  # rad/s
        self.linear_tolerance = 0.1  # m
        self.angular_tolerance = 0.1  # rad

    def move_to_pose(self, target_x: float, target_y: float, target_theta: float = None) -> Twist:
        """Generate command to move to a specific pose"""
        cmd = Twist()

        # Calculate distance to target
        dx = target_x - self.node.robot_pose[0]
        dy = target_y - self.node.robot_pose[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance > self.linear_tolerance:
            # Calculate desired heading
            desired_theta = math.atan2(dy, dx)

            # Calculate heading error
            theta_error = desired_theta - self.node.robot_pose[2]

            # Normalize angle error
            while theta_error > math.pi:
                theta_error -= 2 * math.pi
            while theta_error < -math.pi:
                theta_error += 2 * math.pi

            # Proportional control for angular velocity
            cmd.angular.z = max(-self.max_angular_speed,
                               min(self.max_angular_speed, 2.0 * theta_error))

            # Linear velocity based on distance (slow down when close)
            cmd.linear.x = max(0.1, min(self.max_linear_speed, 0.5 * distance))
        else:
            # Close enough to target position, stop linear motion
            cmd.linear.x = 0.0

            if target_theta is not None:
                # Adjust orientation to target theta
                theta_error = target_theta - self.node.robot_pose[2]

                # Normalize angle error
                while theta_error > math.pi:
                    theta_error -= 2 * math.pi
                while theta_error < -math.pi:
                    theta_error += 2 * math.pi

                # Proportional control for angular velocity
                cmd.angular.z = max(-self.max_angular_speed,
                                   min(self.max_angular_speed, 2.0 * theta_error))
            else:
                cmd.angular.z = 0.0

        return cmd

    def follow_path(self, path: List[Tuple[float, float]], lookahead_distance: float = 0.5) -> Twist:
        """Follow a path using pure pursuit algorithm"""
        if not path:
            return Twist()  # Stop if no path

        cmd = Twist()

        # Find the point on the path that is lookahead_distance away from the robot
        robot_x, robot_y = self.node.robot_pose[0], self.node.robot_pose[1]

        closest_idx = 0
        min_dist = float('inf')

        # Find closest point on path
        for i, (x, y) in enumerate(path):
            dist = math.sqrt((x - robot_x)**2 + (y - robot_y)**2)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        # Find the point that is lookahead_distance ahead of the closest point
        target_x, target_y = path[-1]  # Default to last point

        for i in range(closest_idx, len(path)):
            dist_to_robot = math.sqrt((path[i][0] - robot_x)**2 + (path[i][1] - robot_y)**2)

            if dist_to_robot >= lookahead_distance:
                target_x, target_y = path[i]
                break
        else:
            # If no point is far enough, use the last point
            target_x, target_y = path[-1]

        # Calculate control using pure pursuit
        dx = target_x - robot_x
        dy = target_y - robot_y
        distance_to_target = math.sqrt(dx**2 + dy**2)

        if distance_to_target > 0.1:  # Only move if target is far enough
            # Calculate angle to target relative to robot heading
            angle_to_target = math.atan2(dy, dx)
            robot_heading = self.node.robot_pose[2]
            angle_error = angle_to_target - robot_heading

            # Normalize angle error
            while angle_error > math.pi:
                angle_error -= 2 * math.pi
            while angle_error < -math.pi:
                angle_error += 2 * math.pi

            # Calculate angular velocity proportional to angle error
            cmd.angular.z = max(-self.max_angular_speed,
                               min(self.max_angular_speed, 2.0 * angle_error))

            # Calculate linear velocity based on angle error (reduce speed when turning sharply)
            cmd.linear.x = max(0.1, self.max_linear_speed * math.cos(angle_error))

        return cmd

    def stop_robot(self) -> Twist:
        """Generate command to stop the robot"""
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        return cmd


class BehaviorExecutor:
    """Behavior execution component"""

    def __init__(self, node):
        self.node = node
        self.current_behavior = 'idle'
        self.behavior_start_time = None
        self.waypoint_index = 0

    def execute_idle(self):
        """Execute idle behavior"""
        if self.current_behavior != 'idle':
            self._change_behavior('idle')

        # Stop the robot
        cmd = self.node.motion_controller.stop_robot()
        self.node.cmd_vel_publisher.publish(cmd)

    def execute_navigation(self, plan: List[Tuple[float, float]]):
        """Execute navigation behavior"""
        if self.current_behavior != 'navigation':
            self._change_behavior('navigation')
            self.waypoint_index = 0

        if plan and len(plan) > 0:
            # Follow the plan using path following
            cmd = self.node.motion_controller.follow_path(plan)
            self.node.cmd_vel_publisher.publish(cmd)
        else:
            # No plan, go to idle
            self.execute_idle()

    def execute_safety_stop(self):
        """Execute safety stop behavior"""
        if self.current_behavior != 'safety_stop':
            self._change_behavior('safety_stop')

        # Emergency stop
        cmd = self.node.motion_controller.stop_robot()
        self.node.cmd_vel_publisher.publish(cmd)

    def execute_cautious_behavior(self, decision: str):
        """Execute cautious behavior"""
        base_behavior = decision.replace('cautious_', '')

        if self.current_behavior != f'cautious_{base_behavior}':
            self._change_behavior(f'cautious_{base_behavior}')

        # Modify commands to be more cautious (reduce speeds)
        if base_behavior == 'navigate':
            plan = self.node.current_plan
            if plan and len(plan) > 0:
                cmd = self.node.motion_controller.follow_path(plan)
                # Reduce speeds for cautious navigation
                cmd.linear.x *= 0.5
                cmd.angular.z *= 0.7
                self.node.cmd_vel_publisher.publish(cmd)
        else:
            self.execute_idle()

    def execute_replan_behavior(self):
        """Execute replan behavior"""
        if self.current_behavior != 'replan':
            self._change_behavior('replan')

        # Stop robot while waiting for new plan
        cmd = self.node.motion_controller.stop_robot()
        self.node.cmd_vel_publisher.publish(cmd)

    def execute_wait_behavior(self):
        """Execute wait behavior"""
        if self.current_behavior != 'wait':
            self._change_behavior('wait')

        # Stop robot
        cmd = self.node.motion_controller.stop_robot()
        self.node.cmd_vel_publisher.publish(cmd)

    def _change_behavior(self, new_behavior: str):
        """Internal method to change behavior"""
        self.current_behavior = new_behavior
        self.behavior_start_time = time.time()
        self.node.current_behavior = new_behavior
        self.node.get_logger().info(f'Changed behavior to: {new_behavior}')


class SafetyMonitor:
    """Safety monitoring component"""

    def __init__(self, node):
        self.node = node
        self.safety_thresholds = {
            'min_obstacle_distance': 0.5,  # meters
            'max_linear_speed': 1.0,      # m/s
            'max_angular_speed': 2.0,     # rad/s
            'max_current': 10.0           # arbitrary unit
        }

    def check_safety_conditions(self) -> Optional[str]:
        """Check safety conditions and return violation description if any"""
        # This would integrate with perception system to check for obstacles
        # For this example, we'll simulate checking based on velocity

        linear_speed = abs(self.node.robot_velocity[0])
        angular_speed = abs(self.node.robot_velocity[1])

        if linear_speed > self.safety_thresholds['max_linear_speed']:
            return f'linear_speed_exceeded: {linear_speed} > {self.safety_thresholds["max_linear_speed"]}'

        if angular_speed > self.safety_thresholds['max_angular_speed']:
            return f'angular_speed_exceeded: {angular_speed} > {self.safety_thresholds["max_angular_speed"]}'

        # In a real system, this would check for obstacles from perception
        # For simulation, we'll create a scenario where safety stop is needed
        if self.node.current_decision == 'safety_test':
            return 'simulated_obstacle_ahead'

        return None


def main(args=None):
    rclpy.init(args=args)

    integrated_action = IntegratedAction()

    try:
        rclpy.spin(integrated_action)
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure robot stops on shutdown
        stop_cmd = Twist()
        integrated_action.cmd_vel_publisher.publish(stop_cmd)
        integrated_action.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
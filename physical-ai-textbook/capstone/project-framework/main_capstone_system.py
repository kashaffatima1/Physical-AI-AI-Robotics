#!/usr/bin/env python3
"""
Capstone Project Framework: Autonomous Physical AI Assistant for Smart Environments

This is the main system framework that integrates all components for the capstone project.
"""

import rospy
import numpy as np
import cv2
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# ROS imports
from sensor_msgs.msg import Image, LaserScan, Imu
from geometry_msgs.msg import Twist, Pose, Point, Vector3
from nav_msgs.msg import Odometry
from std_msgs.msg import String, Float32
from visualization_msgs.msg import Marker, MarkerArray
from tf.transformations import euler_from_quaternion, quaternion_from_euler

# Action libraries for navigation
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import PoseStamped

# Custom message types (these would be defined in your package)
try:
    from capstone_msgs.msg import Task, TaskStatus, HumanDetection, EnvironmentMap
except ImportError:
    # Fallback for when custom messages are not available
    print("Custom message types not available, using standard types")


class TaskState(Enum):
    """Enumeration for task states"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class TaskDefinition:
    """Data class for task definitions"""
    id: str
    name: str
    description: str
    priority: int  # 1-10 scale, 10 is highest
    required_resources: List[str]
    estimated_duration: float  # in seconds
    success_criteria: List[str]
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PerceptionSystem:
    """Perception system for environment understanding"""

    def __init__(self):
        # Initialize subscribers
        self.image_sub = rospy.Subscriber('/camera/rgb/image_raw', Image, self.image_callback)
        self.laser_sub = rospy.Subscriber('/scan', LaserScan, self.laser_callback)
        self.odom_sub = rospy.Subscriber('/odom', Odometry, self.odom_callback)
        self.imu_sub = rospy.Subscriber('/imu', Imu, self.imu_callback)

        # Initialize publishers
        self.marker_pub = rospy.Publisher('/visualization_marker', Marker, queue_size=10)
        self.environment_map_pub = rospy.Publisher('/environment_map', String, queue_size=10)

        # State variables
        self.current_pose = None
        self.odom_data = None
        self.imu_data = None
        self.laser_data = None
        self.image_data = None
        self.obstacles = []
        self.humans = []
        self.objects = []

        # Processing parameters
        self.obstacle_threshold = 1.0  # meters
        self.human_detection_range = 3.0  # meters
        self.object_detection_range = 2.0  # meters

        # Camera parameters
        self.camera_matrix = np.array([[554.25, 0.0, 320.5], [0.0, 554.25, 240.5], [0.0, 0.0, 1.0]])

        print("Perception System initialized")

    def image_callback(self, data):
        """Process image data from camera"""
        # Convert ROS Image to OpenCV format
        # In a real implementation, you'd use cv_bridge
        # For simulation, we'll just store the raw data
        self.image_data = data

        # Process image for object detection (simplified)
        self.detect_objects_in_image()

    def laser_callback(self, data):
        """Process LIDAR data for obstacle detection"""
        self.laser_data = data
        self.detect_obstacles()
        self.detect_humans()

    def odom_callback(self, data):
        """Process odometry data"""
        self.odom_data = data
        self.current_pose = data.pose.pose

    def imu_callback(self, data):
        """Process IMU data"""
        self.imu_data = data

    def detect_objects_in_image(self):
        """Detect objects in the camera image"""
        # This would use a trained object detection model in practice
        # For simulation, we'll create some dummy objects
        if self.image_data is not None:
            # Simulated object detection
            self.objects = [
                {"type": "cup", "position": (1.5, 2.0, 0.0), "confidence": 0.85},
                {"type": "document", "position": (3.2, -1.5, 0.0), "confidence": 0.92},
                {"type": "person", "position": (-0.5, 1.0, 0.0), "confidence": 0.98}
            ]

    def detect_obstacles(self):
        """Detect obstacles from LIDAR data"""
        if self.laser_data is not None:
            ranges = np.array(self.laser_data.ranges)
            valid_ranges = ranges[(ranges > self.laser_data.range_min) & (ranges < self.laser_data.range_max)]

            self.obstacles = []
            for i, range_val in enumerate(valid_ranges):
                if range_val < self.obstacle_threshold:
                    angle = self.laser_data.angle_min + i * self.laser_data.angle_increment
                    # Convert to global coordinates relative to robot
                    if self.current_pose:
                        x_local = range_val * np.cos(angle)
                        y_local = range_val * np.sin(angle)
                        # Transform to global coordinates (simplified)
                        global_x = self.current_pose.position.x + x_local
                        global_y = self.current_pose.position.y + y_local
                        self.obstacles.append((global_x, global_y, range_val))

    def detect_humans(self):
        """Detect humans in the environment"""
        # Simplified human detection based on LIDAR data
        if self.laser_data is not None:
            ranges = np.array(self.laser_data.ranges)
            angles = np.array([self.laser_data.angle_min + i * self.laser_data.angle_increment
                              for i in range(len(ranges))])

            human_candidates = []
            for i, range_val in enumerate(ranges):
                if self.laser_data.range_min < range_val < self.human_detection_range:
                    # Check if this point is part of a larger cluster (indicating human shape)
                    # Simplified approach: look for clusters of points at similar distances
                    if i > 0 and i < len(ranges) - 1:
                        prev_range = ranges[i-1]
                        next_range = ranges[i+1]

                        # If adjacent points are close in range, it might be a human
                        if abs(range_val - prev_range) < 0.3 and abs(range_val - next_range) < 0.3:
                            angle = angles[i]
                            x_local = range_val * np.cos(angle)
                            y_local = range_val * np.sin(angle)

                            if self.current_pose:
                                global_x = self.current_pose.position.x + x_local
                                global_y = self.current_pose.position.y + y_local
                                human_candidates.append((global_x, global_y, range_val))

            self.humans = human_candidates

    def get_environment_map(self) -> Dict[str, Any]:
        """Return current environment map"""
        env_map = {
            "timestamp": rospy.Time.now().to_sec(),
            "robot_pose": {
                "x": self.current_pose.position.x if self.current_pose else 0.0,
                "y": self.current_pose.position.y if self.current_pose else 0.0,
                "z": self.current_pose.position.z if self.current_pose else 0.0,
                "orientation": {
                    "x": self.current_pose.orientation.x if self.current_pose else 0.0,
                    "y": self.current_pose.orientation.y if self.current_pose else 0.0,
                    "z": self.current_pose.orientation.z if self.current_pose else 0.0,
                    "w": self.current_pose.orientation.w if self.current_pose else 1.0
                }
            } if self.current_pose else None,
            "obstacles": [{"x": x, "y": y, "distance": d} for x, y, d in self.obstacles],
            "humans": [{"x": x, "y": y, "distance": d} for x, y, d in self.humans],
            "objects": self.objects,
            "safety_zone_active": len(self.humans) > 0  # Safety zone if humans detected
        }

        return env_map

    def publish_environment_map(self):
        """Publish environment map to ROS topic"""
        env_map = self.get_environment_map()
        json_map = json.dumps(env_map)
        self.environment_map_pub.publish(String(json_map))


class PathPlanner:
    """Path planning system for navigation"""

    def __init__(self):
        # Initialize path planning parameters
        self.resolution = 0.1  # meters per grid cell
        self.inflation_radius = 0.5  # meters to inflate obstacles
        self.goal_tolerance = 0.5  # meters tolerance for reaching goal

        # Action client for move_base
        self.move_base_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        self.move_base_client.wait_for_server()

        print("Path Planner initialized")

    def plan_path(self, start_pose: Pose, goal_pose: Pose, obstacles: List[Tuple[float, float, float]]) -> Optional[List[Tuple[float, float]]]:
        """Plan a path from start to goal avoiding obstacles"""
        # Simplified path planning - in practice, this would use A*, Dijkstra, or RRT
        # For this framework, we'll use the move_base action client

        # Create a MoveBaseGoal
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose = goal_pose

        # Send the goal to the action server
        self.move_base_client.send_goal(goal)

        # Return None since path planning is handled by move_base
        return None

    def is_path_clear(self, start: Tuple[float, float], goal: Tuple[float, float], obstacles: List[Tuple[float, float, float]]) -> bool:
        """Check if path from start to goal is clear of obstacles"""
        # Simplified line-of-sight check
        dx = goal[0] - start[0]
        dy = goal[1] - start[1]
        distance = np.sqrt(dx*dx + dy*dy)

        # Sample points along the path
        steps = int(distance / self.resolution)
        for i in range(steps):
            t = i / steps
            x = start[0] + t * dx
            y = start[1] + t * dy

            # Check if this point is too close to any obstacle
            for obs_x, obs_y, obs_radius in obstacles:
                dist_to_obs = np.sqrt((x - obs_x)**2 + (y - obs_y)**2)
                if dist_to_obs < obs_radius + 0.3:  # Add safety margin
                    return False

        return True

    def send_navigation_goal(self, goal_pose: Pose) -> bool:
        """Send navigation goal to move_base"""
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose = goal_pose

        # Send goal
        self.move_base_client.send_goal(goal)

        # Wait for result with timeout
        finished_within_time = self.move_base_client.wait_for_result(rospy.Duration(60.0))

        if not finished_within_time:
            self.move_base_client.cancel_goal()
            return False

        # Get result
        state = self.move_base_client.get_state()
        result = self.move_base_client.get_result()

        return state == actionlib.GoalStatus.SUCCEEDED


class DecisionMakingSystem:
    """Decision making system for task prioritization and execution"""

    def __init__(self):
        self.current_task = None
        self.task_queue = []
        self.task_history = []
        self.emergency_active = False

        # Publishers for task management
        self.task_status_pub = rospy.Publisher('/task_status', String, queue_size=10)

        print("Decision Making System initialized")

    def add_task(self, task: TaskDefinition):
        """Add a task to the queue"""
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)  # Higher priority first

    def get_next_task(self) -> Optional[TaskDefinition]:
        """Get the next task to execute based on priority and dependencies"""
        if not self.task_queue:
            return None

        # Check dependencies and return highest priority available task
        for task in self.task_queue:
            if self._dependencies_satisfied(task):
                return task

        return None

    def _dependencies_satisfied(self, task: TaskDefinition) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            # Check if dependency was completed
            dep_completed = any(t.id == dep_id and t.id in [h.id for h in self.task_history]
                              for t in self.task_history)
            if not dep_completed:
                return False
        return True

    def make_decision(self, environment_map: Dict[str, Any]) -> Optional[TaskDefinition]:
        """Make a decision based on current environment"""
        # Check for emergencies first
        if self._check_emergency(environment_map):
            self.emergency_active = True
            return self._create_emergency_task()

        # Get next task from queue
        next_task = self.get_next_task()

        # Update current task if none is active
        if self.current_task is None and next_task:
            self.current_task = next_task
            self._publish_task_status(self.current_task, TaskState.PLANNING)

        return next_task

    def _check_emergency(self, environment_map: Dict[str, Any]) -> bool:
        """Check if there's an emergency situation"""
        # For simulation, consider it an emergency if humans are very close (less than 0.5m)
        for human in environment_map.get("humans", []):
            if human.get("distance", float('inf')) < 0.5:
                return True
        return False

    def _create_emergency_task(self) -> TaskDefinition:
        """Create an emergency task"""
        return TaskDefinition(
            id="emergency_stop",
            name="Emergency Stop",
            description="Immediate stop due to safety concern",
            priority=10,
            required_resources=["navigation", "control"],
            estimated_duration=1.0,
            success_criteria=["robot_stopped", "safety_ensured"]
        )

    def update_task_status(self, task_id: str, status: TaskState):
        """Update the status of a task"""
        if self.current_task and self.current_task.id == task_id:
            self._publish_task_status(self.current_task, status)

            if status in [TaskState.COMPLETED, TaskState.FAILED]:
                # Move current task to history
                self.task_history.append(self.current_task)
                self.current_task = None
                # Remove from queue
                self.task_queue = [t for t in self.task_queue if t.id != task_id]

    def _publish_task_status(self, task: TaskDefinition, status: TaskState):
        """Publish task status to ROS topic"""
        status_msg = {
            "task_id": task.id,
            "task_name": task.name,
            "status": status.value,
            "timestamp": rospy.Time.now().to_sec()
        }
        self.task_status_pub.publish(String(json.dumps(status_msg)))


class ControlSystem:
    """Control system for robot actuation"""

    def __init__(self):
        # Publisher for velocity commands
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

        # Parameters for safety
        self.max_linear_vel = 0.5  # m/s
        self.max_angular_vel = 0.5  # rad/s
        self.safety_enabled = True

        # Robot state
        self.is_moving = False
        self.emergency_stop_active = False

        print("Control System initialized")

    def move_robot(self, linear_x: float = 0.0, linear_y: float = 0.0, linear_z: float = 0.0,
                   angular_x: float = 0.0, angular_y: float = 0.0, angular_z: float = 0.0):
        """Send velocity commands to robot"""
        if self.emergency_stop_active:
            self.stop_robot()
            return

        cmd = Twist()
        cmd.linear.x = max(min(linear_x, self.max_linear_vel), -self.max_linear_vel)
        cmd.linear.y = max(min(linear_y, self.max_linear_vel), -self.max_linear_vel)
        cmd.linear.z = max(min(linear_z, self.max_linear_vel), -self.max_linear_vel)
        cmd.angular.x = max(min(angular_x, self.max_angular_vel), -self.max_angular_vel)
        cmd.angular.y = max(min(angular_y, self.max_angular_vel), -self.max_angular_vel)
        cmd.angular.z = max(min(angular_z, self.max_angular_vel), -self.max_angular_vel)

        # Apply safety constraints
        if self.safety_enabled:
            cmd = self._apply_safety_constraints(cmd)

        self.cmd_vel_pub.publish(cmd)
        self.is_moving = True

    def _apply_safety_constraints(self, cmd: Twist) -> Twist:
        """Apply safety constraints to velocity commands"""
        # Reduce speed if humans are nearby (simplified)
        # In a real system, this would integrate with perception system
        return cmd

    def stop_robot(self):
        """Stop the robot immediately"""
        cmd = Twist()
        self.cmd_vel_pub.publish(cmd)
        self.is_moving = False

    def execute_navigation(self, goal_pose: Pose) -> bool:
        """Execute navigation to goal pose using path planner"""
        # This would typically be handled by the PathPlanner
        # For this framework, we'll just return True
        return True

    def enable_emergency_stop(self):
        """Enable emergency stop"""
        self.emergency_stop_active = True
        self.stop_robot()

    def disable_emergency_stop(self):
        """Disable emergency stop"""
        self.emergency_stop_active = False


class HumanRobotInteraction:
    """Human-robot interaction system"""

    def __init__(self):
        # Publisher for HRI status
        self.hri_status_pub = rospy.Publisher('/hri_status', String, queue_size=10)

        # Parameters
        self.personal_space_radius = 1.0  # meters
        self.social_space_radius = 2.0   # meters
        self.safety_space_radius = 0.5   # meters

        print("Human-Robot Interaction System initialized")

    def check_human_safety(self, environment_map: Dict[str, Any]) -> Dict[str, Any]:
        """Check safety regarding humans in environment"""
        safety_status = {
            "humans_detected": len(environment_map.get("humans", [])) > 0,
            "safety_violations": [],
            "recommended_action": "continue_normal"
        }

        robot_pos = environment_map.get("robot_pose", {})
        if robot_pos:
            robot_x = robot_pos.get("x", 0.0)
            robot_y = robot_pos.get("y", 0.0)
        else:
            robot_x, robot_y = 0.0, 0.0

        for human in environment_map.get("humans", []):
            human_x = human.get("x", 0.0)
            human_y = human.get("y", 0.0)

            dist_to_human = np.sqrt((robot_x - human_x)**2 + (robot_y - human_y)**2)

            if dist_to_human < self.safety_space_radius:
                safety_status["safety_violations"].append({
                    "type": "too_close",
                    "distance": dist_to_human,
                    "recommended_action": "emergency_stop"
                })
                safety_status["recommended_action"] = "emergency_stop"
            elif dist_to_human < self.personal_space_radius:
                safety_status["safety_violations"].append({
                    "type": "in_personal_space",
                    "distance": dist_to_human,
                    "recommended_action": "reduce_speed"
                })
                if safety_status["recommended_action"] == "continue_normal":
                    safety_status["recommended_action"] = "reduce_speed"

        return safety_status

    def generate_hri_response(self, human_action: str) -> str:
        """Generate appropriate response to human action"""
        responses = {
            "wave": "Hello! How can I assist you today?",
            "point": "I see you're pointing. Let me navigate to that location.",
            "stop": "Stopping immediately. How else may I help?",
            "follow": "I will follow you. Please maintain a safe distance."
        }

        return responses.get(human_action, "I acknowledge your presence.")


class CapstonePhysicalAISystem:
    """Main Physical AI system for the capstone project"""

    def __init__(self):
        # Initialize all subsystems
        self.perception = PerceptionSystem()
        self.path_planner = PathPlanner()
        self.decision_maker = DecisionMakingSystem()
        self.control = ControlSystem()
        self.hri = HumanRobotInteraction()

        # System state
        self.system_state = TaskState.IDLE
        self.operational = True

        # Initialize common ROS node components
        self.rate = rospy.Rate(10)  # 10 Hz

        # Add sample tasks to the system
        self._initialize_sample_tasks()

        print("Capstone Physical AI System initialized and ready")

    def _initialize_sample_tasks(self):
        """Initialize sample tasks for the capstone project"""
        # Task 1: Office Assistant
        office_assistant_task = TaskDefinition(
            id="office_assistant_001",
            name="Office Assistant Task",
            description="Navigate to office, deliver document, return to base",
            priority=8,
            required_resources=["navigation", "manipulation"],
            estimated_duration=300.0,  # 5 minutes
            success_criteria=["document_delivered", "base_reached", "no_collisions"]
        )

        # Task 2: Environment Monitoring
        monitoring_task = TaskDefinition(
            id="monitoring_001",
            name="Environment Monitoring",
            description="Monitor environment for changes and report anomalies",
            priority=5,
            required_resources=["perception", "communication"],
            estimated_duration=1800.0,  # 30 minutes
            success_criteria=["environment_monitored", "anomalies_reported"]
        )

        # Add tasks to decision maker
        self.decision_maker.add_task(office_assistant_task)
        self.decision_maker.add_task(monitoring_task)

    def run(self):
        """Main execution loop"""
        print("Starting Capstone Physical AI System...")

        while not rospy.is_shutdown() and self.operational:
            try:
                # Get current environment state
                environment_map = self.perception.get_environment_map()

                # Check human safety
                safety_status = self.hri.check_human_safety(environment_map)

                if safety_status["recommended_action"] == "emergency_stop":
                    print("EMERGENCY: Safety violation detected, stopping robot")
                    self.control.enable_emergency_stop()
                    self.system_state = TaskState.EMERGENCY_STOP
                else:
                    # Resume normal operation if emergency was resolved
                    if self.system_state == TaskState.EMERGENCY_STOP:
                        self.control.disable_emergency_stop()
                        self.system_state = TaskState.IDLE

                    # Make decisions based on environment
                    current_task = self.decision_maker.make_decision(environment_map)

                    if current_task:
                        print(f"Executing task: {current_task.name}")
                        self.system_state = TaskState.EXECUTING

                        # For this framework, we'll just simulate task execution
                        self._execute_task(current_task, environment_map)

                        # Mark task as completed (for simulation)
                        self.decision_maker.update_task_status(current_task.id, TaskState.COMPLETED)
                        self.system_state = TaskState.IDLE
                    else:
                        # No tasks to execute, might want to do patrol or monitoring
                        self._idle_behavior()

                # Publish environment map
                self.perception.publish_environment_map()

                # Sleep to maintain loop rate
                self.rate.sleep()

            except Exception as e:
                print(f"Error in main loop: {e}")
                self.control.stop_robot()
                self.system_state = TaskState.FAILED
                rospy.sleep(1.0)  # Brief pause before continuing

    def _execute_task(self, task: TaskDefinition, environment_map: Dict[str, Any]):
        """Execute a specific task"""
        print(f"Executing task: {task.name}")

        # Task-specific execution logic would go here
        # For simulation, we'll just wait
        rospy.sleep(task.estimated_duration / 10.0)  # Simulate task execution

    def _idle_behavior(self):
        """Behavior when no tasks are active"""
        # In a real system, this might involve patrolling, charging, or monitoring
        pass

    def shutdown(self):
        """Clean shutdown of the system"""
        print("Shutting down Capstone Physical AI System...")
        self.control.stop_robot()
        self.operational = False


def main():
    """Main entry point"""
    rospy.init_node('capstone_physical_ai_system', anonymous=True)

    try:
        # Create and run the capstone system
        ai_system = CapstonePhysicalAISystem()

        print("Capstone Physical AI System starting...")
        print("Press Ctrl+C to stop the system")

        # Run the system
        ai_system.run()

    except rospy.ROSInterruptException:
        print("ROS Interrupt received, shutting down...")
    except KeyboardInterrupt:
        print("Keyboard interrupt received, shutting down...")
    finally:
        # Ensure clean shutdown
        if 'ai_system' in locals():
            ai_system.shutdown()


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Integrated Cognition System for Physical AI
This module implements the cognition component of the integrated Physical AI system
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from builtin_interfaces.msg import Time
import numpy as np
import threading
import time
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
import json


class IntegratedCognition(Node):
    """
    Integrated Cognition System for Physical AI
    Handles decision making, planning, reasoning, and goal management
    """

    def __init__(self):
        super().__init__('integrated_cognition')

        # QoS profile for reliable communication
        from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
        qos_profile = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        # Publishers
        self.decision_publisher = self.create_publisher(String, 'cognition/decision', qos_profile)
        self.plan_publisher = self.create_publisher(Path, 'cognition/plan', qos_profile)
        self.goal_publisher = self.create_publisher(PoseStamped, 'cognition/goal', qos_profile)
        self.cognition_status_publisher = self.create_publisher(String, 'cognition/status', qos_profile)

        # Subscribers
        self.perception_subscription = self.create_subscription(
            String, 'perception/status', self.perception_callback, qos_profile
        )
        self.task_subscription = self.create_subscription(
            String, 'tasks/command', self.task_callback, qos_profile
        )
        self.goal_subscription = self.create_subscription(
            PoseStamped, 'goal_pose', self.goal_callback, qos_profile
        )

        # System state
        self.perception_data = {}
        self.current_goals = []
        self.belief_state = {}
        self.current_plan = None
        self.current_task = 'idle'
        self.system_active = True

        # Cognition components
        self.reasoning_engine = ReasoningEngine()
        self.planner = PathPlanner()
        self.goal_manager = GoalManager()
        self.decision_maker = DecisionMaker()

        # Data buffers
        self.perception_buffer = deque(maxlen=10)
        self.task_buffer = deque(maxlen=5)

        # Threading for concurrent processing
        self.reasoning_thread = threading.Thread(target=self.reasoning_loop, daemon=True)
        self.reasoning_thread.start()

        self.planning_thread = threading.Thread(target=self.planning_loop, daemon=True)
        self.planning_thread.start()

        # Timer for cognition coordination
        self.cognition_timer = self.create_timer(0.1, self.cognition_coordination_callback)

        self.get_logger().info('Integrated Cognition System initialized')

    def perception_callback(self, msg):
        """Handle incoming perception data"""
        try:
            # Parse perception status message
            perception_parts = msg.data.split(', ')
            perception_dict = {}
            for part in perception_parts:
                if ':' in part:
                    key, value = part.split(': ', 1)
                    perception_dict[key.strip()] = value.strip()

            self.perception_data = perception_dict
            self.perception_buffer.append(perception_dict)
        except Exception as e:
            self.get_logger().error(f'Error parsing perception data: {e}')

    def task_callback(self, msg):
        """Handle incoming task commands"""
        self.current_task = msg.data
        self.task_buffer.append(msg.data)

    def goal_callback(self, msg):
        """Handle incoming goal poses"""
        goal = {
            'x': msg.pose.position.x,
            'y': msg.pose.position.y,
            'z': msg.pose.position.z,
            'qx': msg.pose.orientation.x,
            'qy': msg.pose.orientation.y,
            'qz': msg.pose.orientation.z,
            'qw': msg.pose.orientation.w
        }
        self.current_goals.append(goal)

    def reasoning_loop(self):
        """Reasoning processing loop"""
        while rclpy.ok() and self.system_active:
            # Perform reasoning based on perception and goals
            self.perform_reasoning()

            # Sleep to control processing rate
            time.sleep(0.1)  # 10 Hz

    def planning_loop(self):
        """Planning processing loop"""
        while rclpy.ok() and self.system_active:
            # Update plans based on current state
            self.update_plans()

            # Sleep to control processing rate
            time.sleep(0.2)  # 5 Hz

    def perform_reasoning(self):
        """Perform cognitive reasoning"""
        try:
            # Update belief state based on perception
            self.update_beliefs()

            # Perform situational reasoning
            situation_assessment = self.reasoning_engine.assess_situation(
                self.belief_state, self.perception_data
            )

            # Update belief state with assessment
            self.belief_state.update(situation_assessment)

            # Perform goal reasoning
            if self.current_goals:
                goal_assessment = self.reasoning_engine.assess_goals(
                    self.current_goals, self.belief_state
                )
                self.belief_state.update(goal_assessment)

        except Exception as e:
            self.get_logger().error(f'Error in reasoning: {e}')

    def update_beliefs(self):
        """Update belief state based on perception data"""
        # Update robot position if available in perception
        if 'robot_position' in self.belief_state:
            self.belief_state['robot_position'] = self.perception_data.get('position', self.belief_state.get('robot_position'))

        # Update object beliefs
        if 'objects' in self.perception_data:
            self.belief_state['detected_objects'] = self.perception_data['objects']

        # Update obstacle beliefs
        if 'obstacles' in self.perception_data:
            self.belief_state['obstacles'] = self.perception_data['obstacles']

        # Update environmental beliefs
        self.belief_state['environment_known'] = True
        self.belief_state['last_perception_update'] = time.time()

    def update_plans(self):
        """Update plans based on current state"""
        try:
            if self.current_goals and self.belief_state.get('environment_known', False):
                # Generate plan for current goal
                current_goal = self.current_goals[-1]  # Use latest goal
                plan = self.planner.generate_plan(
                    self.belief_state.get('robot_position', (0, 0, 0)),
                    current_goal,
                    self.belief_state.get('obstacles', [])
                )

                if plan:
                    self.current_plan = plan
                    self.publish_plan(plan)

        except Exception as e:
            self.get_logger().error(f'Error updating plans: {e}')

    def cognition_coordination_callback(self):
        """Cognition coordination callback"""
        # Make decisions based on current state
        decision = self.decision_maker.make_decision(
            self.belief_state, self.current_task
        )

        # Publish decision
        decision_msg = String()
        decision_msg.data = decision
        self.decision_publisher.publish(decision_msg)

        # Publish cognition status
        status_msg = String()
        status_msg.data = f"Goals: {len(self.current_goals)}, Beliefs: {len(self.belief_state)}, Decision: {decision}"
        self.cognition_status_publisher.publish(status_msg)

    def publish_plan(self, plan):
        """Publish the current plan"""
        if plan:
            path_msg = Path()
            path_msg.header.stamp = self.get_clock().now().to_msg()
            path_msg.header.frame_id = 'map'

            for point in plan:
                pose = PoseStamped()
                pose.header = path_msg.header
                pose.pose.position.x = point[0]
                pose.pose.position.y = point[1]
                pose.pose.position.z = 0.0
                path_msg.poses.append(pose)

            self.plan_publisher.publish(path_msg)

    def get_belief_state(self) -> Dict:
        """Get current belief state"""
        return self.belief_state.copy()

    def get_current_plan(self) -> Optional[List[Tuple[float, float]]]:
        """Get current plan"""
        return self.current_plan


class ReasoningEngine:
    """Cognitive reasoning engine"""

    def __init__(self):
        self.reasoning_methods = {
            'situational': self.situational_reasoning,
            'goal': self.goal_reasoning,
            'spatial': self.spatial_reasoning
        }

    def assess_situation(self, belief_state: Dict, perception_data: Dict) -> Dict:
        """Assess the current situation"""
        situation = {}

        # Assess safety
        obstacles = belief_state.get('obstacles', [])
        if obstacles:
            min_distance = min([obs['distance'] for obs in obstacles]) if obstacles else float('inf')
            situation['safety_level'] = 'dangerous' if min_distance < 0.5 else 'cautious' if min_distance < 1.0 else 'safe'
        else:
            situation['safety_level'] = 'safe'

        # Assess environment complexity
        objects = perception_data.get('Objects:', '0')
        try:
            num_objects = int(objects.split(':')[-1].strip()) if ':' in objects else int(objects)
            situation['environment_complexity'] = 'simple' if num_objects < 3 else 'moderate' if num_objects < 8 else 'complex'
        except:
            situation['environment_complexity'] = 'moderate'

        # Assess task feasibility
        situation['task_feasibility'] = self.assess_task_feasibility(belief_state)

        return situation

    def assess_goals(self, goals: List[Dict], belief_state: Dict) -> Dict:
        """Assess goals for achievability"""
        goal_assessment = {}

        if goals:
            current_goal = goals[-1]
            goal_assessment['current_goal'] = current_goal

            # Assess if goal is reachable
            robot_pos = belief_state.get('robot_position', (0, 0, 0))
            goal_pos = (current_goal['x'], current_goal['y'], current_goal['z'])

            distance = np.sqrt((goal_pos[0] - robot_pos[0])**2 +
                             (goal_pos[1] - robot_pos[1])**2)

            goal_assessment['goal_reachable'] = distance < 10.0  # Arbitrary threshold
            goal_assessment['distance_to_goal'] = distance

        return goal_assessment

    def assess_task_feasibility(self, belief_state: Dict) -> str:
        """Assess if current task is feasible"""
        safety_level = belief_state.get('safety_level', 'safe')
        environment_complexity = belief_state.get('environment_complexity', 'simple')

        if safety_level == 'dangerous':
            return 'not_feasible'
        elif safety_level == 'cautious' and environment_complexity == 'complex':
            return 'challenging'
        else:
            return 'feasible'

    def situational_reasoning(self, belief_state: Dict, perception_data: Dict) -> Dict:
        """Perform situational reasoning"""
        # This would perform more complex situational analysis
        return {}

    def goal_reasoning(self, goals: List[Dict], belief_state: Dict) -> Dict:
        """Perform goal-oriented reasoning"""
        # This would perform goal prioritization and conflict resolution
        return {}

    def spatial_reasoning(self, spatial_data: Dict) -> Dict:
        """Perform spatial reasoning"""
        # This would perform spatial relationship analysis
        return {}


class PathPlanner:
    """Path planning component"""

    def __init__(self):
        self.planning_algorithm = 'a_star'  # Options: a_star, dijkstra, rrt

    def generate_plan(self, start: Tuple[float, float, float], goal: Dict, obstacles: List[Dict]) -> Optional[List[Tuple[float, float]]]:
        """Generate a path from start to goal"""
        try:
            # Extract goal coordinates
            goal_pos = (goal['x'], goal['y'])

            # Extract start coordinates
            start_pos = (start[0], start[1])

            # Simple path planning (in a real system, this would use proper path planning)
            if self.planning_algorithm == 'a_star':
                plan = self.a_star_plan(start_pos, goal_pos, obstacles)
            elif self.planning_algorithm == 'dijkstra':
                plan = self.dijkstra_plan(start_pos, goal_pos, obstacles)
            else:
                plan = self.simple_plan(start_pos, goal_pos)

            return plan

        except Exception as e:
            print(f"Error in path planning: {e}")
            return None

    def simple_plan(self, start: Tuple[float, float], goal: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Generate a simple straight-line path"""
        # This is a very simplified path planning
        # In a real system, this would use proper path planning algorithms
        steps = 10
        plan = []

        dx = (goal[0] - start[0]) / steps
        dy = (goal[1] - start[1]) / steps

        for i in range(steps + 1):
            x = start[0] + i * dx
            y = start[1] + i * dy
            plan.append((x, y))

        return plan

    def a_star_plan(self, start: Tuple[float, float], goal: Tuple[float, float], obstacles: List[Dict]) -> List[Tuple[float, float]]:
        """A* path planning implementation"""
        # For this example, we'll use the simple plan
        # A full A* implementation would be much more complex
        return self.simple_plan(start, goal)

    def dijkstra_plan(self, start: Tuple[float, float], goal: Tuple[float, float], obstacles: List[Dict]) -> List[Tuple[float, float]]:
        """Dijkstra path planning implementation"""
        # For this example, we'll use the simple plan
        # A full Dijkstra implementation would be much more complex
        return self.simple_plan(start, goal)


class GoalManager:
    """Goal management component"""

    def __init__(self):
        self.active_goals = []
        self.completed_goals = []
        self.failed_goals = []

    def add_goal(self, goal: Dict):
        """Add a new goal"""
        self.active_goals.append(goal)

    def complete_goal(self, goal: Dict):
        """Mark a goal as completed"""
        if goal in self.active_goals:
            self.active_goals.remove(goal)
            self.completed_goals.append(goal)

    def fail_goal(self, goal: Dict):
        """Mark a goal as failed"""
        if goal in self.active_goals:
            self.active_goals.remove(goal)
            self.failed_goals.append(goal)

    def get_active_goals(self) -> List[Dict]:
        """Get active goals"""
        return self.active_goals.copy()


class DecisionMaker:
    """Decision making component"""

    def __init__(self):
        self.decision_rules = [
            self.safety_decision,
            self.task_priority_decision,
            self.resource_decision
        ]

    def make_decision(self, belief_state: Dict, current_task: str) -> str:
        """Make a decision based on belief state and current task"""
        # Apply decision rules in order
        for rule in self.decision_rules:
            decision = rule(belief_state, current_task)
            if decision:
                return decision

        # Default decision
        return current_task if current_task != 'idle' else 'wait'

    def safety_decision(self, belief_state: Dict, current_task: str) -> Optional[str]:
        """Safety-based decision making"""
        safety_level = belief_state.get('safety_level', 'safe')

        if safety_level == 'dangerous':
            return 'safety_stop'
        elif safety_level == 'cautious':
            return f'cautious_{current_task}'

        return None

    def task_priority_decision(self, belief_state: Dict, current_task: str) -> Optional[str]:
        """Task priority-based decision making"""
        goal_reachable = belief_state.get('goal_reachable', True)
        environment_complexity = belief_state.get('environment_complexity', 'simple')

        if not goal_reachable:
            return 'replan'
        elif environment_complexity == 'complex':
            return f'navigate_carefully'

        return None

    def resource_decision(self, belief_state: Dict, current_task: str) -> Optional[str]:
        """Resource-based decision making"""
        # This would check resource availability
        return None


def main(args=None):
    rclpy.init(args=args)

    integrated_cognition = IntegratedCognition()

    try:
        rclpy.spin(integrated_cognition)
    except KeyboardInterrupt:
        pass
    finally:
        integrated_cognition.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
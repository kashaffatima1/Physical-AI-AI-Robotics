import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from nav_msgs.msg import Path, OccupancyGrid
from std_msgs.msg import Header
import numpy as np
from typing import List, Tuple, Optional
import random


class RRTNode:
    """Node for RRT tree"""
    def __init__(self, x: float, y: float, parent=None):
        self.x = x
        self.y = y
        self.parent = parent

    def distance_to(self, other) -> float:
        """Calculate distance to another node"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


class RRTPlanner(Node):
    """
    RRT (Rapidly-exploring Random Tree) path planning algorithm implementation for Physical AI systems.
    Uses RRT to find path in 2D grid map.
    """

    def __init__(self):
        super().__init__('rrt_planner')

        # Create publisher for computed path
        self.path_publisher = self.create_publisher(Path, 'path_planner/path', 10)

        # Create subscriber for map
        self.map_subscription = self.create_subscription(
            OccupancyGrid,
            'map',
            self.map_callback,
            10
        )

        # Create subscriber for start/goal poses
        self.start_subscription = self.create_subscription(
            PoseStamped,
            'path_planner/start',
            self.start_callback,
            10
        )

        self.goal_subscription = self.create_subscription(
            PoseStamped,
            'path_planner/goal',
            self.goal_callback,
            10
        )

        # Initialize variables
        self.map_data = None
        self.map_width = 0
        self.map_height = 0
        self.map_resolution = 0.0
        self.map_origin_x = 0.0
        self.map_origin_y = 0.0

        self.start_pose = None
        self.goal_pose = None

        # RRT parameters
        self.max_iterations = 1000
        self.step_size = 0.3  # meters
        self.goal_bias = 0.1  # probability of sampling goal

        self.get_logger().info('RRT Planner initialized')

    def map_callback(self, msg):
        """Callback to receive map data"""
        self.map_data = np.array(msg.data).reshape((msg.info.height, msg.info.width))
        self.map_width = msg.info.width
        self.map_height = msg.info.height
        self.map_resolution = msg.info.resolution
        self.map_origin_x = msg.info.origin.position.x
        self.map_origin_y = msg.info.origin.position.y

        self.get_logger().info(f'Received map: {self.map_width}x{self.map_height}')

    def start_callback(self, msg):
        """Callback to receive start pose"""
        self.start_pose = (msg.pose.position.x, msg.pose.position.y)
        self.get_logger().info(f'Start pose received: {self.start_pose}')
        if self.goal_pose is not None:
            self.plan_path()

    def goal_callback(self, msg):
        """Callback to receive goal pose"""
        self.goal_pose = (msg.pose.position.x, msg.pose.position.y)
        self.get_logger().info(f'Goal pose received: {self.goal_pose}')
        if self.start_pose is not None:
            self.plan_path()

    def plan_path(self):
        """Plan path using RRT algorithm"""
        if self.map_data is None:
            self.get_logger().error('No map data available')
            return

        path = self.rrt(self.start_pose, self.goal_pose)

        if path:
            self.publish_path(path)
            self.get_logger().info(f'RRT path found with {len(path)} waypoints')
        else:
            self.get_logger().warn('RRT: No path found')

    def rrt(self, start: Tuple[float, float], goal: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """
        RRT path planning algorithm
        """
        # Convert start and goal to RRTNodes
        start_node = RRTNode(start[0], start[1])
        goal_node = RRTNode(goal[0], goal[1])

        # Initialize tree with start node
        tree = [start_node]

        for i in range(self.max_iterations):
            # Sample random point (with bias toward goal)
            if random.random() < self.goal_bias:
                sample = goal_node
            else:
                # Sample random point in map bounds
                sample = self.sample_random_point()

            # Find nearest node in tree
            nearest = self.find_nearest_node(tree, sample)

            # Create new node in direction of sample
            new_node = self.steer(nearest, sample)

            # Check if path to new node is collision-free
            if new_node and self.is_collision_free(nearest, new_node):
                new_node.parent = nearest
                tree.append(new_node)

                # Check if goal is reached
                if new_node.distance_to(goal_node) < self.step_size:
                    # Found path to goal, reconstruct path
                    return self.reconstruct_path(new_node, start_node)

        # Path not found
        return None

    def sample_random_point(self) -> RRTNode:
        """Sample a random point in the map bounds"""
        # Convert map bounds to world coordinates
        min_x = self.map_origin_x
        max_x = self.map_origin_x + self.map_width * self.map_resolution
        min_y = self.map_origin_y
        max_y = self.map_origin_y + self.map_height * self.map_resolution

        # Sample random point
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)

        return RRTNode(x, y)

    def find_nearest_node(self, tree: List[RRTNode], target: RRTNode) -> RRTNode:
        """Find the nearest node in the tree to the target"""
        nearest = tree[0]
        min_dist = nearest.distance_to(target)

        for node in tree[1:]:
            dist = node.distance_to(target)
            if dist < min_dist:
                min_dist = dist
                nearest = node

        return nearest

    def steer(self, from_node: RRTNode, to_node: RRTNode) -> Optional[RRTNode]:
        """Create a new node in the direction from from_node to to_node"""
        dist = from_node.distance_to(to_node)

        if dist < self.step_size:
            # If close enough, just return the target
            if self.is_valid_position(to_node.x, to_node.y):
                return RRTNode(to_node.x, to_node.y)
            else:
                return None
        else:
            # Move step_size in the direction of target
            theta = np.arctan2(to_node.y - from_node.y, to_node.x - from_node.x)
            new_x = from_node.x + self.step_size * np.cos(theta)
            new_y = from_node.y + self.step_size * np.sin(theta)

            if self.is_valid_position(new_x, new_y):
                return RRTNode(new_x, new_y)
            else:
                return None

    def is_collision_free(self, node1: RRTNode, node2: RRTNode) -> bool:
        """Check if the path between two nodes is collision-free"""
        # Sample points along the line between nodes
        dist = node1.distance_to(node2)
        steps = int(dist / (self.map_resolution / 2))  # Sample at high resolution

        for i in range(steps + 1):
            t = i / steps
            x = node1.x + t * (node2.x - node1.x)
            y = node1.y + t * (node2.y - node1.y)

            if not self.is_valid_position(x, y):
                return False

        return True

    def is_valid_position(self, x: float, y: float) -> bool:
        """Check if a world position is valid (not occupied)"""
        # Convert to grid coordinates
        grid_x = int((x - self.map_origin_x) / self.map_resolution)
        grid_y = int((y - self.map_origin_y) / self.map_resolution)

        # Check bounds
        if grid_x < 0 or grid_x >= self.map_width or grid_y < 0 or grid_y >= self.map_height:
            return False

        # Check if occupied
        cell_value = self.map_data[grid_y, grid_x]
        return cell_value < 50  # Free space

    def is_valid_cell(self, x: int, y: int) -> bool:
        """Check if a grid cell is valid (within bounds and not occupied)"""
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return False

        # Check if cell is occupied (value > 50 means occupied in OccupancyGrid)
        cell_value = self.map_data[y, x]
        return cell_value < 50  # Free space

    def reconstruct_path(self, goal_node: RRTNode, start_node: RRTNode) -> List[Tuple[float, float]]:
        """Reconstruct path from goal to start"""
        path = []
        current = goal_node

        while current is not None:
            path.append((current.x, current.y))
            current = current.parent

        path.reverse()
        return path

    def publish_path(self, waypoints: List[Tuple[float, float]]):
        """Publish the computed path"""
        path_msg = Path()
        path_msg.header = Header()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = 'map'

        for i, (x, y) in enumerate(waypoints):
            pose = PoseStamped()
            pose.header = Header()
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.header.frame_id = 'map'
            pose.pose.position.x = x
            pose.pose.position.y = y
            pose.pose.position.z = 0.0
            # Set orientation to face along the path (simple approximation)
            if i < len(waypoints) - 1:
                dx = waypoints[i+1][0] - x
                dy = waypoints[i+1][1] - y
                theta = np.arctan2(dy, dx)
                pose.pose.orientation.z = np.sin(theta/2)
                pose.pose.orientation.w = np.cos(theta/2)
            else:
                # Keep orientation of last segment
                if len(waypoints) > 1:
                    dx = x - waypoints[i-1][0]
                    dy = y - waypoints[i-1][1]
                    theta = np.arctan2(dy, dx)
                    pose.pose.orientation.z = np.sin(theta/2)
                    pose.pose.orientation.w = np.cos(theta/2)

            path_msg.poses.append(pose)

        self.path_publisher.publish(path_msg)


def main(args=None):
    rclpy.init(args=args)

    rrt_planner = RRTPlanner()

    try:
        rclpy.spin(rrt_planner)
    except KeyboardInterrupt:
        pass
    finally:
        rrt_planner.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
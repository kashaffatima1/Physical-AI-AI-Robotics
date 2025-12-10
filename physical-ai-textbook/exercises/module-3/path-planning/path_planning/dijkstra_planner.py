import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from nav_msgs.msg import Path, OccupancyGrid
from std_msgs.msg import Header
import heapq
import numpy as np
from typing import List, Tuple, Optional


class DijkstraPlanner(Node):
    """
    Dijkstra path planning algorithm implementation for Physical AI systems.
    Uses Dijkstra's algorithm to find shortest path in 2D grid map.
    """

    def __init__(self):
        super().__init__('dijkstra_planner')

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

        self.get_logger().info('Dijkstra Planner initialized')

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
        """Plan path using Dijkstra's algorithm"""
        if self.map_data is None:
            self.get_logger().error('No map data available')
            return

        # Convert world coordinates to grid coordinates
        start_grid = self.world_to_grid(self.start_pose)
        goal_grid = self.world_to_grid(self.goal_pose)

        if not self.is_valid_cell(start_grid[0], start_grid[1]) or \
           not self.is_valid_cell(goal_grid[0], goal_grid[1]):
            self.get_logger().error('Start or goal position is invalid')
            return

        # Run Dijkstra algorithm
        path = self.dijkstra(start_grid, goal_grid)

        if path:
            # Convert grid path to world coordinates
            world_path = [self.grid_to_world(cell) for cell in path]
            self.publish_path(world_path)
            self.get_logger().info(f'Path found with {len(path)} waypoints')
        else:
            self.get_logger().warn('No path found')

    def dijkstra(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Dijkstra's pathfinding algorithm
        """
        # Define movement directions (8-connected)
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        # Cost multipliers for diagonal movement
        move_costs = [
            1.414, 1.0, 1.414,  # Up-left, Up, Up-right
            1.0,          1.0,   # Left, Right
            1.414, 1.0, 1.414   # Down-left, Down, Down-right
        ]

        # Initialize priority queue
        open_set = [(0, start)]  # (cost, position)
        heapq.heapify(open_set)

        # Store costs from start
        costs = {start: 0}

        # Store came_from for path reconstruction
        came_from = {}

        while open_set:
            current_cost, current = heapq.heappop(open_set)

            # Check if we reached the goal
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path

            # Explore neighbors
            for i, direction in enumerate(directions):
                neighbor = (current[0] + direction[0], current[1] + direction[1])

                # Check if neighbor is valid
                if not self.is_valid_cell(neighbor[0], neighbor[1]):
                    continue

                # Calculate tentative cost
                tentative_cost = costs[current] + move_costs[i]

                # If this path to neighbor is better than any previous one
                if neighbor not in costs or tentative_cost < costs[neighbor]:
                    came_from[neighbor] = current
                    costs[neighbor] = tentative_cost

                    # Add to open set
                    heapq.heappush(open_set, (tentative_cost, neighbor))

        # No path found
        return None

    def is_valid_cell(self, x: int, y: int) -> bool:
        """Check if a grid cell is valid (within bounds and not occupied)"""
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return False

        # Check if cell is occupied (value > 50 means occupied in OccupancyGrid)
        cell_value = self.map_data[y, x]
        return cell_value < 50  # Free space

    def world_to_grid(self, world_pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates"""
        grid_x = int((world_pos[0] - self.map_origin_x) / self.map_resolution)
        grid_y = int((world_pos[1] - self.map_origin_y) / self.map_resolution)
        return (grid_x, grid_y)

    def grid_to_world(self, grid_pos: Tuple[int, int]) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates"""
        world_x = grid_pos[0] * self.map_resolution + self.map_origin_x
        world_y = grid_pos[1] * self.map_resolution + self.map_origin_y
        return (world_x, world_y)

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

    dijkstra_planner = DijkstraPlanner()

    try:
        rclpy.spin(dijkstra_planner)
    except KeyboardInterrupt:
        pass
    finally:
        dijkstra_planner.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
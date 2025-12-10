import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class JointCommandPublisher(Node):
    """
    A ROS 2 node that publishes joint commands for Physical AI systems.
    This simulates sending commands to robot joints in a Physical AI context.
    """

    def __init__(self):
        super().__init__('joint_command_publisher')
        self.publisher_ = self.create_publisher(String, 'joint_commands', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        # Simulate joint commands for a simple robot
        joint_commands = f"Joint positions: head_yaw={0.1 * self.i}, left_shoulder={0.2 * self.i}, right_elbow={0.15 * self.i}"
        msg = String()
        msg.data = joint_commands
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.i += 1


def main(args=None):
    rclpy.init(args=args)

    joint_command_publisher = JointCommandPublisher()

    rclpy.spin(joint_command_publisher)

    # Destroy the node explicitly
    joint_command_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class JointCommandSubscriber(Node):
    """
    A ROS 2 node that subscribes to joint commands for Physical AI systems.
    This simulates receiving and processing joint commands in a Physical AI context.
    """

    def __init__(self):
        super().__init__('joint_command_subscriber')
        self.subscription = self.create_subscription(
            String,
            'joint_commands',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(f'Received joint commands: "{msg.data}"')

        # Simulate processing the joint commands
        self.process_joint_commands(msg.data)

    def process_joint_commands(self, command_string):
        """
        Simulate processing joint commands in a Physical AI system.
        In a real system, this would interface with actuators or simulation.
        """
        self.get_logger().info(f'Processing command: {command_string}')

        # Extract joint values (simplified parsing)
        if 'head_yaw=' in command_string:
            self.get_logger().info('Head yaw command received - simulating head movement')

        if 'left_shoulder=' in command_string:
            self.get_logger().info('Left shoulder command received - simulating arm movement')

        if 'right_elbow=' in command_string:
            self.get_logger().info('Right elbow command received - simulating arm movement')


def main(args=None):
    rclpy.init(args=args)

    joint_command_subscriber = JointCommandSubscriber()

    rclpy.spin(joint_command_subscriber)

    # Destroy the node explicitly
    joint_command_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
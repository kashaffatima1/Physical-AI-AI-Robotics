import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch configuration
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_name = LaunchConfiguration('world', default='balance_control_world')

    # Get Gazebo package directory
    gazebo_ros_package_dir = get_package_share_directory('gazebo_ros')

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_package_dir, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': PathJoinSubstitution([
                FindPackageShare('balance_control_simulation'),
                'worlds',
                'balance_world.sdf'
            ]),
            'verbose': 'false',
            'gui': 'true'
        }.items()
    )

    # Spawn humanoid robot in Gazebo
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'humanoid_robot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.8'
        ],
        output='screen'
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )

    # Joint state publisher
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )

    # Balance controller node
    balance_controller = Node(
        package='balance_control',
        executable='balance_controller',
        name='balance_controller',
        parameters=[{
            'use_sim_time': use_sim_time,
            'kp': 100.0,  # Proportional gain for balance
            'ki': 1.0,    # Integral gain for balance
            'kd': 10.0    # Derivative gain for balance
        }]
    )

    # ZMP (Zero Moment Point) controller
    zmp_controller = Node(
        package='balance_control',
        executable='zmp_controller',
        name='zmp_controller',
        parameters=[{
            'use_sim_time': use_sim_time,
            'com_height': 0.8,
            'gravity': 9.81
        }]
    )

    # Create launch description
    ld = LaunchDescription()

    # Add the actions
    ld.add_action(DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    ))

    ld.add_action(DeclareLaunchArgument(
        'world',
        description='Choose one of the world files from `/balance_control_simulation/worlds`'
    ))

    ld.add_action(gazebo)
    ld.add_action(spawn_robot)
    ld.add_action(robot_state_publisher)
    ld.add_action(joint_state_publisher)
    ld.add_action(balance_controller)
    ld.add_action(zmp_controller)

    return ld
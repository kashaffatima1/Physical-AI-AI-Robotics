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
    world_name = LaunchConfiguration('world', default='object_detection_world')

    # Get Gazebo package directory
    gazebo_ros_package_dir = get_package_share_directory('gazebo_ros')

    # World file path
    world_path = PathJoinSubstitution([
        FindPackageShare('object_detection_simulation'),
        'worlds',
        'object_detection_world.sdf'
    ])

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_package_dir, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_path,
            'verbose': 'false',
            'gui': 'true'
        }.items()
    )

    # Spawn robot in Gazebo
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'physical_ai_robot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1'
        ],
        output='screen'
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': ''
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

    # Camera processing node
    camera_processor = Node(
        package='camera_integration',
        executable='camera_subscriber',
        name='camera_processor',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        remappings=[
            ('/camera/image_raw', '/physical_ai_robot/camera/image_raw')
        ]
    )

    # Object detection node
    object_detector = Node(
        package='camera_integration',
        executable='object_detector',
        name='object_detector',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        remappings=[
            ('/camera/image_raw', '/physical_ai_robot/camera/image_raw'),
            ('/camera/detections', '/physical_ai_robot/camera/detections')
        ]
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
        description='Choose one of the world files from `/object_detection_simulation/worlds`'
    ))

    ld.add_action(gazebo)
    ld.add_action(spawn_robot)
    ld.add_action(robot_state_publisher)
    ld.add_action(joint_state_publisher)
    ld.add_action(camera_processor)
    ld.add_action(object_detector)

    return ld
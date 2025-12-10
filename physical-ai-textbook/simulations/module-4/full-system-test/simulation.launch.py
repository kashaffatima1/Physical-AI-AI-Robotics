import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessStart
from launch.actions import LogInfo


def generate_launch_description():
    # Launch configuration
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_name = LaunchConfiguration('world', default='full_system_test_world')

    # Get Gazebo package directory
    gazebo_ros_package_dir = get_package_share_directory('gazebo_ros')

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_package_dir, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': PathJoinSubstitution([
                FindPackageShare('full_system_test_simulation'),
                'worlds',
                'full_system_world.sdf'
            ]),
            'verbose': 'false',
            'gui': 'true'
        }.items()
    )

    # Spawn Physical AI robot in Gazebo
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

    # Full Physical AI system nodes
    physical_ai_system = Node(
        package='full_system_integration',
        executable='physical_ai_system',
        name='physical_ai_system',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    integrated_perception = Node(
        package='full_system_integration',
        executable='integrated_perception',
        name='integrated_perception',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    integrated_cognition = Node(
        package='full_system_integration',
        executable='integrated_cognition',
        name='integrated_cognition',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    integrated_action = Node(
        package='full_system_integration',
        executable='integrated_action',
        name='integrated_action',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    # System coordinator (if exists)
    system_coordinator = Node(
        package='full_system_integration',
        executable='system_coordinator',
        name='system_coordinator',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    # Simulation testing nodes
    test_scenario_manager = Node(
        package='full_system_integration',
        executable='test_scenario_manager',
        name='test_scenario_manager',
        parameters=[{
            'use_sim_time': use_sim_time,
            'test_scenario': 'integration_test_1'
        }],
        output='screen'
    )

    performance_monitor = Node(
        package='full_system_integration',
        executable='performance_monitor',
        name='performance_monitor',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        output='screen'
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
        description='Choose one of the world files from `/full_system_test_simulation/worlds`'
    ))

    # Add Gazebo and robot spawning
    ld.add_action(gazebo)
    ld.add_action(spawn_robot)
    ld.add_action(robot_state_publisher)
    ld.add_action(joint_state_publisher)

    # Add the full Physical AI system
    ld.add_action(physical_ai_system)
    ld.add_action(integrated_perception)
    ld.add_action(integrated_cognition)
    ld.add_action(integrated_action)
    ld.add_action(system_coordinator)

    # Add testing components
    ld.add_action(test_scenario_manager)
    ld.add_action(performance_monitor)

    # Add logging for system startup
    ld.add_action(LogInfo(msg='Full System Integration Test Environment launched'))

    return ld
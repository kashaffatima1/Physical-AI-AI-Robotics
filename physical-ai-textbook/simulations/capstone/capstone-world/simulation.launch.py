#!/usr/bin/env python3
"""
Capstone Simulation Environment Launch File

This launch file sets up the complete simulation environment for the capstone project:
Autonomous Physical AI Assistant for Smart Environments.

The environment includes:
- A complex office world with multiple rooms
- Dynamic obstacles (humans moving around)
- Various objects for manipulation
- Sensor-equipped humanoid robot
- Complete ROS 2 simulation stack
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, RegisterEventHandler
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, TextSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    # Launch configuration
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_file = LaunchConfiguration('world', default='capstone_office.world')
    robot_name = LaunchConfiguration('robot_name', default='physical_ai_robot')

    # Package names
    pkg_gazebo_ros = FindPackageShare('gazebo_ros').find('gazebo_ros')
    pkg_capstone_sim = get_package_share_directory('capstone_simulation')
    pkg_robot_description = get_package_share_directory('physical_ai_robot_description')

    # World file path
    world_path = PathJoinSubstitution([pkg_capstone_sim, 'worlds', world_file])

    # Robot description (XACRO to URDF)
    robot_description_path = os.path.join(pkg_robot_description, 'urdf', 'humanoid_robot.xacro')
    robot_description_config = xacro.process_file(robot_description_path)
    robot_description = {'robot_description': robot_description_config.toxml()}

    # Launch Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_path,
            'verbose': 'true',
            'gui': 'true'
        }.items()
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': use_sim_time}]
    )

    # Spawn robot in Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', robot_name,
            '-x', '0.0', '-y', '0.0', '-z', '0.5',  # Start position
            '-R', '0.0', '-P', '0.0', '-Y', '0.0'   # Start orientation
        ],
        output='screen'
    )

    # Joint State Publisher (for simulation)
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[('/joint_states', 'joint_states')]
    )

    # Joint State Publisher GUI (optional, for debugging)
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        condition=IfCondition(LaunchConfiguration('gui', default='false')),
        remappings=[('/joint_states', 'joint_states')]
    )

    # RViz2 for visualization
    rviz_config_file = PathJoinSubstitution([pkg_capstone_sim, 'rviz', 'capstone_config.rviz'])
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(LaunchConfiguration('rviz', default='true'))
    )

    # Navigation stack
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time
        }.items(),
        condition=IfCondition(LaunchConfiguration('navigation', default='true'))
    )

    # SLAM toolbox (for mapping)
    slam_toolbox = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[os.path.join(pkg_capstone_sim, 'config', 'slam_params.yaml')],
        condition=IfCondition(LaunchConfiguration('slam', default='false'))
    )

    # Perception nodes
    object_detection = Node(
        package='capstone_perception',
        executable='object_detector',
        name='object_detector',
        parameters=[os.path.join(pkg_capstone_sim, 'config', 'perception_params.yaml')],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    human_detector = Node(
        package='capstone_perception',
        executable='human_detector',
        name='human_detector',
        parameters=[os.path.join(pkg_capstone_sim, 'config', 'perception_params.yaml')],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Control nodes
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[os.path.join(pkg_capstone_sim, 'config', 'controllers.yaml')],
        parameters=[robot_description],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    robot_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['robot_controller'],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Capstone main system
    capstone_system = Node(
        package='capstone_system',
        executable='main_capstone_system',
        name='capstone_physical_ai_system',
        parameters=[os.path.join(pkg_capstone_sim, 'config', 'capstone_params.yaml')],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    # Dynamic obstacles (humans) - simulated
    human_simulator = Node(
        package='capstone_simulation',
        executable='human_simulator',
        name='human_simulator',
        parameters=[os.path.join(pkg_capstone_sim, 'config', 'human_params.yaml')],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Environment monitor
    environment_monitor = Node(
        package='capstone_system',
        executable='environment_monitor',
        name='environment_monitor',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Task manager
    task_manager = Node(
        package='capstone_system',
        executable='task_manager',
        name='task_manager',
        parameters=[os.path.join(pkg_capstone_sim, 'config', 'task_params.yaml')],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Launch Description
    ld = LaunchDescription()

    # Declare launch arguments
    ld.add_action(DeclareLaunchArgument('use_sim_time', default_value='true',
                                       description='Use simulation (Gazebo) clock if true'))
    ld.add_action(DeclareLaunchArgument('world', default_value='capstone_office.world',
                                       description='Choose one of the world files from `/capstone_simulation/worlds`'))
    ld.add_action(DeclareLaunchArgument('robot_name', default_value='physical_ai_robot',
                                       description='Name of the robot'))
    ld.add_action(DeclareLaunchArgument('rviz', default_value='true',
                                       description='Open RViz2 if true'))
    ld.add_action(DeclareLaunchArgument('navigation', default_value='true',
                                       description='Launch navigation stack if true'))
    ld.add_action(DeclareLaunchArgument('slam', default_value='false',
                                       description='Launch SLAM if true'))
    ld.add_action(DeclareLaunchArgument('gui', default_value='false',
                                       description='Launch joint state publisher gui if true'))

    # Add all actions to launch description
    ld.add_action(gazebo)
    ld.add_action(robot_state_publisher)
    ld.add_action(spawn_entity)
    ld.add_action(joint_state_publisher)
    ld.add_action(joint_state_publisher_gui)
    ld.add_action(rviz)
    ld.add_action(navigation_launch)
    ld.add_action(slam_toolbox)
    ld.add_action(object_detection)
    ld.add_action(human_detector)
    ld.add_action(controller_manager)
    ld.add_action(joint_state_broadcaster)
    ld.add_action(robot_controller_spawner)
    ld.add_action(capstone_system)
    ld.add_action(human_simulator)
    ld.add_action(environment_monitor)
    ld.add_action(task_manager)

    return ld


# Additional configuration files that would be created alongside this launch file:

"""
# File: config/capstone_params.yaml
capstone_physical_ai_system:
  ros__parameters:
    # Perception parameters
    perception:
      obstacle_threshold: 1.0
      human_detection_range: 3.0
      object_detection_range: 2.0
      camera_matrix: [554.25, 0.0, 320.5, 0.0, 554.25, 240.5, 0.0, 0.0, 1.0]

    # Decision making parameters
    decision_making:
      emergency_distance: 0.5
      task_priority_scale: 10
      planning_frequency: 10.0  # Hz

    # Control parameters
      max_linear_velocity: 0.5
      max_angular_velocity: 0.5
      safety_margin: 0.3

    # HRI parameters
      personal_space_radius: 1.0
      social_space_radius: 2.0
      safety_space_radius: 0.5
"""

"""
# File: worlds/capstone_office.world
<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="capstone_office">
    <!-- Include the default outdoor environment -->
    <include>
      <uri>model://sun</uri>
    </include>

    <!-- Ground plane -->
    <include>
      <uri>model://ground_plane</uri>
    </include>

    <!-- Office building -->
    <model name="office_building">
      <static>true</static>
      <link name="building_link">
        <collision name="building_collision">
          <geometry>
            <box>
              <size>20 15 3</size>
            </box>
          </geometry>
        </collision>
        <visual name="building_visual">
          <geometry>
            <box>
              <size>20 15 3</size>
            </box>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
            <specular>0.1 0.1 0.1 1</specular>
          </material>
        </visual>
      </link>
    </model>

    <!-- Furniture -->
    <model name="desk_1">
      <pose>-5 2 0 0 0 0</pose>
      <link name="desk_link">
        <collision name="desk_collision">
          <geometry>
            <box>
              <size>1.5 0.8 0.75</size>
            </box>
          </geometry>
        </collision>
        <visual name="desk_visual">
          <geometry>
            <box>
              <size>1.5 0.8 0.75</size>
            </box>
          </geometry>
          <material>
            <ambient>0.6 0.4 0.2 1</ambient>
            <diffuse>0.6 0.4 0.2 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <model name="chair_1">
      <pose>-5.5 1.5 0 0 0 1.57</pose>
      <link name="chair_link">
        <collision name="chair_collision">
          <geometry>
            <box>
              <size>0.5 0.5 0.8</size>
            </box>
          </geometry>
        </collision>
        <visual name="chair_visual">
          <geometry>
            <box>
              <size>0.5 0.5 0.8</size>
            </box>
          </geometry>
          <material>
            <ambient>0.3 0.3 0.5 1</ambient>
            <diffuse>0.3 0.3 0.5 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Objects for manipulation -->
    <model name="document_stack">
      <pose>-4.5 2.2 0.75 0 0 0</pose>
      <link name="document_link">
        <collision name="document_collision">
          <geometry>
            <box>
              <size>0.2 0.25 0.1</size>
            </box>
          </geometry>
        </collision>
        <visual name="document_visual">
          <geometry>
            <box>
              <size>0.2 0.25 0.1</size>
            </box>
          </geometry>
          <material>
            <ambient>1 1 1 1</ambient>
            <diffuse>1 1 1 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <model name="coffee_cup">
      <pose>-4.8 1.8 0.75 0 0 0</pose>
      <link name="cup_link">
        <collision name="cup_collision">
          <geometry>
            <cylinder>
              <radius>0.04</radius>
              <length>0.1</length>
            </cylinder>
          </geometry>
        </collision>
        <visual name="cup_visual">
          <geometry>
            <cylinder>
              <radius>0.04</radius>
              <length>0.1</length>
            </cylinder>
          </geometry>
          <material>
            <ambient>0.8 0.6 0.2 1</ambient>
            <diffuse>0.8 0.6 0.2 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Rooms and areas -->
    <model name="reception_desk">
      <pose>6 0 0 0 0 0</pose>
      <link name="reception_link">
        <collision name="reception_collision">
          <geometry>
            <box>
              <size>2 1 0.8</size>
            </box>
          </geometry>
        </collision>
        <visual name="reception_visual">
          <geometry>
            <box>
              <size>2 1 0.8</size>
            </box>
          </geometry>
          <material>
            <ambient>0.5 0.5 0.5 1</ambient>
            <diffuse>0.5 0.5 0.5 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Conference room -->
    <model name="conference_table">
      <pose>2 -4 0 0 0 0</pose>
      <link name="table_link">
        <collision name="table_collision">
          <geometry>
            <box>
              <size>2 1 0.75</size>
            </box>
          </geometry>
        </collision>
        <visual name="table_visual">
          <geometry>
            <box>
              <size>2 1 0.75</size>
            </box>
          </geometry>
          <material>
            <ambient>0.4 0.2 0.1 1</ambient>
            <diffuse>0.4 0.2 0.1 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Add lighting -->
    <light name="office_light_1" type="point">
      <pose>0 0 2.5 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <attenuation>
        <range>10</range>
        <constant>0.5</constant>
        <linear>0.1</linear>
        <quadratic>0.05</quadratic>
      </attenuation>
    </light>
  </world>
</sdf>
"""

"""
# File: rviz/capstone_config.rviz
Panels:
  - Class: rviz_common/Displays
    Name: Displays
  - Class: rviz_common/Views
    Name: Views
Visualization Manager:
  Displays:
    - Class: rviz_default_plugins/Grid
      Name: Grid
      Enabled: true
    - Class: rviz_default_plugins/RobotModel
      Name: RobotModel
      Enabled: true
      Topic: /robot_description
    - Class: rviz_default_plugins/TF
      Name: TF
      Enabled: true
    - Class: rviz_default_plugins/MarkerArray
      Name: Obstacles
      Topic: /visualization_marker_array
    - Class: rviz_default_plugins/Camera
      Name: Camera
      Topic: /camera/rgb/image_raw
    - Class: rviz_default_plugins/Map
      Name: Map
      Topic: /map
  Global Options:
    Fixed Frame: map
    Frame Rate: 30
"""
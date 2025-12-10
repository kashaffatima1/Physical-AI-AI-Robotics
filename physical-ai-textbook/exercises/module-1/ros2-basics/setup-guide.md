# ROS 2 Setup Guide for Physical AI

## Introduction

This guide will help you set up ROS 2 (Robot Operating System 2) for Physical AI applications. ROS 2 is a flexible framework for writing robot software that provides services designed for a heterogeneous computer cluster, including hardware abstraction, device drivers, libraries, visualizers, message-passing, package management, and more.

## Prerequisites

Before installing ROS 2, ensure your system meets the following requirements:

- Ubuntu 22.04 (Jammy Jellyfish) or Windows 10/11
- At least 5GB of free disk space
- Python 3.8 or higher
- Internet connection for package installation

## Installing ROS 2 (Humble Hawksbill)

### On Ubuntu

1. **Set locale to support UTF-8:**
```bash
locale  # check for UTF-8
sudo apt update && sudo apt install locales
sudo locale-gen en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

2. **Add ROS 2 apt repository:**
```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl gnupg lsb-release
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

3. **Install ROS 2 packages:**
```bash
sudo apt update
sudo apt install ros-humble-desktop
```

4. **Install colcon build tools:**
```bash
sudo apt install python3-colcon-common-extensions
```

5. **Install additional dependencies:**
```bash
sudo apt install python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool build-essential
sudo rosdep init
rosdep update
```

### On Windows

1. **Install Chocolatey package manager**
2. **Install Python 3.8 or higher**
3. **Install Visual Studio Build Tools**
4. **Install ROS 2 using the Windows installer**

## Setting up your ROS 2 workspace

### Create a workspace directory:
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
```

### Source the ROS 2 installation:
```bash
source /opt/ros/humble/setup.bash
```

### Create a package for Physical AI examples:
```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python physical_ai_examples
```

## Basic ROS 2 Concepts

### Nodes
A node is an executable that uses ROS 2 to communicate with other nodes. You can group multiple nodes in a single package.

### Topics and Messages
Topics are named buses over which nodes exchange messages. Messages are the data exchanged between nodes.

### Services
Services provide a request/response communication pattern between nodes.

### Actions
Actions are like services but designed for long-running tasks with feedback.

## Basic Node Example

Let's create a simple publisher and subscriber:

1. **Navigate to your package:**
```bash
cd ~/ros2_ws/src/physical_ai_examples
```

2. **Create the publisher script:**
```bash
touch physical_ai_examples/talker.py
chmod +x physical_ai_examples/talker.py
```

3. **Create the subscriber script:**
```bash
touch physical_ai_examples/listener.py
chmod +x physical_ai_examples/listener.py
```

4. **Set up the package:**
```bash
touch setup.py
touch setup.cfg
```

## Environment Setup

### Add ROS 2 to your bash profile:
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

### Reload your environment:
```bash
source ~/.bashrc
```

## Building your workspace

```bash
cd ~/ros2_ws
colcon build --packages-select physical_ai_examples
source install/setup.bash
```

## Running Your First Example

After creating the node examples (covered in the next section), you can run them:

```bash
# Terminal 1 - Run the publisher
ros2 run physical_ai_examples talker

# Terminal 2 - Run the subscriber
ros2 run physical_ai_examples listener
```

## Simulation Setup (Gazebo)

For Physical AI applications, we'll use Gazebo for simulation:

```bash
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control
```

## Troubleshooting

### Common Issues:

1. **Package not found**: Make sure you've sourced the setup.bash file
2. **Permission denied**: Check file permissions and ensure executables are marked as such
3. **Network issues**: ROS 2 uses DDS for communication; firewall settings may need adjustment

### Useful Commands:

```bash
# List available topics
ros2 topic list

# Echo messages from a topic
ros2 topic echo <topic_name> <message_type>

# List available services
ros2 service list

# Get information about a node
ros2 node info <node_name>
```

## Next Steps

With ROS 2 installed and configured, you're ready to create your first Physical AI nodes. The next section covers creating basic publisher and subscriber nodes for Physical AI applications.
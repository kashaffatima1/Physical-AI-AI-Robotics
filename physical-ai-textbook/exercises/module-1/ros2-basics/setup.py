from setuptools import setup

package_name = 'physical_ai_examples'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Physical AI Team',
    maintainer_email='physical-ai@example.com',
    description='Examples for Physical AI with ROS 2',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'joint_command_publisher = physical_ai_examples.joint_command_publisher:main',
            'joint_command_subscriber = physical_ai_examples.joint_command_subscriber:main',
        ],
    },
)
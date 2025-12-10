from setuptools import setup

package_name = 'path_planning'

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
    description='Path planning algorithms for Physical AI',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'a_star_planner = path_planning.a_star_planner:main',
            'dijkstra_planner = path_planning.dijkstra_planner:main',
            'rrt_planner = path_planning.rrt_planner:main',
            'path_follower = path_planning.path_follower:main',
            'grid_map_publisher = path_planning.grid_map_publisher:main',
        ],
    },
)
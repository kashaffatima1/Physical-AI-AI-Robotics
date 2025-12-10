from setuptools import setup

package_name = 'camera_integration'

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
    description='Camera integration examples for Physical AI',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_publisher = camera_integration.camera_publisher:main',
            'camera_subscriber = camera_integration.camera_subscriber:main',
            'object_detector = camera_integration.object_detector:main',
            'camera_fusion = camera_integration.camera_fusion:main',
        ],
    },
)
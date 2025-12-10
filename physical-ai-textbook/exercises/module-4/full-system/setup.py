from setuptools import setup

package_name = 'full_system_integration'

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
    description='Full Physical AI system integration',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'physical_ai_system = full_system_integration.physical_ai_system:main',
            'integrated_perception = full_system_integration.integrated_perception:main',
            'integrated_cognition = full_system_integration.integrated_cognition:main',
            'integrated_action = full_system_integration.integrated_action:main',
            'system_coordinator = full_system_integration.system_coordinator:main',
        ],
    },
)
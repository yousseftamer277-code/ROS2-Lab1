from setuptools import setup
from glob import glob
package_name = 'turtle_control'
setup(
    name=package_name, version='0.0.1', packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'], zip_safe=True,
    maintainer='Student Team', maintainer_email='student@example.com',
    description='ROS 2 turtlesim lab servers', license='Apache-2.0',
    entry_points={'console_scripts': [
        'go_to_pose = turtle_control.go_to_pose:main',
        'reset_server = turtle_control.reset_server:main',
        'square_server = turtle_control.square_server:main',
    ]},
)

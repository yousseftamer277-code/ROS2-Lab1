from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('linear_speed', default_value='2.0'),
        DeclareLaunchArgument('angular_speed', default_value='2.0'),
        Node(package='turtlesim', executable='turtlesim_node', name='turtlesim'),
        Node(package='turtle_control', executable='go_to_pose', name='go_to_pose_server',
             parameters=[{
                 'max_linear_speed': ParameterValue(LaunchConfiguration('linear_speed'), value_type=float),
                 'max_angular_speed': ParameterValue(LaunchConfiguration('angular_speed'), value_type=float),
             }]),
        Node(package='turtle_control', executable='reset_server', name='reset_server'),
        Node(package='turtle_control', executable='square_server', name='square_server'),
    ])

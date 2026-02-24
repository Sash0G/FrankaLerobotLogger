#Currently we dont use launch, because it hijacks the input and the loger, doesnt run


import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('franka_loger')
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value='logger_params.yaml',
        description='Name of the YAML config file in the config folder'
    )
    config_path = [
        os.path.join(pkg_share, 'config', ''), 
        LaunchConfiguration('config_file')
    ]
    return LaunchDescription([
        config_file_arg,
        Node(
            package='franka_loger',
            executable='franka_loger',
            name='franka_loger',
            parameters=[config_path],
            output='screen'
        )
    ])
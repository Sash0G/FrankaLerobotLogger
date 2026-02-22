import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description(): #this code is gemini, but it looks fine
    # 1. Define where the 'config' folder is
    pkg_share = get_package_share_directory('franka_loger')
    
    # 2. Declare a launch argument called 'config_file'
    # Default value points to your standard logger_params.yaml
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value='logger_params.yaml',
        description='Name of the YAML config file in the config folder'
    )

    # 3. Create a path that joins the share directory with the user's input
    # LaunchConfiguration('config_file') grabs the string you type in the terminal
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
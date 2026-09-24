from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
            output='screen'
        ),

        Node(
            package='g03_prii3_turtlesim',
            executable='draw_three',
            name='g03_turtle_controller',
            output='screen'
        ),

    ])
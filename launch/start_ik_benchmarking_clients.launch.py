import os
import sys
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory
from copy import deepcopy


def generate_launch_description():

    # Declare launch arguments
    move_group_arg = DeclareLaunchArgument(
        "move_group", default_value="iiwa_arm", description="Move group name required for run_ik_benchmarks node"
    )

    moveit_config_pkg_arg = DeclareLaunchArgument(
        'moveit_config_pkg', default_value="iiwa_moveit_config", description="Moveit config package to load robot description"
    )

    kinematics_file_arg = DeclareLaunchArgument(
        "kinematics_file", default_value="kinematics.yaml", description="Provides information about the inverse kinematics (IK) solver to use"
    )

    sample_size_arg = DeclareLaunchArgument(
        "sample_size", default_value="10000", description="Sets how many times the IK solution process is repeated for evaluation"
    )

    # Get parameters from launch arguments
    move_group = LaunchConfiguration("move_group")
    sample_size = LaunchConfiguration("sample_size")

    # Extract the robot name if the moveit_config_pkg arg is provided
    # It is usually in the form of <robot_name>_moveit_config
    # Default values are as follows
    robot_name = "iiwa"
    moveit_config_pkg_name = "iiwa_moveit_config"
    kinematics_file_name = "kinematics.yaml"

    for arg in sys.argv:
        if arg.startswith("moveit_config_pkg:="):
            moveit_config_pkg_name = arg.split(":=")[1]
            robot_name = moveit_config_pkg_name.split("_")[0]
        elif arg.startswith("kinematics_file:="):
            kinematics_file_name = arg.split(":=")[1]

    # Build moveit_config using the robot name and kinematic file
    moveit_config = (MoveItConfigsBuilder(robot_name)
                     .robot_description_kinematics(
        file_path=os.path.join(
            get_package_share_directory(moveit_config_pkg_name),
            "config",
            kinematics_file_name,
        )
    )
        .to_moveit_configs()
    )

    # moveit_config_1 = deepcopy(moveit_config)
    # moveit_config_2 = deepcopy(moveit_config)
    # moveit_config_3 = deepcopy(moveit_config)

    # if 'robot_description_kinematics' in moveit_config_1.robot_description_kinematics:
    #     moveit_config_1.robot_description_kinematics['robot_description_kinematics_1'] = moveit_config_1.robot_description_kinematics['robot_description_kinematics']
    #     del moveit_config_1.robot_description_kinematics['robot_description_kinematics']

    # if 'robot_description_kinematics' in moveit_config_2.robot_description_kinematics:
    #     moveit_config_2.robot_description_kinematics['robot_description_kinematics_2'] = moveit_config_2.robot_description_kinematics['robot_description_kinematics']
    #     del moveit_config_2.robot_description_kinematics['robot_description_kinematics']

    # if 'robot_description_kinematics' in moveit_config_3.robot_description_kinematics:
    #     moveit_config_3.robot_description_kinematics['robot_description_kinematics_3'] = moveit_config_3.robot_description_kinematics['robot_description_kinematics']
    #     del moveit_config_3.robot_description_kinematics['robot_description_kinematics']

    # Start benchmarking client(s) node with required robot description and move_group parameters
    benchmarking_clients_node = Node(
        package="ik_benchmarking",
        executable="ik_benchmarking_client",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            # moveit_config_1.robot_description_kinematics,
            # moveit_config_2.robot_description_kinematics,
            # moveit_config_3.robot_description_kinematics,
            {"move_group": move_group, "sample_size": sample_size},
        ],
    )

    return LaunchDescription([move_group_arg, moveit_config_pkg_arg, kinematics_file_arg, sample_size_arg, benchmarking_clients_node])

# Make a script:

# source ./install_setup.bash

# ros2 launch ik_benchmarking benchmark.launch.py ik_params:=file_1.yaml

# ros2 launch ik_benchmarking benchmark.launch.py ik_params:=file_2.yaml
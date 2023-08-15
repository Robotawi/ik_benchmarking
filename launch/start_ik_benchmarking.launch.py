import os
import sys
import yaml
from launch import LaunchDescription
from launch.actions import TimerAction
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory

import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration

# Temporary solution


def get_cmdline_argument(arg_name):
    for arg in sys.argv:
        if arg.startswith(arg_name + ":="):
            return arg.split(":=")[1]
    return '0'

# Use Opaque function
# Check: https://answers.ros.org/question/340705/access-launch-argument-in-launchfile-ros2/

# def get_argument(context, *args, **kwargs):
#     # Access the argument from context
#     # arg_value = LaunchConfiguration('ik_solver_number').perform(context)
#     arg_value = context.launch_configurations['my_arg']
#     print(f"The value of 'my_arg' is: {arg_value}")


def load_benchmarking_config(ik_benchmarking_pkg, ik_benchmarking_config):
    # Construct the configuration file path
    file_path = os.path.join(get_package_share_directory(ik_benchmarking_pkg),
                             "config",
                             ik_benchmarking_config
                             )
    # Open file and parse content
    with open(file_path, "r") as config_file:
        config_data = yaml.safe_load(config_file)

    # Extract content and handle missing keys
    def get_config_data(key, parent_data=None):
        source_data = parent_data if parent_data else config_data
        value = source_data.get(key)
        if value is None:
            raise ValueError(f"Missing required configuration key {key}")
        return value

    moveit_config_pkg = get_config_data('moveit_config_pkg')
    move_group = get_config_data('move_group')
    sample_size = get_config_data('sample_size')

    # Extract IK solvers details
    # Assume three solvers are given (for simplicity)
    ik_solvers_data = get_config_data('ik_solvers')
    ik_solver_1_data = get_config_data('ik_solver_1', ik_solvers_data)
    ik_solver_2_data = get_config_data('ik_solver_2', ik_solvers_data)
    ik_solver_3_data = get_config_data('ik_solver_3', ik_solvers_data)

    ik_solver_1 = ik_solver_1_data.get('name')
    ik_solver_2 = ik_solver_2_data.get('name')
    ik_solver_3 = ik_solver_3_data.get('name')

    ik_solver_1_kinematics_file = ik_solver_1_data.get('kinematics_file')
    ik_solver_2_kinematics_file = ik_solver_2_data.get('kinematics_file')
    ik_solver_3_kinematics_file = ik_solver_3_data.get('kinematics_file')

    # Return a dictionary to avoid errors due to return order
    return {
        'moveit_config_pkg': moveit_config_pkg,
        'move_group': move_group,
        'sample_size': sample_size,
        'ik_solver_1': ik_solver_1,
        'ik_solver_2': ik_solver_2,
        'ik_solver_3': ik_solver_3,
        'ik_solver_1_kinematics_file': ik_solver_1_kinematics_file,
        'ik_solver_2_kinematics_file': ik_solver_2_kinematics_file,
        'ik_solver_3_kinematics_file': ik_solver_3_kinematics_file
    }


def get_robot_name(moveit_config_pkg):
    parts = moveit_config_pkg.split("_")

    if len(parts) < 2:
        print(
            "Error: The package name {moveit_config_pkg} is not standard. Please use 'robot_moveit_config' or 'moveit_resources_robot_moveit_config'.")
        exit(1)

    package_name_prefix = '_'.join(parts[:2])

    if package_name_prefix == "moveit_resources":
        robot_name = '_'.join(parts[:3])
    else:
        robot_name = parts[0]

    return robot_name


def generate_launch_description():
    # Declar launch argument to decide which solver to use
    ik_solver_arg = DeclareLaunchArgument(
        "ik_solver_number", default_value="0", description="IK solver number corresponding to the ik_benchmarking.yaml config file. Use values of 1, 2, and 3.")

    # Get parameter from launch argument
    # ik_solver_number_value = get_argument()
    ik_solver_value = get_cmdline_argument("ik_solver_number")

    ik_benchmarking_pkg = "ik_benchmarking"
    ik_benchmarking_config = "ik_benchmarking.yaml"
    benchmarking_config = load_benchmarking_config(
        ik_benchmarking_pkg, ik_benchmarking_config)

    robot_name = get_robot_name(benchmarking_config['moveit_config_pkg'])

    # Check ik_solver value and decide kinematics_file to use
    kinematics_file_key = ''
    ik_solver_key = ''
    if (ik_solver_value > '0'):
        ik_solver_key = 'ik_solver_'+ik_solver_value
        kinematics_file_key = 'ik_solver_'+ik_solver_value+'_kinematics_file'

    # Build moveit_config using the robot name and kinematic file
    moveit_config = (MoveItConfigsBuilder(robot_name)
                     .robot_description_kinematics(
        file_path=os.path.join(
            get_package_share_directory(
                benchmarking_config['moveit_config_pkg']),
            "config",
            benchmarking_config[kinematics_file_key],
        )
    )
        .to_moveit_configs()
    )

    # Start benchmarking server node with required robot description and move_group parameters
    benchmarking_server_node = Node(
        package="ik_benchmarking",
        executable="ik_benchmarking_server",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            {
                "move_group": benchmarking_config['move_group'],
                "sample_size": benchmarking_config['sample_size']
            },
        ],
    )

    print(
        f'\n Running calculations for IK Solver: {benchmarking_config[ik_solver_key]} \n',)

    # Start benchmarking client node with the same parameters as the server, but with delay
    benchmarking_client_node = Node(
        package="ik_benchmarking",
        executable="ik_benchmarking_client",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            {
                "move_group": benchmarking_config['move_group'],
                "sample_size": benchmarking_config['sample_size'],
                "ik_solver": benchmarking_config[ik_solver_key]
            },
        ],
    )

    # Delay the client node launch for two seconds till the server is fully started
    delayed_benchmarking_client_node = TimerAction(
        period=2.0, actions=[benchmarking_client_node])

    return LaunchDescription([benchmarking_server_node, delayed_benchmarking_client_node, ik_solver_arg])

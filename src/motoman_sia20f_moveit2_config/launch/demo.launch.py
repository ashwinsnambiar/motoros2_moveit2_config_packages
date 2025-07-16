import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder
import xacro


def generate_launch_description():
      db_arg = DeclareLaunchArgument("warehouse_host", default_value="", description="Database connection path")

      robot_description_file_path = os.path.join(
        get_package_share_directory("motoman_sia20f_moveit2_config"), "config", "motoman_sia20d.urdf.xacro"
      )

      robot_description_semantic_file_path = os.path.join(
        get_package_share_directory("motoman_sia20f_moveit2_config"), "config", "motoman_sia20d.srdf"
      )

      trajectory_execution_file_path = os.path.join(
        get_package_share_directory("motoman_sia20f_moveit2_config"), "config", "moveit_controllers.yaml"
      )

      rviz_config_file_path = os.path.join(
        get_package_share_directory("motoman_sia20f_moveit2_config"), "config", "moveit.rviz"
      )

      robot_description_contents = xacro.process_file(robot_description_file_path).toxml()

      warehouse_ros_config = {
            "warehouse_plugin": "warehouse_ros_sqlite::DatabaseConnection",
            "warehouse_host": LaunchConfiguration("warehouse_host")
      }

      moveit_config = (
            MoveItConfigsBuilder("motoman_sia20d", 
			      package_name="motoman_sia20f_moveit2_config",)
        	  .robot_description(file_path=robot_description_file_path)
        	  .robot_description_semantic(file_path=robot_description_semantic_file_path)
    		    .trajectory_execution(file_path=trajectory_execution_file_path)
    		    .to_moveit_configs()
	  )
    

	  # Start the actual move_group node/action server
      robot_namespace = "virero"

      move_group_node = Node(
        
            package="moveit_ros_move_group",
            executable="move_group",
            output="screen",
            # namespace=robot_namespace,
            parameters=[moveit_config.to_dict(), warehouse_ros_config],
            arguments=["--ros-args", "--log-level", "info"],
	  )


      rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        # namespace=robot_namespace,
        arguments=["-d", rviz_config_file_path],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            warehouse_ros_config,
        ],
      )

      robot_state_publisher_node = Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="both",
            # namespace=robot_namespace,
            parameters=[{'robot_description':robot_description_contents}]
            )

      # Load controllers
      # TODO: This was an additional item I added from a github dicussion. I am not sure if it is necessary
      load_controllers = []
      for controller in [
          "follow_joint_trajectory",
      ]:
          load_controllers += [
              ExecuteProcess(
                  cmd=["ros2 run controller_manager spawner {}".format(controller)],
                  shell=True,
                  output="screen",
              )
          ]


      return LaunchDescription(
        [
          db_arg,
          move_group_node, 
          rviz_node, 
          robot_state_publisher_node,
        ]
      )
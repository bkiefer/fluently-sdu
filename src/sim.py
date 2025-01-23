import omni
from omni.isaac.kit import SimulationApp
simulation_app = SimulationApp({"headless": False, "window_width": 2000, "window_height":1500})
from gubokit import utilities, isaac_sim, ros
import rclpy
from rclpy.node import Node
from custom_interfaces.srv import String
import os
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core import World
import omni.isaac.core.utils.numpy.rotations as rot_utils
import numpy as np
from pathlib import Path
import time
import select
import sys

class MEM(Node):
    """This is just a basic node that opens a scene and setup the environment, copy and paste this for future projects
    not usable as a class in other prjects
    Use this to start isaac sim
    """
    def __init__(self):
        # 
        super().__init__("basic_setup")
        omni.usd.get_context().open_stage(str(Path(__file__).parent.parent) + "/props/scene.usd")
        self.logger = utilities.CustomLogger("Basic_setup", str(Path(__file__).parent.parent) + "/logs/basic_setup.log", overwrite=True)
        self.logger.info("="*10 + "Starting simulation" + "="*10)

        self.setup_world()
        
        self.basic_ros_service_srv = self.create_service(String, 'basic_ros_service', self.basic_ros_service)

        self.world.reset()
        self.setup_task()
    
    # ---------------- ISAAC ---------------- #
    def setup_world(self):
        """
        setup the world initializing all the needed objects
        """
        self.timeline = omni.timeline.get_timeline_interface()
        self.world = World(stage_units_in_meters=1.0)
        self.stage = omni.usd.get_context().get_stage()
        # self.world.get_physics_context().enable_gpu_dynamics(True)
        self.robot = isaac_sim.SimRobot("/World/ur5e", str(Path(__file__).parent.parent) + "/urdf/ur5e.urdf", tcp_frame_urdf="tool0")
        self.cover = isaac_sim.SimulationObject("/World/battery_pack/case_top")
        self.world.scene.add(self.robot)
        self.world.scene.add(self.cover)
        self.target_pose = self.world.scene.add(XFormPrim(prim_path="/World/target", name="target", position=[0,0,1], orientation=rot_utils.euler_angles_to_quats([0, np.pi, 0])))
        self.robot.subscribe_to_topic('joint_states') # use a JointPublisher to send joint configuration to the robot
        pose_sub = isaac_sim.PoseArraySubscriber('poses', world=self.world, ros_node=self, prim_path="/World/ros_poses/pose")
    
    def setup_task(self):
        pass

            
    def manage_input(self):
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            cmd = sys.stdin.read(1)
            os.system('clear')
            if cmd == 'j':
                print(self.robot.get_joint_positions())
                print(self.robot.get_tcp_pose())

    # ----------------- ROS ----------------- #
    def basic_ros_service(self, request, response):
        self.logger.info("Check dimension service requested")
        response.ans = "success"
        return response

    # ----------- MAIN SIMULATION ----------- #
    def run_simulation(self):
        self.timeline.play()
        while simulation_app.is_running():
            rclpy.spin_once(self, timeout_sec=0.0)
            if self.world.is_playing():
                if self.world.current_time_step_index == 100:
                    pass
                if self.world.current_time_step_index > 100:
                    self.robot.follow_frame(self.target_pose)
                    self.manage_input()
                self.robot.physisc_step()
                self.world.step(render=True)
        self.timeline.stop()
        self.destroy_node()
        simulation_app.close()

def main():
    rclpy.init()
    demo = MEM()
    demo.run_simulation()

if __name__ == "__main__":
    main()
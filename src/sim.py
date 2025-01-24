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
from omni.physx.scripts import utils

import time
import select
import spatialmath as sm
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
        # omni.usd.get_context().open_stage(os.environ['FLUENTLY_WS_PATH'] + "/props/scene_prima_additiva.usd")

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
        tool0_T_cup = sm.SE3([0, 0, 0.02])
        self.robot = isaac_sim.SimRobot("/World/ur5e", str(Path(__file__).parent.parent) + "/urdf/ur5e.urdf", tcp_frame_urdf="tool0", tcp_frame_transf=tool0_T_cup)
        self.objects = {}
        self.objects['top_cover'] = isaac_sim.SimulationObject("/World/battery_pack/case_top",      name="top_cover")
        self.objects['bot_cover'] = isaac_sim.SimulationObject("/World/battery_pack/case_bot",      name="bot_cover")
        self.objects['top_spacers'] = isaac_sim.SimulationObject("/World/battery_pack/spacers_bot", name="top_spacers")
        self.objects['bot_spacers'] = isaac_sim.SimulationObject("/World/battery_pack/spacers_top", name="bot_spacers", visible=False)
        self.battery_cell_prim_path = "/World/battery_pack/batteries/Battery_cell_"
        self.target_pose = self.world.scene.add(XFormPrim(prim_path="/World/target", name="target", position=[0,0,1], orientation=rot_utils.euler_angles_to_quats([0, np.pi, 0])))
        
        self.cover_top_grab_j = [0.67755276, -0.7666832, 1.4482822, -2.2479215, -1.570691, 2.24841]
        self.battery_cell_00_grab_T = sm.SE3.Rt(np.array([[-1, 0,  0],
                                                           [0, 1,  0],
                                                        #    [0, 0, -1]]), [-0.482,  0.633,  0.082])
                                                           [0, 0, -1]]), [-0.017,  0.334,  0.826])
         
        self.world.scene.add(self.robot)
        for obj in self.objects:
            self.world.scene.add(self.objects[obj])

        self.robot.subscribe_to_topic('joint_states')
        pose_sub = isaac_sim.PoseArraySubscriber('poses', world=self.world, ros_node=self, prim_path="/World/ros_poses/pose")
    
    def setup_task(self):
        pass

    def manage_input(self):
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            cmd = sys.stdin.read(1)
            os.system('clear')
            if cmd == 'j':
                print(self.robot.get_joint_positions())
                print("robot frame:", self.robot.get_tcp_pose())
                print("world frame:", self.robot.robot_T_world(self.robot.get_tcp_pose()))

    def grab_cover(self, starting_idx=100):
        if self.world.current_time_step_index == starting_idx:
            self.robot.move_to_joint_position(self.cover_top_grab_j, t=100)
        if self.world.current_time_step_index == starting_idx+100:
            self.joint = utils.createJoint(self.world.stage, "Fixed", self.world.stage.GetPrimAtPath(self.objects['top_cover'].prim_path), self.world.stage.GetPrimAtPath("/World/ur5e/tool0/suction_cup"))
            self.robot.move_up(-0.35, t=100)
            self.robot.move_to_cart_position(self.robot.get_tcp_pose() * sm.SE3([0.3, 0, 0]), t=100)
            self.robot.move_up(0.35, t=100)
        if self.world.current_time_step_index == starting_idx+400:
            self.world.stage.RemovePrim(self.joint.GetPath())
            self.robot.move_up(-0.75, t=100)
            self.robot.move_to_home_position()

    def grab_battery(self, battery_id=0, starting_idx=100, t=300):
        # cell_p = self.battery_cell_00_grab_T * sm.SE3([])
        if self.world.current_time_step_index == starting_idx:
            self.robot.move_to_cart_position(self.robot.world_T_robot(self.battery_cell_00_grab_T * sm.SE3([0, 0, -0.3])), t=t)
            self.robot.move_up(0.3, t=t)
        if self.world.current_time_step_index == starting_idx+2*t:
            self.joint = utils.createJoint(self.world.stage, "Fixed", self.world.stage.GetPrimAtPath(str(self.battery_cell_prim_path) + "{:02d}".format(battery_id)), self.world.stage.GetPrimAtPath("/World/ur5e/tool0/suction_cup"))
            self.robot.move_up(-0.2, t=t)
            self.robot.move_to_cart_position(self.robot.get_tcp_pose() * sm.SE3([0.18, 0, 0]), t=t)
            self.robot.move_up(0.2, t=t)
        if self.world.current_time_step_index == starting_idx+(6*t):
            self.world.stage.RemovePrim(self.joint.GetPath())
            self.robot.move_up(-0.5, t=t)
            self.robot.move_to_home_position()

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
                self.robot.physisc_step()
                self.world.step(render=True)
                self.manage_input()
                # self.robot.follow_frame(self.target_pose)
                self.grab_battery()
        self.timeline.stop()
        self.destroy_node()
        simulation_app.close()

def main():
    rclpy.init()
    demo = MEM()
    demo.run_simulation()

if __name__ == "__main__":
    main()
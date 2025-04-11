import py_trees as pt
import time
from gui_module import MemGui
from robot_module import RobotModule
from battery_pack_module import PackState
from rdf_store import RdfStore
from vision_module import VisionModule
from behaviors import *
from viewer import BtViewer
import spatialmath as sm
import numpy as np

class BehaviourTree(pt.trees.BehaviourTree):
    def __init__(self):        
        # Blackboard and registering keys 
        cell_m_q, cell_h_q = 0.6, 0.8 # this defines them everywhere
        R = sm.UnitQuaternion(s=0.7058517498982678, v=[0.006697022630599267, -0.0007521624314972674, 0.7083275310935719]).SO3()     
        t = np.array([0.04627923466437427, -0.03278714750773679, 0.01545089678599013])

        self.over_pack_T = sm.SE3([-0.23, -0.31, 0.33]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg")
        self.discard_T = sm.SE3([-0.247, -0.575, 0.15]) * sm.SE3.Rx(np.pi)    # needs to be defined from the real setup
        self.keep_T =    sm.SE3([-0.106, -0.518, 0.15]) * sm.SE3.Rx(np.pi)    # needs to be defined from the real setup
        self.camera_Ext = sm.SE3.Rt(R, t)
        self.bin_rotvec = [-0.03655, -0.5088, 0.20, -0.5923478428527734, 3.063484429352879, 0.003118486651508924]
        self.pack_height = 0.090

        self.blackboard = pt.blackboard.Client(name="Blackboard_client")   
        self.rdf = RdfStore()
        self.vision = VisionModule(camera_Ext=self.camera_Ext)
        self.robot = RobotModule(ip="192.168.1.100", home_position=[0, 0, 0, 0, 0, 0], tcp_length_dict={'small': -0.041, 'big': -0.08}, active_gripper='big', gripper_id=0)
        self.pack_state = PackState()
        #self.pack_state = PackState(rows=1, cols=2)
        #self.pack_state.update_cell(0, 1, pose=(sm.SE3([-0.295, -0.255, 0.110]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg")))
        #self.pack_state.update_cell(0, 0, pose=(sm.SE3([-0.281, -0.288, 0.110]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg")))
        self.gui = MemGui(camera_frame=self.vision.get_current_frame(format='pil'), cell_m_q=cell_m_q, cell_h_q=cell_h_q)
        #self.robot.move_to_cart_pos(self.over_pack_T)

        # Leaf nodes
        self.begin_session = BeginSession(name="begin_session", rdf=self.rdf, gui=self.gui, vision=self.vision, frame_id = 7)        
        self.pack_placed = PackPlaced(name="pack_placed", rdf=self.rdf, gui=self.gui, vision=self.vision, frame_id = 8)
        self.auto_pack_class = AutoPackClass(name="auto_pack_class", rdf=self.rdf, gui=self.gui, vision=self.vision, frame_id = 15, pack_state=self.pack_state)
        self.helped_pack_class = HelpedPackClass(name="helped_pack_class", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, vision=self.vision, frame_id = 16)
        self.helped_locate_pack = HelpedLocatePack(name="helped_locate_pack", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, frame_id = 17, vision=self.vision)
        self.check_cover_off = CheckCoverOff(name="check_cover_off", rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.check_human_removes_cover = CheckHumanRemovesCover(name="check_human_removes_cover", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, frame_id = 12, vision=self.vision)
        self.check_colab_remove_cover = pt.decorators.Inverter(name="inverter",child=CheckColabRemoveCover(name="check_colab_remove_cover", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, frame_id = 12, vision=self.vision))
        self.colab_await_human = ColabAwaitHuman(name="colab_await_human", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, frame_id = 13, vision=self.vision)
        self.remove_cover = RemoveCover(name="remove_cover", rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui, 
                                        robot=self.robot, bin_rotvec=self.bin_rotvec, pack_height=self.pack_height, over_pack_T=self.over_pack_T, frame_id = 14)
        self.await_tool_change_small = AwaitToolChange(name="await_tool_change_small", rdf=self.rdf, gui=self.gui, robot=self.robot, frame_id = 10, vision=self.vision)
        self.await_tool_change_big = AwaitToolChange(name="await_tool_change_big", rdf=self.rdf, gui=self.gui, robot=self.robot, frame_id = 10, vision=self.vision)
        self.big_gripper = BigGripper(name="big_gripper", rdf=self.rdf, gui=self.gui, robot=self.robot, frame_id = 9, vision=self.vision)
        self.small_gripper = SmallGripper(name="small_gripper", rdf=self.rdf, gui=self.gui, robot=self.robot, frame_id = 9, vision=self.vision)
        self.check_pack_known = CheckPackKnown(name="check_pack_known", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, vision=self.vision)
        self.auto_cell_class = AutoCellClass(name="auto_cell_class", rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui, frame_id = 1)
        self.helped_cell_class = HelpedCellClass(name="helped_cell_class", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, frame_id = 2, vision=self.vision)
        self.detect = Detect(name="detect", rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui, robot=self.robot, frame_id = 3)
        self.assess = Assess(name="assess", rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui, frame_id = 4)
        self.check_cells_ok = CheckCellsOK(name="check_cells_ok", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, vision=self.vision)
        self.auto_sort = AutoSort(name="auto_sort", rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, robot=self.robot, gui=self.gui, 
                                  cell_h_q=cell_h_q, cell_m_q=cell_m_q, discard_T=self.discard_T, keep_T=self.keep_T, over_pack_T=self.over_pack_T, frame_id = 5)
        self.helped_sort = HelpedSort(name="helped_sort", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, frame_id = 6, vision=self.vision)
        self.await_cover_fastening = AwaitCoverFastening(name="await_cover_fastening", rdf=self.rdf, gui=self.gui, frame_id = 11, vision=self.vision)
        self.discard_pack = RemoveCover(name="discard_pack", rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, vision=self.vision, robot=self.robot, bin_rotvec=self.bin_rotvec, 
                                        pack_height=self.pack_height, over_pack_T=self.over_pack_T, frame_id = 14)

        # Selectors and sequences
        self.helped_pack_class_sequence = pt.composites.Sequence(name="helped_pack_class_sequence", memory=True, children=[self.helped_pack_class,self.helped_locate_pack])
        self.class_pack_selector = pt.composites.Selector(name="class_pack_selector", memory=True, children=[self.auto_pack_class, self.helped_pack_class_sequence]) # memory=True to avoid GUI state switch
        self.big_tool_selector = pt.composites.Selector(name="big_tool_selector", memory=True, children=[self.big_gripper, self.await_tool_change_big]) 
        self.colab_cover_removal_selector = pt.composites.Selector(name="colab_cover_removal_selector", memory=True, children=[self.check_colab_remove_cover, self.colab_await_human])
        self.robot_remove_cover_sequence = pt.composites.Sequence(name="robot_remove_cover_sequence",memory=True, children=[self.big_tool_selector, self.colab_cover_removal_selector, self.remove_cover])
        self.remove_cover_selector = pt.composites.Selector(name="remove_cover_selector", memory=True, children=[self.check_human_removes_cover, self.robot_remove_cover_sequence])
        
        # memory = False to keep checking whether cover is on/off until confirmed
        self.cover_selector = pt.composites.Selector(name="cover_selector", memory=False, children=[self.check_cover_off, self.remove_cover_selector])
        self.class_cell_selector = pt.composites.Selector(name="class_cell_selector", memory=True, children=[self.check_pack_known, self.auto_cell_class, self.helped_cell_class]) 
        self.small_tool_selector = pt.composites.Selector(name="small_tool_selector", memory=True, children=[self.small_gripper, self.await_tool_change_small]) 
        self.robot_sort_sequence = pt.composites.Sequence(name="robot_sort_sequence",memory=True, children=[self.small_tool_selector, self.auto_sort])
        self.human_sort_sequence = pt.composites.Sequence(name="human_sort_sequence",memory=True, children=[self.check_cells_ok, self.helped_sort])
        self.discard_pack_sequence = pt.composites.Sequence(name="discard_pack_sequence",memory=True, children=[self.await_cover_fastening, self.discard_pack])
        self.sort_selector = pt.composites.Selector(name="sort_selector", memory=True, children=[self.robot_sort_sequence, self.human_sort_sequence, self.discard_pack_sequence])

        # Main sequence 
        self.main_sequence = pt.composites.Sequence(name="main_sequence",memory=True)
        self.main_sequence.add_children([self.begin_session,
                                         self.pack_placed,
                                         self.class_pack_selector,
                                         self.cover_selector,
                                         self.class_cell_selector,
                                         self.detect,
                                         self.assess,
                                         self.sort_selector])

        tree = self.main_sequence

        super(BehaviourTree, self).__init__(tree)
        # self.viewer = BtViewer(self)

        #self.gui.after(1000, self.tick_tree_in_gui)
        #self.gui.mainloop()

    def on_gui_closure(self):
        self.root.status = pt.common.Status.FAILURE
        print("GUI closed")
        self.gui.destroy()

    def tick_tree_in_gui(self):
        if self.root.status == pt.common.Status.SUCCESS:
            print("Behavior tree succeeded")
            print(self.pack_state)
            self.gui.reset_gui()
            self.main_sequence.stop(pt.common.Status.INVALID) # reset the tree
            self.gui.after(1, self.tick_tree_in_gui)
        elif self.root.status == pt.common.Status.FAILURE:
            print("Behavior tree failed")
            print(self.pack_state)
            self.gui.quit()
        else:
            self.tick()
            self.gui.after(1, self.tick_tree_in_gui)
            #self.viewer.update()
            #print("\n"+pt.display.unicode_tree(root=self.root,show_status=True))
        
def main(args=None):
    tree = BehaviourTree()
    tree.gui.protocol("WM_DELETE_WINDOW", tree.on_gui_closure)

    tree.gui.after(1, tree.tick_tree_in_gui)
    tree.gui.mainloop()

if __name__ == "__main__":
    main()
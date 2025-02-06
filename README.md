# fluently_mem
MEM use case from fluently project

## GUI

The gui is basically ready, the buttons changes some variables in the gui object. The behaviors should look at these variables and suceed or fail accordingly. Each (or almost all) behavior should activate one frame of the gui with:

     self.gui.show_frame(id).
    
See class Test01 for an example

To see which number represent which state you can run: 
    
    python3 src/gui_module.py <id>

## Vision module

Vision module is in place and should be usable, I have not implemented everything but everything is in place(it will just provide random datas) the function you want to use are: 

    vision_module.classify_cell([camera_frame])
    positions = vision_module.cell_detection(camera_frame)
    qualities = vision_module.assess_cells_qualities(camera_frame, positions)
    pickedup = vision_module. verify_pickup(camera_frame, positions[-1][:-1])

## Robot module

The robot module should not be of any concern for you yet there are functions in place that you can call 

    robot_module.pick_and_place()
    robot_module.frame_to_world()

## Behaviour tree and GUI integration

Since we need both of them to run cyclically together we need to integrate them one into the other. See example.py on how to do that.
Add this function to your behavior tree:

    def tick_tree_in_gui(self):
        self.tick()
        self.gui.after(1, self.tick_tree_in_gui)

After you init the behavior tree add the function in the after of the gui, this will make the gui run the fucntion every 1 ms

    self.gui.after(1, self.tick_tree_in_gui)

Start the gui mainloop
    self.gui.mainloop()

you can either do that in the init as i did or you can do it later in the program
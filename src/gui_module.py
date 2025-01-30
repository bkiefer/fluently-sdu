from numpy import ndarray

class Gui():
    def __init__(self):
        self.states = []
        self.showing_frame = None
        self.active_state = 0
        self.wait_interaction = False
        self.chosen_model = ""
        self.chosen_locations = []

    def update_state(self, state_id: int):
        """update the state of the gui the current state will be hidden and the new one will be visible

        Args:
            state_id (int): id of new state
        """
        pass

    def ask_for_help(self,  query: str):
        """ask human for help for something

        Args:
            query (str): the question/request for the human
        """
        pass

    def draw_bbs(self, bbs_position: list[ndarray]):
        """draw bounding boxes on the battery on the frame showed for the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes
        """
    
    def write_qualities(self, bbs_position: list[ndarray], qualities: list[float]):
        """write the quality of each cell on the frame showed to the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes for each cell
            qualities (list[float]): qualities of each cell
        """

class GuiState():
    def __init__(self):
        pass

import logging
import numpy as np
from numpy import ndarray
import spatialmath as sm

class CustomLogger(logging.Logger):
    """
    Custom class expanding the logger from python library
    """
    def __init__(self, name, filename=None, console_level="warning", file_level=None, overwrite=True):

        super().__init__(name)
        formatter = logging.Formatter('%(name)-6s: %(asctime)s - %(levelname)-7s - %(message)s')
        self.filename = filename

        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(formatter)

        levels = {'warning': logging.WARNING, 'error': logging.ERROR, 'info': logging.INFO, 'debug': logging.DEBUG}
        self.console_handler.setLevel(level=levels[console_level])
        self.addHandler(self.console_handler)

        if file_level is not None:
            # Create file handler and set level to DEBUG
            if os.path.exists(self.filename):
                if os.path.getsize(self.filename) > 100e3: # the size is in Byte
                    os.remove(self.filename)
            mode = 'a' if not overwrite else 'w' # mode a: append at the end of the file, w: write new file
            if filename is not None:
                file_handler = logging.FileHandler(self.filename, mode=mode, encoding='utf-8')
                file_handler.setLevel(level=levels[file_level])

                # Create formatter and add it to the handlers
                file_handler.setFormatter(formatter)

                # Add the handlers to the logger
                self.addHandler(file_handler)

        self.info("NEW RUN")

    def toggle_offon(self):
        self.console_handler.setLevel(level=logging.CRITICAL)

def bool_to_str_fancy(var: bool):
    if var is None:
        return "○"
    return "✗" if not var else "✓"

def rotvec_to_T(rotvec: ndarray):
    return sm.SE3.Rt(sm.SO3.EulerVec(rotvec[3:]), rotvec[:3])

def T_to_rotvec(T: sm.SE3):
    return np.hstack((T.t, sm.SO3(T.R).eulervec()))

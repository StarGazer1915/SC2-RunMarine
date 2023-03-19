import numpy as np

class MarineAgent:
    def __init__(self):
        self.use_viz = False                    # Use visualization
        self.vismap_stored = False              # There is a vision map stored
        self.vismap_scores = np.array([])       # The actual vision map with its values (what the marine has seen)
        self.valid_point_threshold = 0.8        # Threshold that determines if a point is valid to move towards
        self.passability_map = np.array([])     # The passability map that shows what points are actually passable.
        self.map_y_size = 0                     # vertical length of the current map
        self.map_x_size = 0                     # horizontal length of the current map
        super().__init__()


    def percept_environment(self):
        pass


    def define_state(self):
        pass


    def take_action(self):
        pass




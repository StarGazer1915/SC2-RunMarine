import numpy as np
from sc2.position import Point2

class MarineAgent:
    def __init__(self):
        self.unit = None                        # sc2 unit object (Marine unit is this case)
        self.vision_mask = np.array([])  # array with True/False that indicates the current vision of the unit
        self.use_viz = False                    # Use visualization
        self.vismap_stored = False              # There is a vision map stored
        self.vismap_scores = np.array([])       # The actual full vision map with its scored values
        self.valid_point_threshold = 0.8        # Threshold that determines if a point is valid to move towards
        self.passability_map = np.array([])     # The passability map that shows what map points are passable
        self.map_y_size = None                  # vertical length of the current map
        self.map_x_size = None                  # horizontal length of the current map
        super().__init__()

    def pad_with(self, array, pad_width, iaxis, kwargs):
        """
        Function that adds padding to an array to be able to create
        scores for the outer edges when creating areas with create_area().
        :param array: ndarray
        :param pad_width: integer
        :param iaxis: integer
        :param kwargs: float
        """
        array[:pad_width[0]] = kwargs.get('padder', 10)
        array[-pad_width[1]:] = kwargs.get('padder', 10)

    def create_area(self, array, point, distance=2):
        """
        Simple function that takes the values around a point (5x5 in this case)
        and returns it as a ndarray with the initial point in the center.
        :param array: ndarray
        :param point: tuple
        :param distance: int (default 2)
        :return: ndarray
        """
        return array[point[0] - distance:point[0] + distance + 1, point[1] - distance:point[1] + distance + 1]

    def percept_environment(self):
        newmap = self.unit.visibility.data_numpy.astype("float64")

        if not self.vismap_stored:
            self.vismap_scores = newmap
            self.vismap_stored = True
        else:
            # ===== Generate scores for current vision ===== #
            vismap_padded = np.pad(newmap, 2, self.pad_with, padder=0.)
            for row in range(self.map_y_size):
                for col in range(self.map_x_size):
                    if self.vision_mask[row][col] and vismap_padded[row+2][col+2] != 0.0:
                        if self.passability_map[row][col] != 0.0:
                            area = self.create_area(vismap_padded, (row+2, col+2), distance=2).copy()
                            area[area > self.valid_point_threshold] = 1
                            area[area <= self.valid_point_threshold] = 0
                            score = round(sum(area.flatten()) / (len(area) * len(area[0])), 2)
                            self.vismap_scores[row][col] = score
                        else:
                            vismap_padded[row+2][col+2] = 0.0
                            self.vismap_scores[row][col] = 0.0

    def define_state(self):
        pass

    def take_action(self):
        highest_coor_in_vision = 0.0
        highest_scoring_coor = (0.0, 0.0)
        longest_distance_to_bane = 0.0

        for row in range(self.map_y_size):
            for col in range(self.map_x_size):
                if self.vision_mask[row][col]:
                    if self.vismap_scores[row][col] >= highest_coor_in_vision:
                        if round(self.unit.distance_to(Point2((col, row))), 2) > longest_distance_to_bane:
                            highest_coor_in_vision = self.vismap_scores[row][col]
                            highest_scoring_coor = (col, (-row + 32))
                            longest_distance_to_bane = round(self.unit.distance_to(Point2((col, row))), 2)
                        else:
                            highest_coor_in_vision = self.vismap_scores[row][col]
                            highest_scoring_coor = (col, (-row + 32))

        self.unit.move(Point2(highest_scoring_coor))




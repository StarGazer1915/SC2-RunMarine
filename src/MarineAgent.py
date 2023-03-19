import numpy as np
from sc2.position import Point2


class MarineAgent:
    def __init__(self, unit, passability_map, map_y_size, map_x_size):
        self.unit = unit                            # sc2 unit object (Marine unit is this case)
        self.vismap_stored = False                  # There is a vision map stored
        self.vismap_scores = np.array([])           # The actual full vision map with its scored values
        self.valid_point_threshold = 0.8            # Threshold that determines if a point is valid to move towards
        self.passability_map = passability_map      # The passability map that shows what map points are passable
        self.bmasks = []                            # Baneling objects in current vision
        self.map_y_size = map_y_size                # vertical length of the current map
        self.map_x_size = map_x_size                # horizontal length of the current map

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
        and returns it as a np-array with the initial point in the center.
        :param array: ndarray
        :param point: tuple
        :param distance: int (default 2)
        :return: ndarray
        """
        return array[point[0] - distance:point[0] + distance + 1, point[1] - distance:point[1] + distance + 1]

    def percept_environment(self, updated_map, vision_mask):
        new_map = updated_map.copy()
        new_map[vision_mask != True] = 0.0

        if not self.vismap_stored:
            self.vismap_scores = new_map
            self.vismap_stored = True
        else:
            # ===== Generate scores for current vision ===== #
            vismap_padded = np.pad(new_map, 2, self.pad_with, padder=0.)
            for row in range(self.map_y_size):
                for col in range(self.map_x_size):
                    if vision_mask[row][col] and vismap_padded[row+2][col+2] != 0.0:
                        if self.passability_map[row][col] != 0.0:
                            area = self.create_area(vismap_padded, (row+2, col+2), distance=2).copy()
                            area[area > self.valid_point_threshold] = 1
                            area[area <= self.valid_point_threshold] = 0
                            score = round(sum(area.flatten()) / (len(area) * len(area[0])), 2)
                            self.vismap_scores[row][col] = score
                        else:
                            vismap_padded[row+2][col+2] = 0.0
                            self.vismap_scores[row][col] = 0.0

    def apply_baneling_sof(self, marine_mask, baneling_masks):
        for mask_set in baneling_masks:
            self.vismap_scores[(mask_set[2] == True) & (marine_mask == True)] *= 0.9
            self.vismap_scores[(mask_set[1] == True) & (marine_mask == True)] *= 0.6
            self.vismap_scores[(mask_set[0] == True) & (marine_mask == True)] *= 0.1
        self.vismap_scores = np.around(self.vismap_scores.copy(), 2)

    def define_state(self):
        pass

    def take_action(self, vision_mask, known_banes):
        highest_coor_in_vision = 0.0
        highest_scoring_coor = (0.0, 0.0)
        longest_distance_to_bane = 0.0

        for row in range(self.map_y_size):
            for col in range(self.map_x_size):
                if vision_mask[row][col]:
                    # for baneling in known_banes:
                    #     b_dist_to_p = baneling.distance_to(Point2((col, row)))
                    #     m_dist_to_p = self.unit.distance_to(Point2((col, row)))
                    # if m_dist_to_p < b_dist_to_p:
                    if self.vismap_scores[row][col] >= highest_coor_in_vision:
                        if known_banes[0].distance_to(Point2((col, row))) > longest_distance_to_bane:
                            highest_coor_in_vision = self.vismap_scores[row][col]
                            highest_scoring_coor = (col, (-row + 32))
                            longest_distance_to_bane = round(known_banes[0].distance_to(Point2((col, row))), 2)
                        else:
                            highest_coor_in_vision = self.vismap_scores[row][col]
                            highest_scoring_coor = (col, (-row + 32))

        return self.unit.move(Point2(highest_scoring_coor))

    def __str__(self):
        return f"Agent: {self.unit.name}"




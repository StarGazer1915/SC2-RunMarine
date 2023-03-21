import numpy as np
from sc2.position import Point2


class MarineAgent:
    def __init__(self, unit, passability_map, map_y_size, map_x_size):
        self.unit = unit                            # sc2 unit object in-game (Marine unit is this case)
        self.vismap_stored = False                  # If a vision map is stored
        self.vismap_scores = np.array([])           # The actual full vision map with its scored values
        self.valid_point_threshold = 0.8            # Threshold that determines if a point is valid to move towards
        self.passability_map = passability_map      # The passability map that shows what map points are passable
        self.bmasks = []                            # Baneling objects in current vision
        self.map_y_size = map_y_size                # vertical length of the current map
        self.map_x_size = map_x_size                # horizontal length of the current map

    def pad_with(self, array, pad_width, iaxis, kwargs):
        """
        Takes an array and pads it (extends the outer edges of a grid).
        :param array: numpy array / list
        :param pad_width: int
        :param iaxis: int
        :param kwargs: kwarg object (int)
        """
        array[:pad_width[0]] = kwargs.get('padder', 10)
        array[-pad_width[1]:] = kwargs.get('padder', 10)

    def create_area(self, array, point, distance=2):
        """
        Creates a new array/list in an area around a certain index (point). In the percept_environment() function
        for example it will take values in a 5x5 area around the point, so the point is in the center. This way
        a score can be generated on how passable a point is based on the area around the point.
        :param array: numpy array / list
        :param point: tuple
        :param distance: int
        :return: numpy array / list
        """
        return array[point[0] - distance:point[0] + distance + 1, point[1] - distance:point[1] + distance + 1]

    def percept_environment(self, updated_map, vision_mask):
        """

        :param updated_map:
        :param vision_mask:
        """
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
        """
        This function applies modifiers on the scoremap in the masks given by the baneling_masks.
        These modifiers indicate to the agent how dangerous areas around the baneling are. These can be
        seen as multiple circular layers and their impact becomes increasingly negative the closer the agent
        moves towards the baneling. This way the fear of getting close to the baneling is simulated.
        :param marine_mask: numpy array
        :param baneling_masks: list of numpy arrays
        :return: void
        """
        for mask_set in baneling_masks:
            self.vismap_scores[(mask_set[2] == True) & (marine_mask == True)] *= 0.9
            self.vismap_scores[(mask_set[1] == True) & (marine_mask == True)] *= 0.6
            self.vismap_scores[(mask_set[0] == True) & (marine_mask == True)] *= 0.1
        self.vismap_scores = np.around(self.vismap_scores.copy(), 2)

    def define_state(self):
        return

    def take_action(self, vision_mask, known_banes):
        """
        This function looks at all the points inside the current vision of the agent and calculates the
        highest scoring point that is also the farthest away from the baneling. It then returns the move
        command with said point so the SC2bot can execute the move order.
        :param vision_mask: numpy array
        :param known_banes: list of sc2 unit objects
        :return: sc2 move command
        """
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

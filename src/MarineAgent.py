import numpy as np
from sc2.position import Point2


class MarineAgent:
    def __init__(self, passability_map, map_y_size, map_x_size):
        self.position = None
        self.vismap_stored = False
        self.vismap_scores = np.zeros(shape=(map_x_size, map_y_size)).astype("float64")
        self.valid_point_threshold = 0.7
        self.passability_map = passability_map
        self.map_y_size = map_y_size
        self.map_x_size = map_x_size

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

    def percept_environment(self, vision_mask):
        """
        ...
        :param updated_map:
        :param vision_mask:
        """
        new_map = self.vismap_scores.copy()
        new_map[vision_mask == True] = 2.0
        # ===== Generate scores for current vision ===== #
        vismap_padded = np.pad(new_map, 2, self.pad_with, padder=0.)
        for row in range(self.map_y_size):
            for col in range(self.map_x_size):
                if vision_mask[row][col]:
                    if self.passability_map[row][col] != 0.0:
                        area = self.create_area(vismap_padded, (row+2, col+2), distance=2).copy()
                        area[area > self.valid_point_threshold] = 1
                        area[area <= self.valid_point_threshold] = 0
                        score = round(sum(area.flatten()) / (len(area) * len(area[0])), 2)
                        self.vismap_scores[row][col] = score
                    else:
                        vismap_padded[row+2][col+2] = 0.0
                        self.vismap_scores[row][col] = 0.0

    def apply_baneling_sof(self, baneling_masks):
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
            self.vismap_scores[(mask_set[2] == True)] *= 0.9    # Bmask 3, sight_range, outer circle
            self.vismap_scores[(mask_set[1] == True)] *= 0.7    # Bmask 2, sight_range - 3.0, medium circle
            self.vismap_scores[(mask_set[0] == True)] *= 0.1    # Bmask 1, sight_range - 6.0, baneling touching

        self.vismap_scores = np.around(self.vismap_scores.copy(), 2)

        # print("\n")
        # for y in self.vismap_scores:
        #     line = ""
        #     for x in y:
        #         line += str(f"{x} ")
        #     print(line)

    def define_state(self):
        return

    def get_best_point(self, vision_mask, marine, known_banes):
        """
        This function looks at all the points inside the current vision of the agent and calculates the
        highest scoring point that is also the farthest away from the baneling. It then returns the move
        command with said point so the SC2bot can execute the move order.
        :param vision_mask: numpy array
        :param known_banes: list of sc2 unit objects
        :return: sc2 move command
        """
        highest_point_in_vision = 0.0
        highest_scoring_point = (0.0, 0.0)
        longest_distance_to_bane = 0.0
        marine_position = (round(marine.position[0], 0), (-round(marine.position[1], 0) + 32))
        baneling_position = (round(known_banes[0].position[0], 0), (-round(known_banes[0].position[1], 0) + 32))

        for row in range(self.map_y_size):
            for col in range(self.map_x_size):
                if vision_mask[row][col]:
                    if self.vismap_scores[row][col] > highest_point_in_vision:
                        bane_dist_to_point = round(known_banes[0].distance_to(Point2((col, row))), 2)
                        if bane_dist_to_point > longest_distance_to_bane:
                            highest_point_in_vision = self.vismap_scores[row][col]
                            highest_scoring_point = (col, row)
                            longest_distance_to_bane = bane_dist_to_point
                        else:
                            highest_point_in_vision = self.vismap_scores[row][col]
                            highest_scoring_point = (col, row)

        # ====================================================================================================== #
        print(f"\n\nCHOSEN POINT: {highest_scoring_point}")
        print(f"VISION MASK: ")
        for row2 in range(len(vision_mask)):
            line = ""
            for point2 in range(len(vision_mask[row2])):
                if int(point2) == int(highest_scoring_point[0]) and int(row2) == int(highest_scoring_point[1]):
                    line += str(f"-GOAL- ")
                elif int(point2) == int(marine_position[0]) and int(row2) == int(marine_position[1]):
                    line += str(f"-TM- ")
                elif int(point2) == int(baneling_position[0]) and int(row2) == int(baneling_position[1]):
                    line += str(f"-ZB- ")
                else:
                    line += str(f"{vision_mask[row2][point2]} ")
            print(line)

        print(f"\nSCORES:")
        for row2 in range(len(self.vismap_scores)):
            line = ""
            for point2 in range(len(self.vismap_scores[row2])):
                if int(point2) == int(highest_scoring_point[0]) and int(row2) == int(highest_scoring_point[1]):
                    line += str(f"-GOAL- ")
                elif int(point2) == int(marine_position[0]) and int(row2) == int(marine_position[1]):
                    line += str(f"-TM- ")
                elif int(point2) == int(baneling_position[0]) and int(row2) == int(baneling_position[1]):
                    line += str(f"-ZB- ")
                else:
                    line += str(f"{self.vismap_scores[row2][point2]} ")
            print(line)
        # ====================================================================================================== #
        flipped_point = (highest_scoring_point[0], -highest_scoring_point[1] + 32)
        return Point2(flipped_point)

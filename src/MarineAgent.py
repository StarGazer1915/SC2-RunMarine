import numpy as np
from sc2.position import Point2


class MarineAgent:
    def __init__(self, passability_map, map_y_size, map_x_size, tag):
        self.position = None
        self.vismap_stored = False
        self.vismap_scores = np.zeros(shape=(map_y_size, map_x_size)).astype("float64")
        self.valid_point_threshold = 0.8
        self.passability_map = passability_map
        self.map_y_size = map_y_size
        self.map_x_size = map_x_size
        self.tag = tag
        self.atype = ""
        self.performance_score = 0
        self.partner_agent_tag = 0
        self.chosen_action = ""

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
        This function generates scores in the current vision_mask. These scores are based on how passable the
        points are and what their area contains (if the area contains a lot of passable points). The scores are
        then calculated and stored in the agent's memory (self.vismap_scores).
        :param vision_mask: numpy array / list
        :return: void
        """
        new_map = self.vismap_scores.copy()
        new_map[vision_mask == True] = 2.0

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
        This function applies modifiers on the score map in the masks given by the baneling_masks.
        These modifiers indicate to the agent how dangerous areas around the baneling are. These can be
        seen as multiple circular layers and their impact becomes increasingly negative the closer the agent
        moves towards the baneling. This way the fear of getting close to the baneling is simulated.
        :param baneling_masks: list of numpy arrays
        :return: void
        """
        for mask_set in baneling_masks:
            self.vismap_scores[(mask_set[2] == True)] *= 0.9    # Bmask 3, sight_range, outer baneling vision
            self.vismap_scores[(mask_set[1] == True)] *= 0.5    # Bmask 2, sight_range - 2.5, baneling attack range
            self.vismap_scores[(mask_set[0] == True)] *= 0.1    # Bmask 1, sight_range - 6.0, baneling lethal zone

        self.vismap_scores = np.around(self.vismap_scores.copy(), 2)

    def define_matrix_scores(self, adict):
        """
        This function seperates the choices and scores from the dictionary into a comprehensible and iterable
        multidimensional list.
        :param adict: nested dict
        :return: multidimensional list
        """
        choices = []
        scores = []
        for cat in adict["Scores"]:
            for subcat in adict["Scores"][cat]:
                choices.append([f"{cat}", f"{subcat}"])
                scores.append(adict["Scores"][cat][subcat])

        return [choices, scores]

    def find_altruistic_best_choice(self, adict):
        """
        This function chooses the most pareto optimal choice for the altruistic agents, in this case being the combination
        that yields both parties the biggest possible result.
        :param adict: nested dict
        :return: string
        """
        #! Finding a pareto optimallity
        pairs = self.define_matrix_scores(adict)
        highest_score = max(pairs[1])  # Get largest scoring pair
        best_combo = pairs[0][pairs[1].index(highest_score)]  # See what combination results those scores
        return best_combo[0]  # Return own choice for that combination of choices

    def find_rational_choice(self, adict):
        """
        TODO rewrite this docstring for a rational agent.
        This function is used for the rational agent type, and looks for a nash equilibrium in the state of social dillema.
        If it can find multiple it will pick the most profitable option for both parties.
        Else it will settle for a more sub optimal solution.
        :param adict: nested dict
        :return: string
        """

        # # * The rational agent always assumes that his partner agent is also a rational agent.

        scores = adict["Scores"]
        
        # Looking from the perspective of m1
        m1_best_combo_m2a = ["Attack", "Attack"] if scores["Attack"]["Attack"][0] > scores["Flee"]["Attack"][0] else ["Flee", "Attack"]
        m1_best_choice_m2a = m1_best_combo_m2a[0]

        m1_best_combo_m2f = ["Attack", "Flee"] if scores["Attack"]["Flee"][0] > scores["Flee"]["Flee"][0] else ["Flee", "Flee"]
        m1_best_choice_m2f = m1_best_combo_m2f[0]

        # Now Looking from the partners perspective 
        m2_best_combo_m1a = ["Attack", "Attack"] if scores["Attack"]["Attack"][1] > scores["Attack"]["Flee"][1] else ["Attack", "Flee"]
        m2_best_choice_m1a = m2_best_combo_m1a[1]

        m2_best_combo_m1f = ["Flee", "Attack"] if scores["Flee"]["Attack"][1] > scores["Flee"]["Flee"][1] else ["Flee", "Flee"]
        m2_best_choice_m1f = m2_best_combo_m1f[1]

        # Checking for nash equilibrium
        if m1_best_combo_m2a == m2_best_combo_m1a or m1_best_combo_m2a == m2_best_combo_m1f:
            if m1_best_combo_m2f == m2_best_combo_m1a or m1_best_combo_m2a == m2_best_combo_m1f:
                self.chosen_action = m1_best_choice_m2a if scores[m1_best_combo_m2a].sum() > scores[m1_best_choice_m2f].sum() else m1_best_choice_m2f
            else:
                self.chosen_action = m1_best_choice_m2a
        elif m1_best_combo_m2f == m2_best_combo_m1a or m1_best_combo_m2a == m2_best_combo_m1f:
            self.chosen_action = m1_best_choice_m2f

        # If now nash equilibrium has been found, figure out and take the best suboptimol outcome for both parties
        elif m1_best_choice_m2a == m1_best_choice_m2f:
            if m1_best_choice_m2a == "Attack":
                self.chosen_action = m1_best_choice_m2a if m2_best_choice_m1a == "Attack" else m1_best_choice_m2f
            elif m1_best_choice_m2a == "Flee":
                self.chosen_action = m1_best_choice_m2a if m2_best_choice_m1f == "Attack" else m1_best_choice_m2f

        elif m2_best_choice_m1a == m2_best_choice_m1f:
            if m2_best_choice_m1a == "Attack":
                self.chosen_action = m1_best_choice_m2a
            elif m2_best_choice_m1a == "Flee":
                self.chosen_action = m1_best_choice_m2f





    def take_action_from_action_matrix(self, action_matrix):
        """
        Choose an action behavior based on the agent's atype.
        :param action_matrix: nested dict
        """
        if self.atype == "rational":
            self.chosen_action = self.find_rational_choice(action_matrix)
        elif self.atype == "altruistic":
            self.chosen_action = self.find_altruistic_best_choice(action_matrix)
        elif self.atype == "attacker":
            self.chosen_action = "Attack"
        else:
            self.chosen_action = "Flee"

    def get_best_point(self, vision_mask, known_banes):
        """
        This function looks at all the points inside the current vision of the agent and calculates the
        highest scoring point that is also the farthest away from the baneling. The choice is based
        on the viability/passability of the point, and it's surrounding area. It then returns the point
        so that in this case the SC2 bot can execute a move order to that point.
        :param vision_mask: numpy array
        :param known_banes: list of sc2 unit objects
        :return: sc2 Point2
        """
        highest_point_in_vision = 0.0
        highest_scoring_point = (0.0, 0.0)
        longest_distance_to_bane = 0.0

        for row in range(self.map_y_size):
            for col in range(self.map_x_size):
                if vision_mask[row][col]:
                    bane_dist_to_point = round(known_banes[0].distance_to(Point2((col, row))), 0)
                    if self.vismap_scores[row][col] >= highest_point_in_vision:
                        if bane_dist_to_point >= longest_distance_to_bane:
                            highest_point_in_vision = self.vismap_scores[row][col]
                            highest_scoring_point = (col, row)
                            longest_distance_to_bane = bane_dist_to_point
                        else:
                            highest_point_in_vision = self.vismap_scores[row][col]
                            highest_scoring_point = (col, row)

        flipped_point = (highest_scoring_point[0], -highest_scoring_point[1] + self.map_y_size)
        return Point2(flipped_point)

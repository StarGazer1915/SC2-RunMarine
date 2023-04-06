import numpy as np
import time
import sc2
from sc2.constants import BANELING, MARINE
from src.MarineAgent import MarineAgent


class GameBot(sc2.BotAI):
    def __init__(self):
        self.agent_dict = {}
        self.pathing_map = np.array([])
        self.map_y_size = 0.
        self.map_x_size = 0.
        self.action_matrix = np.array([[[3, 3], [1, 4]], [[4, 1], [2, 2]]], dtype=np.float16)
        super().__init__()

    def on_start(self):
        """
        Defines variables and attributes when the environment is initialized.
        :return: void
        """
        self.pathing_map = self.game_info.pathing_grid.data_numpy.astype("float64")
        self.map_y_size = len(self.pathing_map)
        self.map_x_size = len(self.pathing_map[0])
        for agent in self.units.of_type(MARINE):
            self.agent_dict[str(agent.tag)] = MarineAgent(self.pathing_map, self.map_y_size, self.map_x_size)
        return super().on_start()

    def create_circular_mask(self, center=None, radius=None):
        """
        This function creates a circular mask around a given index in a multidimensional array.
        In this case it would be the StarCraft II map. It then returns this mask as a numpy array
        with boolean values (True = Mask). This is used to (for example) create 'vision masks'
        to determine the vision of a specific sc2 unit using the unit.sight_range attribute.
        :param center: tuple
        :param radius: int/float
        :return: numpy array
        """
        if center is None:  # use the middle
            center = (int(self.map_x_size / 2), int(self.map_y_size / 2))
        if radius is None:  # use the smallest distance between the center and map edges
            radius = min(center[0], center[1], self.map_x_size - center[0], self.map_y_size - center[1])

        Y, X = np.ogrid[:self.map_y_size, :self.map_x_size]
        dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)
        return dist_from_center <= radius

    def create_baneling_masks(self, known_banelings):
        """
        This function creates different masks (numpy arrays) with different ranges for the banelings in
        the current vision (known banelings) and stores them in a list which it then returns. This can then
        be used to apply the "Sphere of Fear" (SOF) around the baneling. See apply_baneling_sof() in MarineAgent.py
        :param known_banelings: list of sc2 units
        :return: list of masks
        """
        mask_list = []
        for bane in known_banelings:
            pos = bane.position.rounded
            b_sight_range = bane.sight_range  # default is 8.0
            bmask1 = np.flip(self.create_circular_mask(pos, b_sight_range - 6.0), 0)
            bmask2 = np.flip(self.create_circular_mask(pos, b_sight_range - 2.5), 0)
            bmask3 = np.flip(self.create_circular_mask(pos, b_sight_range), 0)
            mask_list.append([bmask1, bmask2, bmask3])

        return mask_list

    async def on_step(self, iteration):
        """
        This function executes the perception and actions of the agents inside the simulation (every step).
        :param iteration: iteration (sc2)
        """
        baneling_list = [unit for unit in self.known_enemy_units if unit.name == "Baneling"]
        for agent in self.units.of_type(MARINE):
            # Update agent variables
            tag = str(agent.tag)
            self.agent_dict[tag].position = agent.position

            # Start behavior process
            score_mask = np.flip(self.create_circular_mask(agent.position, agent.sight_range), 0)
            self.agent_dict[tag].percept_environment(score_mask)
            visible_banes = [b for b in baneling_list if \
                             score_mask[(-b.position.rounded[1] + self.map_y_size)][b.position.rounded[0]]]

            if len(visible_banes) > 0:
                self.agent_dict[tag].apply_baneling_sof(self.create_baneling_masks(visible_banes))
                time.sleep(0.01)
                await self.do(agent.move(self.agent_dict[tag].get_best_point(score_mask, visible_banes)))

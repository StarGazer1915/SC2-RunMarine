import matplotlib.pyplot as plt
import numpy as np
import time
import sc2
# from sc2.constants import BANELING, MARINE
from sc2.ids.unit_typeid import UnitTypeId
from src.MarineAgent import MarineAgent


class GameBot(sc2.BotAI):
    def __init__(self):
        self.agent_dict = {}
        self.pathing_map = np.array([])
        self.map_y_size = 0.
        self.map_x_size = 0.
        super().__init__()

    async def on_step(self, iteration):
        """
        This function executes the perception and actions of the agents inside the simulation (every step).
        :param iteration: iteration (sc2)
        """
        baneling_list = [unit for unit in self.known_enemy_units if unit.name == "Baneling"]
        for agent in self.units.of_type(UnitTypeId.MARINE):  # MARINE):
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

    def on_start(self):
        """
        Defines variables and attributes when the environment is initialized.
        :return: void
        """
        self.pathing_map = self.game_info.pathing_grid.data_numpy.astype("float64")
        self.map_y_size = len(self.pathing_map)
        self.map_x_size = len(self.pathing_map[0])
        for agent in self.units.of_type(UnitTypeId.MARINE):  # MARINE):
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

    @staticmethod
    def get_coordinates_middlepoint(y, x, boxes):
        coordinates = []
        for i in range(int(y // (boxes * 2)), y, int(y // boxes)):
            coordinates.append((i, int(x // 2)))
        return coordinates

    def plot_centerpoints(self):
        boxes = 4
        y = self.map_y_size
        x = self.map_x_size
        coordinates = self.get_coordinates_middlepoint(y, x, boxes)
        # Create a new figure and axis
        fig, ax = plt.subplots()
        # Set the aspect ratio to equal
        ax.set_aspect('equal')
        # Set the limits of the axis
        ax.set_ylim(0, y)
        ax.set_xlim(0, x)
        step = int(y / boxes)
        y_ticks = [i for i in range(0, y, step)] + [y]
        x_ticks = [i for i in range(0, x, int(step // 2))] + [x]
        ax.set_yticks(y_ticks)
        ax.set_xticks(x_ticks)
        y_scatter = [i[0] for i in coordinates]
        x_scatter = [i[1] for i in coordinates]
        plt.scatter(x_scatter, y_scatter, s=5, c='r', label='middenpunt')
        for i in range(1, boxes):
            if i == 1:
                plt.axhline(y=i * step, linestyle='-', color='black', label='scheidingswand')
            else:
                plt.axhline(y=i * step, linestyle='-', color='black')
        # Set the axis labels and title
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title('middenpunt van agents', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(3, 1))
        fig1 = plt.gcf()
        # plt.show()
        plt.draw()
        fig1.savefig('coordinates_middlepoint.png', dpi=720)
    plot_centerpoints()

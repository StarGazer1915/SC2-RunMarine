import time
import numpy as np
import pandas as pd
from datetime import datetime
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
        self.history = pd.DataFrame()  # remember desired information
        super().__init__()

    def on_start(self):
        """
        Defines variables and attributes when the environment is initialized.
        :return: void
        """
        self.pathing_map = self.game_info.pathing_grid.data_numpy.astype("float64")
        self.map_y_size = len(self.pathing_map)
        self.map_x_size = len(self.pathing_map[0])
        for agent in self.units.of_type(UnitTypeId.MARINE):  #MARINE):
            self.agent_dict[str(agent.tag)] = MarineAgent(self.pathing_map, self.map_y_size, self.map_x_size)
        return super().on_start()


    # ==================== MASKING FUNCTIONS ==================== #
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
        the current vision (known banelings) and stores them in a list which it then returns.
        :param known_banelings: list of sc2 units
        :return: list of masks
        """
        mask_list = []
        for bane in known_banelings:
            pos = bane.position.rounded
            b_sight_range = bane.sight_range  # default 8.0
            bmask1 = np.flip(self.create_circular_mask(pos, b_sight_range-4.0), 0)
            bmask2 = np.flip(self.create_circular_mask(pos, b_sight_range-2.0), 0)
            bmask3 = np.flip(self.create_circular_mask(pos, b_sight_range), 0)
            mask_list.append([bmask1, bmask2, bmask3])

        return mask_list

    # ==================== STEP FUNCTION ==================== #
    async def on_step(self, iteration):
        """
        Function step by step:
        1. Get the updated vision map and all known banelings that the bot sees on the map
        2. For each agent (marine):
            2.1 Create the agent's scoremask, make the agent percept the environment and list the banelings in vision.
            2.2 If there is a baneling in the agent's current vision:
                2.2.1 Apply the baneling 'Sphere Of Fear (sof)' for each baneling in known_banes (agent vision).
                2.2.2 Make the agent think of, and move to, the next best possible position.

        :param iteration: iteration (sc2)
        """
        baneling_list = [unit for unit in self.known_enemy_units if unit.name == "Baneling"]

        if True == False:
            for agent in self.units.of_type(self.units.of_type(UnitTypeId.MARINE)):  #MARINE):
                tag = str(agent.tag)
                score_mask = np.flip(self.create_circular_mask(agent.position, agent.sight_range), 0)
                self.agent_dict[tag].position = agent.position
                self.agent_dict[tag].percept_environment(score_mask)
                known_banes = [b for b in baneling_list if score_mask[b.position.rounded[1]][b.position.rounded[0]]]
                if len(known_banes) > 0:
                    self.agent_dict[tag].apply_baneling_sof(self.create_baneling_masks(known_banes))
                    time.sleep(0.05)
                    movement_mask = np.flip(self.create_circular_mask(agent.position, agent.sight_range), 0)
                    await self.do(agent.move(self.agent_dict[tag].take_action(movement_mask, known_banes)))

        if True == True:
            # itereer sc2.units.tag en src.GameBot-classobject
            for tag, agent in self.agent_dict.items():
                # creeer apparte pointer voor alle agents
                marine = self.agent_pointer(int(tag))
                # TODO: afvangen prisoners dillema
                if len(self.known_enemy_units) > 0:
                    # seleceer vijand
                    baneling = self.known_enemy_units[0]
                    # val vijand aan
                    await self.do(marine.attack(baneling))

    def agent_pointer(self, tag):
        """pointer naar een agent"""
        return self.units.find_by_tag(tag)

    def history_to_excel(self, new):
        """schrijf gewenste informatie over het spel per iteratie weg naar een excel bestand"""
        # concateneer bestaande history met nieuwe historie
        self.history = pd.concat([self.history, pd.DataFrame(new)], axis=0)
        # sla op als excel bestand
        self.history.to_excel(f"array_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", index=False)
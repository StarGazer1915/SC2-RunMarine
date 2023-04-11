import sys
import numpy as np
import time
import json
from random import choice
import sc2
import pandas as pd
# from sc2.constants import BANELING, MARINE
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from src.MarineAgent import MarineAgent
from datetime import datetime


class GameBot(sc2.BotAI):
    def __init__(self, action_matrix, epoch: int):
        self.square_info_dictionaries = []
        self.agent_dict = {}
        self.pathing_map = np.array([])
        self.map_y_size = 0.
        self.map_x_size = 0.
        self.epoch = epoch
        self.action_matrix = action_matrix
        self.marine_type_combinations = [["runner", "rational"], ["rational", "runner"], ["attacker", "rational"],
                                         ["rational", "attacker"], ["rational", "greedy"], ["greedy", "rational"],
                                         ["rational", "rational"], ["runner", "greedy"], ["greedy", "runner"],
                                         ["attacker", "greedy"], ["greedy", "attacker"], ["greedy", "greedy"]]
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
        type_combinations = self.marine_type_combinations

        # Define all agents in the current environment
        for agent in self.units.of_type(UnitTypeId.MARINE):  #MARINE):
            self.agent_dict[str(agent.tag)] = MarineAgent(self.pathing_map, self.map_y_size, self.map_x_size, agent.tag)

        # Define the combinations of agent 'personalities' / types and assign them
        self.define_square_trios()
        for d in self.square_info_dictionaries:
            type_combination = choice(type_combinations)
            self.agent_dict[str(d[f"marine1"])].atype = type_combination[0]
            self.agent_dict[str(d[f"marine2"])].atype = type_combination[1]
            type_combinations.pop(type_combinations.index(type_combination))

        # Define what actions the agents are going to take based on their 'personality' / type
        for tag in self.agent_dict:
            self.agent_dict[tag].take_action_from_action_matrix(self.action_matrix)

        return super().on_start()

    def update_action_matrix(self):
        """
        Update the global action_matrix with all the scores of the marineAgents from this iteration.
        :return: void
        """
        for agent in self.agent_dict.values():
            if agent.atype == "rational":
                m1_score = agent.performance_score
                m2_score = self.agent_dict[str(agent.partner_agent_tag)].performance_score

                m1_action = agent.chosen_action
                m2_action = self.agent_dict[str(agent.partner_agent_tag)].chosen_action

                # Update the action matrix with the new scores
                old_payoffs = self.action_matrix["Scores"][m1_action][m2_action]
                n0, n1 = self.action_matrix["Counts"][m1_action][m2_action]  # number of counts so far

                # Calculate running average
                if n0 != 0 and n1 != 0:
                    new_payoffs = (
                        (old_payoffs[0] * n0 + m1_score) / (n0 + 1),
                        (old_payoffs[1] * n1 + m2_score) / (n1 + 1)
                    )
                else:
                    new_payoffs = (m1_score, m2_score)

                # Replace the old values
                self.action_matrix["Scores"][m1_action][m2_action] = new_payoffs
                self.action_matrix["Counts"][m1_action][m2_action] = (n0+1, n1+1)

        self.save_action_matrix_to_file()

    def save_action_matrix_to_file(self, file="action_matrix.json"):
        """
        This function saves the current action_matrix to a .json file.
        :param file: string
        :return: void
        """
        with open(file, "w") as f:
            json.dump(self.action_matrix, f)

    def save_agent_data(self):
        with open("agent_data.csv", "a") as data_file:
            for agent in self.agent_dict.values():
                data_file.write(f"{agent.tag};{agent.atype};{agent.chosen_action};{agent.performance_score};{self.epoch}\n")

    def create_circular_mask(self, center=None, radius=None):
        """
        This function creates a circular mask around a given index in a multidimensional array.
        In this case it will be in the StarCraft II map. It then returns this mask as a numpy array
        with boolean values (True = Mask). This is used (for example) to create 'vision masks'
        to determine the vision of a specific sc2 unit using the unit.sight_range attribute.
        :param center: tuple
        :param radius: int/float
        :return: numpy array (booleans)
        """
        if center is None:  # use the middle
            center = (int(self.map_x_size / 2), int(self.map_y_size / 2))
        if radius is None:  # use the smallest distance between the center and map edges
            radius = min(center[0], center[1], self.map_x_size - center[0], self.map_y_size - center[1])

        Y, X = np.ogrid[:self.map_y_size, :self.map_x_size]
        dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)
        return dist_from_center <= radius

    def define_square_trios(self):
        """
        This function defines what marines are next to each other and which baneling is near them. It stores
        this in a list of dictionaries to be used in other functions.
        :return: void
        """
        for enemy in self.known_enemy_units:
            baneling_tag = enemy.tag
            enemy_position = enemy.position
            m1_tag = self.units.sorted_by_distance_to(Point2(enemy_position))[0].tag
            m2_tag = self.units.sorted_by_distance_to(Point2(enemy_position))[1].tag

            # define partner agents so the matrix can be updated correctly
            self.agent_dict[str(m1_tag)].partner_agent_tag = m2_tag
            self.agent_dict[str(m2_tag)].partner_agent_tag = m1_tag

            # append the square info to the global value for easy access
            self.square_info_dictionaries.append({
                "marine1": m1_tag,
                "marine2": m2_tag,
                "baneling_tag": baneling_tag})

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

    def give_scores(self, last_step = False):
        """
        This function updates the scores of agents based on their performance.
        :param last_step: boolean
        :return: void
        """
        for square_info in self.square_info_dictionaries:
            m1_tag = square_info["marine1"]
            m2_tag = square_info["marine2"]
            banetag = square_info["baneling_tag"]
            state = self.check_square_state(m1_tag, m2_tag, banetag)

            # Give points for being alive
            if state[0]:
                self.agent_dict[f"{m1_tag}"].performance_score += 0.5

            if state[1]:
                self.agent_dict[f"{m2_tag}"].performance_score += 0.5

            if last_step:
                # Hand out points for living (+), dying (-) and killing the baneling (++)
                if state[0]:
                    self.agent_dict[f"{m1_tag}"].performance_score += 2
                else:
                    self.agent_dict[f"{m1_tag}"].performance_score -= 2

                if state[1]:
                    self.agent_dict[f"{m2_tag}"].performance_score += 2
                else:
                    self.agent_dict[f"{m2_tag}"].performance_score -= 2

                if not state[2] and self.agent_dict[f"{m1_tag}"].chosen_action == "Attack" \
                        and self.agent_dict[f"{m2_tag}"].chosen_action == "Attack":
                    self.agent_dict[f"{m1_tag}"].performance_score += 4
                    self.agent_dict[f"{m2_tag}"].performance_score += 4


    def check_square_state(self, m1_tag, m2_tag, b_tag):
        """
        This function returns a list with ones and zero (like [1,0,1]) a one represents alive and a zero represents
        the unit being dead. So in the example of the list [1,1,1] both marines and the baneling of a sqaure are alive.
        In the list [1,0,0] only marine 1 is alive and both marine 2 and the baneling are dead.
        :param m1_tag: int
        :param m2_tag: int
        :param b_tag: int
        :return: list
        """
        return [self.unit_is_alive(m1_tag), self.unit_is_alive(m2_tag), self.unit_is_alive(b_tag)]

    def unit_is_alive(self, unit_tag):
        """
        This function checks if a given unit is alive. And returns 0 if the unit is dead and 1 if the unit is alive.
        :param unit_tag: int
        :return: int
        """
        if self.state.units.find_by_tag(unit_tag) is None:
            return 0
        else:
            return 1

    async def on_step(self, iteration):
        """
        This function executes the perception and actions of the agents inside the simulation (every step).
        :param iteration: iteration (sc2)
        """
        if self.time <= 12:
            self.history_to_excel(next(iter(self.agent_dict.values())).vismap_scores)
            baneling_list = [unit for unit in self.known_enemy_units if unit.name == "Baneling"]
            for agent in self.units.of_type(UnitTypeId.MARINE):  #MARINE):
                # ========== Update agent variables ========== #
                tag = str(agent.tag)
                self.agent_dict[tag].position = agent.position

                # ========== Start behaviour process ========== #
                score_mask = np.flip(self.create_circular_mask(agent.position, agent.sight_range), 0)
                self.agent_dict[tag].percept_environment(score_mask)
                visible_banes = [b for b in baneling_list if \
                                 score_mask[(-b.position.rounded[1] + self.map_y_size)][b.position.rounded[0]]]

                time.sleep(0.01)  # Delay to save performance
                if len(visible_banes) > 0:
                    # ========== Execute actions ========== #
                    self.agent_dict[tag].apply_baneling_sof(self.create_baneling_masks(visible_banes))
                    if self.agent_dict[tag].chosen_action == "Attack":
                        await self.do(agent.attack(visible_banes[0]))
                    else:
                        await self.do(agent.move(self.agent_dict[tag].get_best_point(score_mask, visible_banes)))

            self.give_scores()
        else:
            self.give_scores(True)
            self.update_action_matrix()
            self.save_agent_data()
            self.save_action_matrix_to_file()

         

            await self._client.leave()

    def history_to_excel(self, new):
        """schrijf gewenste informatie over het spel per iteratie weg naar een excel bestand"""
        # concateneer bestaande history met nieuwe historie
        self.history = pd.concat([self.history, pd.DataFrame(new)], axis=0)
        # sla op als excel bestand
        self.history.to_excel(f"array_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", index=False)
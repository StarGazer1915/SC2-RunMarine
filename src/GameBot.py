import numpy as np
import time
import json
from random import choice
import sc2
import pandas as pd
from sc2.constants import BANELING, MARINE
from matplotlib import pyplot as plt
# from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from datetime import datetime

from src.MarineAgent import MarineAgent


class GameBot(sc2.BotAI):
    def __init__(self, action_matrix, epoch: int):
        self.square_info_dictionaries = []
        # agent-class-object; key=refferencenumber towards sc.units.unit, value= agent-class-object MarineAgent()
        self.agent_dict = {}
        self.pathing_map = np.array([])
        # y and x coordinates for vision of agent.
        # note that the order in sc2 differce
        self.map_y_size, self.map_x_size = 0., 0.
        self.epoch = epoch
        self.action_matrix = action_matrix
        # possible acction combinations of agent and partner_agent
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
        self.map_y_size, self.map_x_size = self.pathing_map.shape
        type_combinations = self.marine_type_combinations

        # iterate all avvailble marine agents
        for unit in self.units:
            # Define all agents in the current environment
            self.agent_dict[str(unit.tag)] = MarineAgent(self.pathing_map, self.map_y_size, self.map_x_size, unit.tag)

        # Define the combinations of agent 'personalities' / types and assign them
        self.define_square_trios()
        # iterate possible actions
        for d in self.square_info_dictionaries:
            # pick action
            type_combination = choice(type_combinations)
            # define action in agent-class
            self.agent_dict[str(d[f"marine1"])].atype = type_combination[0]
            self.agent_dict[str(d[f"marine2"])].atype = type_combination[1]
            # drop used combination
            type_combinations.pop(type_combinations.index(type_combination))

        # iterate tags of all known actions/
        for tag in self.agent_dict:
            # Define what actions the agents are going to take based on their 'personality' / type
            self.agent_dict[tag].take_action_from_action_matrix(self.action_matrix)

        return super().on_start()

    def update_action_matrix(self):
        """
        Update the global action_matrix with all the scores of the marineAgents from this iteration.
        :return: void
        """
        # iterate aggents
        for agent in self.agent_dict.values():
            # if agent is rational
            if agent.atype == "rational":
                # get performance score
                marine_score = agent.performance_score
                marine_partner_score = self.agent_dict[str(agent.partner_agent_tag)].performance_score
                # get next action
                marine_action = agent.chosen_action
                marine_partner_action = self.agent_dict[str(agent.partner_agent_tag)].chosen_action
                # Update the action matrix with the new scores
                old_payoffs = self.action_matrix["Scores"][marine_action][marine_partner_action]
                n0, n1 = self.action_matrix["Counts"][marine_action][marine_partner_action]  # number of counts so far
                # Calculate running average
                if n0 != 0 and n1 != 0:
                    new_payoffs = (
                        (old_payoffs[0] * n0 + marine_score) / (n0 + 1),
                        (old_payoffs[1] * n1 + marine_partner_score) / (n1 + 1)
                    )
                else:
                    new_payoffs = (marine_score, marine_partner_score)
                # Replace the old values
                self.action_matrix["Scores"][marine_action][marine_partner_action] = new_payoffs
                self.action_matrix["Counts"][marine_action][marine_partner_action] = (n0 + 1, n1 + 1)
        # save newly updated action matrix
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
                data_file.write(
                    f"{agent.tag};{agent.atype};{agent.chosen_action};{agent.performance_score};{self.epoch}\n")

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
            marine_tag = self.units.sorted_by_distance_to(Point2(enemy_position))[0].tag
            marine_partner_tag = self.units.sorted_by_distance_to(Point2(enemy_position))[1].tag

            # define partner agents so the matrix can be updated correctly
            self.agent_dict[str(marine_tag)].partner_agent_tag = marine_partner_tag
            self.agent_dict[str(marine_partner_tag)].partner_agent_tag = marine_tag

            # append the square info to the global value for easy access
            self.square_info_dictionaries.append({
                "marine1": marine_tag,
                "marine2": marine_partner_tag,
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

    def give_scores(self, last_step=False):
        """
        This function updates the scores of agents based on their performance.
        :param last_step: boolean
        :return: void
        """
        for square_info in self.square_info_dictionaries:
            marine_tag = square_info["marine1"]
            marine_partner_tag = square_info["marine2"]
            banetag = square_info["baneling_tag"]
            state = self.check_square_state(marine_tag, marine_partner_tag, banetag)
            marine_agent = self.agent_dict[f"{marine_tag}"]
            partner_agent = self.agent_dict[f"{marine_partner_tag}"]
            # Give points for being alive
            if state[0]: marine_agent.performance_score += 0.5
            if state[1]: partner_agent.performance_score += 0.5
            if last_step:
                # Hand out points for living (+), dying (-) and killing the baneling (++)
                marine_agent.performance_score += 2 if state[0] else -2
                partner_agent.performance_score += 2 if state[1] else -2
            if not state[2] and marine_agent.chosen_action == "Attack" \
                    and partner_agent.chosen_action == "Attack":
                marine_agent.performance_score += 4
                partner_agent.performance_score += 4

    def check_square_state(self, marine_tag, marine_partner_tag, b_tag):
        """
        This function returns a list with ones and zero (like [1,0,1]) a one represents alive and a zero represents
        the unit being dead. So in the example of the list [1,1,1] both marines and the baneling of a sqaure are alive.
        In the list [1,0,0] only marine 1 is alive and both marine 2 and the baneling are dead.
        :param marine_tag: int
        :param marine_partner_tag: int
        :param b_tag: int
        :return: list
        """
        # return list of booleans which identifies which object are not active annymore
        return [self.unit_is_alive(marine_tag), self.unit_is_alive(marine_partner_tag), self.unit_is_alive(b_tag)]

    def unit_is_alive(self, unit_tag):
        """
        This function checks if a given unit is alive. And returns 0 if the unit is dead and 1 if the unit is alive.
        :param unit_tag: int
        :return: int
        """
        # check if agent is still alive
        if self.state.units.find_by_tag(unit_tag) is None:
            return 0
        return 1

    async def on_step(self, iteration):
        """
        This function executes the perception and actions of the agents inside the simulation (every step).
        :param iteration: iteration (sc2)
        """
        # as long as the possible epoch-duration is active
        if self.time <= 12:
            # save vismap_scores to history file
            # get list of enemys within vision of agents
            baneling_list = [unit for unit in self.known_enemy_units if unit.name == "Baneling"]
            # iterate agents
            for agent in self.units.of_type(MARINE):  #  UnitTypeId.MARINE):
                # ========== Update agent variables ========== #
                tag = str(agent.tag)
                self.agent_dict[tag].position = agent.position

                # ========== Start behaviour process ========== #
                score_mask = np.flip(self.create_circular_mask(agent.position, agent.sight_range), 0)
                self.agent_dict[tag].percept_environment(score_mask)
                visible_banes = [b for b in baneling_list if \
                                 score_mask[(-b.position.rounded[1] + self.map_y_size)][b.position.rounded[0]]]
                time.sleep(0.01)  # Delay to save performance
                # if enemys are visible
                if len(visible_banes) > 0:
                    # ========== Execute actions ========== #
                    self.agent_dict[tag].apply_baneling_sof(self.create_baneling_masks(visible_banes))
                    # check is agent would attack
                    if self.agent_dict[tag].chosen_action == "Attack":
                        # attack enemy
                        await self.do(agent.attack(visible_banes[0]))
                    else:
                        # go towards best position within vision
                        await self.do(agent.move(self.agent_dict[tag].get_best_point(score_mask, visible_banes)))

            # assign scores based on the outcome of epoch
            self.give_scores()
        else:
            # assign scores based on the outcome of epoch
            self.give_scores(True)
            # update matrix
            self.update_action_matrix()
            self.save_agent_data()
            # save localy
            self.save_action_matrix_to_file()
            await self._client.leave()

    def history_to_excel(self, new):
        """schrijf gewenste informatie over het spel per iteratie weg naar een excel bestand"""
        # concateneer bestaande history met nieuwe historie
        self.history = pd.concat([self.history, pd.DataFrame(new)], axis=0)
        # sla op als excel bestand
        self.history.to_excel(f"array_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", index=False)

    def get_coordinates_middlepoint(self):
        """
        bereken middenpunt van iedere killbox.
        lijst van tuples bestaande uit de coordinaten welk de middenpunten representeren.
        """
        boxes = 4
        y, x = self.map_y_size, self.map_x_size
        coordinates = []
        for i in range(int(y // (boxes * 2)), y, int(y // boxes)):
            coordinates.append((i, int(x // 2)))
        return coordinates

    def plot_centerpoints(self):
        """
        visualiseer middenpunten om te controleren of de agents juist kunnen worden gegroepeerd.
        """
        boxes = 4
        y = self.map_y_size
        x = self.map_x_size
        coordinates = self.get_coordinates_middlepoint()
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

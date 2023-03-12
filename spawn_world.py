import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import BANELING, MARINE
from sc2.position import Point2
import time
import pygame
import numpy as np


class MarineBot(sc2.BotAI):
    def __init__(self):
        self.use_viz = False
        self.vismap_stored = False
        self.vismap_scores = np.array([])
        self.valid_threshold = 0.5
        self.pathing_map = np.array([])
        self.map_y_size = 0
        self.map_x_size = 0
        super().__init__()

    def on_start(self):
        self.init_window()
        updated_map = self.state.visibility.data_numpy.copy().astype("float64")
        self.pathing_map = self.game_info.pathing_grid.data_numpy.copy().astype("float64")
        self.map_y_size = len(updated_map)
        self.map_x_size = len(updated_map[0])
        return super().on_start()

    def init_window(self):
        pygame.init()
        self.display = pygame.display
        self.screen = self.display.set_mode((640, 480))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Agent Viewer")
        self.use_viz = True

    def create_circular_mask(self, h, w, center=None, radius=None):
        if center is None:  # use the middle
            center = (int(w / 2), int(h / 2))
        if radius is None:  # use the smallest distance between the center and map edges
            radius = min(center[0], center[1], w - center[0], h - center[1])

        Y, X = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)

        mask = dist_from_center <= radius
        return mask

    def pad_with(self, array, pad_width, iaxis, kwargs):
        array[:pad_width[0]] = kwargs.get('padder', 10)
        array[-pad_width[1]:] = kwargs.get('padder', 10)

    def n_closest(self, x, n, d=2):
        return x[n[0] - d:n[0] + d + 1, n[1] - d:n[1] + d + 1]

    def store_or_pad(self, vismap, pad_value):
        """
        Function that stores the initial vision map of the marine into the class attribute
        self.vismap_scores (numpy array) which will serve as the agent's memory.
        If the agent already has a memory then it will pad the current vismap and return it.
        The pad_with() function is used for adding the padding.
        :param vismap: array
        :return: padded array
        """
        if not self.vismap_stored:
            self.vismap_scores = vismap.astype("float64")
            self.vismap_stored = True
        else:
            return np.pad(vismap, 2, self.pad_with, padder=pad_value)


    async def on_step(self, iteration):
        updated_map = self.state.visibility.data_numpy.copy().astype("float64")
        # updated_map[updated_map == 0.] = 2.
        for marine in self.units.of_type(MARINE):
            mmask = np.flip(self.create_circular_mask(self.map_y_size, self.map_x_size,
                                                      marine.position, marine.sight_range), 0)

            await self.generate_scores(updated_map, mmask)
            # await self.baneling_radar(mmask)
            # await self.run_away(marine, mmask)

            if self.use_viz:
                await self.update_viewer()

        # print(f"========== self.vismap_scores: ==========")
        # for y in self.vismap_scores:
        #     line = ""
        #     for x in y:
        #         line += f"{x} | "
        #     print(line)
        # print("\n\n")

        self.state.visibility.plot()

    async def generate_scores(self, updated_map, mmask):
        """
        This function generates scores for the terrain that the marine is currently viewing. It first gets and pads
        the current visionmap and then proceeds to look in a 5x5 range around the current index (with the current
        value in the middle of the 5x5 grid). Note that the function only generates scores for valid terrain that
        the marine sees (so not for impassible (0.0) terrain). This area (5x5 array grid) of values is then checked
        on viable positions based on if the values are higher than the valid_threshold attribute (float). Also note
        that the vismap always gives a score of 2 for passable terrain. If that is the case then all these valid
        points are gathered and the score is calculated based on how many of the 25 possible points are valid
        (So 11 valid points out of 25 is 0.44 for example). This score then replaces the value in the
        self.vismap_scores attribute (Memory) on the correct index.
        :param updated_map:
        :param mmask:
        :return: void
        """
        for y1 in range(self.map_y_size):
            for x1 in range(self.map_x_size):
                if updated_map[y1][x1] in [1.0, 2.0] and self.pathing_map[y1][x1] == 0.0:
                    if mmask[y1][x1]:
                        updated_map[y1][x1] = 0.0
                        if self.vismap_stored:
                            self.vismap_scores[y1][x1] = 0.0

        vismap_padded = self.store_or_pad(updated_map, 0.)
        if vismap_padded is not None:
            for y2 in range(self.map_y_size):
                for x2 in range(self.map_x_size):
                    if updated_map[y2][x2] != 0.0 and self.pathing_map[y2][x2] != 0.0:
                        if mmask[y2][x2]:
                            area = self.n_closest(vismap_padded, (y2 + 2, x2 + 2), d=2).copy()
                            area[area > self.valid_threshold] = 1
                            area[area <= self.valid_threshold] = 0
                            score = round(sum(area.flatten()) / (len(area) * len(area[0])), 2)
                            self.vismap_scores[y2][x2] = score
                    else:
                        if mmask[y2][x2]:
                            self.vismap_scores[y2][x2] = 0.0

    async def baneling_radar(self, mmask):
        enemy_units = self.known_enemy_units
        if len(enemy_units) > 0:
            for unit in enemy_units:
                if unit.name == "Baneling":
                    pos = unit.position.rounded
                    b_sight_range = unit.sight_range  # 8.0
                    bmask1 = np.flip(
                        self.create_circular_mask(self.map_y_size, self.map_x_size, pos, b_sight_range-5.0), 0)
                    bmask2 = np.flip(
                        self.create_circular_mask(self.map_y_size, self.map_x_size, pos, b_sight_range-2.0), 0)
                    # bmask3 = np.flip(
                    #     self.create_circular_mask(self.map_y_size, self.map_x_size, pos, b_sight_range)+1.0, 0)
                    # bmask4 = np.flip(
                    #     self.create_circular_mask(self.map_y_size, self.map_x_size, pos, b_sight_range+4.0), 0)

                    """WIP: The 2 lines below still need to only be applied to points in marine vision only"""
                    # self.vismap_scores[np.where((bmask4 == True) & (mmask == True))] *= 1.0
                    # self.vismap_scores[np.where((bmask3 == True) & (mmask == True))] *= 1.0
                    self.vismap_scores[(bmask2 == True) & (mmask == True)] *= 0.6
                    self.vismap_scores[(bmask1 == True) & (mmask == True)] *= 0.1
                    self.vismap_scores = np.around(self.vismap_scores, 2)

    async def run_away(self, marine, mmask):
        enemy_units = self.known_enemy_units
        if len(enemy_units) > 0:
            for unit in enemy_units:
                if unit.name == "Baneling":
                    highest_coor_in_vision = 0.0
                    highest_scoring_coor = (0.0, 0.0)
                    longest_distance_to_bane = 0.0

                    for row in range(self.map_y_size):
                        for col in range(self.map_x_size):
                            if mmask[row][col]:
                                if self.vismap_scores[row][col] > highest_coor_in_vision:
                                    if round(unit.distance_to(Point2((col, row))), 2) > longest_distance_to_bane:
                                        highest_coor_in_vision = self.vismap_scores[row][col]
                                        highest_scoring_coor = (col, (-row + 32))
                                        longest_distance_to_bane = round(unit.distance_to(Point2((col, row))), 2)
                                    else:
                                        highest_coor_in_vision = self.vismap_scores[row][col]
                                        highest_scoring_coor = (col, (-row + 32))

                    print(f"Point: {highest_coor_in_vision},\n"
                          f"highest_scoring_coor: {highest_scoring_coor},\n"
                          f"Baneling Position: {unit.position}, \n"
                          f"Longest distance to baneling: {longest_distance_to_bane},\n"
                          f"Marine Position: {marine.position}\n")

                    await self.do(marine.move(Point2(highest_scoring_coor)))

        # print(f"========== self.vismap_scores: ==========")
        # for y in self.vismap_scores:
        #     line = ""
        #     for x in y:
        #         line += f"{x} | "
        #     print(line)
        # print("\n\n")

    async def update_viewer(self):
        vis_data = self.state.visibility.data_numpy
        creep_data = self.state.creep.data_numpy
        movegrid_data = np.flip(self.game_info.pathing_grid.data_numpy, 0)
        merge_data = vis_data + movegrid_data

        vis_surf = pygame.surfarray.make_surface(vis_data)
        movegrid_surf = pygame.surfarray.make_surface(movegrid_data)
        merge_surf = pygame.surfarray.make_surface(merge_data)
        creep_surf = pygame.surfarray.make_surface(creep_data)

        self.screen.blit(vis_surf, (0, 0))
        self.screen.blit(movegrid_surf, (200, 0))
        self.screen.blit(creep_surf, (0, 210))
        self.screen.blit(merge_surf, (200, 210))

        pygame.display.update()

# marine_vs_baneling_advanced
# marine_vs_baneling_advanced_noEnemyAI
# marine_vs_baneling_advanced_NoOverlord
run_game(maps.get("marine_vs_baneling_advanced_noEnemyAI"),
         [
             Bot(Race.Terran, MarineBot()),
             Computer(Race.Zerg, Difficulty.Hard)
         ], realtime=True)

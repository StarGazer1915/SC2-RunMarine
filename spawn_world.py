from heapq import merge
from shutil import move
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SCV, MARINE
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
import pygame
import numpy as np


class MarineBot(sc2.BotAI):
    def __init__(self):
        self.use_viz = False
        self.vismap_stored = False
        self.vismap_scores = np.array([])
        self.valid_threshold = 0.5
        super().__init__()


    def on_start(self):
        self.init_window()

        # enemy_location = self.enemy_start_locations
        # print(f"Enemy start locations:\n{enemy_location}\n")
        #
        # self.worker = self.workers[0]
        # self.worker_tag = self.worker.tag
        #
        # print(f"Worker info:\n{self.worker}")
        # print(f"Worker location: {self.worker.position}\n")
        # print(f"Center of map at: {self.game_info.map_center}")

        return super().on_start()


    def init_window(self):
        pygame.init()

        self.display = pygame.display
        self.screen = self.display.set_mode((640, 480))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Agent Viewer")

        self.use_viz = True


    def store_or_pad(self, vismap):
        """
        Function that stores the initial vision map of the marine into the class attribute
        self.vismap_scores (numpy array) which will serve as the agent's memory.
        If the agent already has a memory then it will pad the current vismap and return it.
        The pad_with() function is used for adding the padding.
        :param vismap: array
        :return: padded array
        """
        def pad_with(array, pad_width, iaxis, kwargs):
            array[:pad_width[0]] = kwargs.get('padder', 10)
            array[-pad_width[1]:] = kwargs.get('padder', 10)

        if not self.vismap_stored:
            self.vismap_scores = vismap.astype("float64")
            # self.vismap_scores[self.vismap_scores == 0.0] = 2.0
            self.vismap_stored = True
        else:
            return np.pad(vismap, 2, pad_with, padder=2.)


    def generate_scores(self):
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
        :return: void
        """
        def n_closest(x, n, d=1):
            return x[n[0] - d:n[0] + d + 1, n[1] - d:n[1] + d + 1]

        updated_map = self.state.visibility.data_numpy.copy().astype("float64")
        # for a in updated_map:
        #     print(a)
        # print("\n\n")
        vismap_padded = self.store_or_pad(updated_map)

        if vismap_padded is not None:
            # for b in vismap_padded:
            #     print(b)
            # print("\n\n")
            for y in range(len(updated_map)):
                for x in range(len(updated_map[y])):
                    if updated_map[y][x] != 0.0:
                        area = n_closest(vismap_padded, (y + 2, x + 2), d=2)
                        area[area > self.valid_threshold] = 1
                        area[area <= self.valid_threshold] = 0
                        score = round(sum(area.flatten()) / (len(area) * len(area[0])), 2)
                        self.vismap_scores[y][x] = score

        for y in self.vismap_scores:
            line = ""
            for x in y:
                line += f"{x} | "
            print(line)
        print("\n\n")

    async def update_viewer(self):
        # Get the pixelMap Data
        vis_data = self.state.visibility.data_numpy
        creep_data = self.state.creep.data_numpy
        movegrid_data = np.flip(self.game_info.pathing_grid.data_numpy, 0)

        merge_data = vis_data + movegrid_data
        # print(f"Shape: {merge_data.shape}")

        # Turn them into a surface
        vis_surf = pygame.surfarray.make_surface(vis_data)
        movegrid_surf = pygame.surfarray.make_surface(movegrid_data)
        merge_surf = pygame.surfarray.make_surface(merge_data)
        creep_surf = pygame.surfarray.make_surface(creep_data)

        # and apply them to the screen
        self.screen.blit(vis_surf, (0, 0))
        self.screen.blit(movegrid_surf, (200, 0))
        self.screen.blit(creep_surf, (0, 210))
        self.screen.blit(merge_surf, (200, 210))

        # update display
        pygame.display.update()


    async def on_step(self, iteration):
        self.generate_scores()

        # await self.move_to_point()
        await self.look_for_enemy()

        # print(f"Unit Location: {self.workers[0].position}")

        # self.state.visibility.save_image("vis.png")
        self.state.visibility.plot()

        if self.use_viz:
            await self.update_viewer()


    async def move_to_point(self, unit_tag=None):
        marine = self.units.of_type({MARINE})
        await self.do(marine[0].move(Point2((20, 10))))


    async def do_something(self, tag):
        marine_id = self.units.find_by_tag(tag)
        if marine_id != None:
            await self.do(marine_id.move((0, 0)))
        else:
            print("Could not find unit to move")


    async def look_for_enemy(self):
        enemy_units = self.known_enemy_units
        # enemy_structures = self.known_enemy_structures

        if not len(enemy_units) > 0:
            return
        for unit in enemy_units:
            if unit.is_structure:
                print(f"Structure spotted at: {unit.position}")
            else:
                print(f"enemy spotted at: {unit.position}")


run_game(maps.get("marine_vs_baneling"),
         [
             Bot(Race.Terran, MarineBot()),
             Computer(Race.Zerg, Difficulty.Hard)
         ], realtime=True)

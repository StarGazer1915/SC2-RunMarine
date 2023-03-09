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
        super().__init__()

    def on_start(self):
        self.init_window()

        enemy_location = self.enemy_start_locations
        print(f"Enemy start locations:\n{enemy_location}\n")

        self.worker = self.workers[0]
        self.worker_tag = self.worker.tag

        print(f"Worker info:\n{self.worker}")
        print(f"Worker location: {self.worker.position}\n")
        print(f"Center of map at: {self.game_info.map_center}")

        return super().on_start()

    def init_window(self):
        pygame.init()

        self.display = pygame.display
        self.screen = self.display.set_mode((640, 480))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Agent Viewer")

        self.use_viz = True

    def update_position_scores(self):
        updated_map = self.state.visibility.data_numpy.copy()
        print(f"updated map | type: {updated_map.dtype}, length: ({len(updated_map[0])}, {len(updated_map)})")
        if not self.vismap_stored:
            self.vismap_scores = updated_map.astype("int64")
            self.vismap_stored = True

        for y in range(len(updated_map)):
            for x in range(len(updated_map[y])):
                if updated_map[y][x] == 2:
                    # CALCULATE SCORE AND REPLACE IN: self.vismap_scores
                    self.vismap_scores[y][x] = 999
                    pass

        print(f"vismap_scores | type: {self.vismap_scores.dtype}, "
              f"length: ({len(self.vismap_scores[0])}, {len(self.vismap_scores)})")

        for r in self.vismap_scores:
            print(r)

        self.state.visibility.plot()
        return

    async def update_viewer(self):
        # Get teh pixelMap Data
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
        # await self.distribute_workers()

        await self.move_workers()
        await self.look_for_enemy()

        self.update_position_scores()

        # print(f"Unit Location: {self.workers[0].position}")

        # self.state.visibility.save_image("vis.png")
        # self.state.visibility.plot()

        if self.use_viz:
            await self.update_viewer()

    async def move_workers(self, unit_tag=None):

        all_workers = self.workers
        for worker in all_workers:
            await self.do(worker.move(self.enemy_start_locations[0]))

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


run_game(maps.get("AbyssalReefLE"),
         [
             Bot(Race.Terran, MarineBot()),
             Computer(Race.Zerg, Difficulty.Hard)
         ], realtime=True)

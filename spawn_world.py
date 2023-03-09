from mimetypes import init
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SCV, MARINE
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
import pygame
import numpy as np

class MarineBot(sc2.BotAI):

    def on_start(self):
        self.use_viz = False
        # self.init_window()

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
        self.screen = pygame.display.set_mode((500, 500))
        self.screen.fill((0, 0, 0))
        self.use_viz = True
    

    async def on_step(self, iteration):
        # await self.distribute_workers()

        await self.move_workers()
        await self.look_for_enemy()

        print(f"Unit Location: {self.workers[0].position}")

        self.game_info.pathing_grid.plot()
        # self.state.creep.plot()
        if self.use_viz:
            pygame.display.flip()


    async def move_workers(self, unit_tag=None):

        all_workers = self.workers
        for worker in all_workers:
            await self.do(worker.move(self.game_info.map_center))

    async def do_something(self, tag):
        marine_id = self.units.find_by_tag(tag)
        if marine_id != None:
            await self.do(marine_id.move((0,0)))
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

    def get_visibility(self):
        vis_data = self.state.visibility.data_numpy


run_game(maps.get("AbyssalReefLE"),
[
    Bot(Race.Terran, MarineBot()),
    Computer(Race.Zerg, Difficulty.Hard)
], realtime=False)

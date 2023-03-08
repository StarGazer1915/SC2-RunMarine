import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SCV, MARINE


class MarineBot(sc2.BotAI):

    async def on_step(self, iteration):
        await self.distribute_workers()
        await self.move_to_enemy_base()

    async def move_to_enemy_base(self):
        all_workers = self.units(SCV)
        for worker in all_workers:
            await self.do(worker.move(self.enemy_start_locations[0]))


run_game(maps.get("AbyssalReefLE"),
[
    Bot(Race.Terran, MarineBot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=True)

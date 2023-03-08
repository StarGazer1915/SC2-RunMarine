import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
# from sc2.constants import COMMANDCENTER, SCV, MARINE
from sc2.ids.unit_typeid import UnitTypeId

class MarineBot(sc2.BotAI):

    async def on_step(self, iteration):
        await self.distribute_workers()
        await self.do_something()

        # await self.move_to_enemy_base()

    async def move_to_enemy_base(self):
        all_workers = self.units(UnitTypeId.SCV)
        for worker in all_workers:
            print(worker)
            await self.do(worker.move(self.enemy_start_locations[0]))
    async def do_something(self):
        marine_id = self.units.find_by_tag(1)
        await self.do(marine_id.move())


run_game(maps.get("single marine"),
[
    Bot(Race.Terran, MarineBot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=True)

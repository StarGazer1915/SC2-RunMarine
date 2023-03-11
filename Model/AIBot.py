import sc2
# from sc2 import run_game, maps, Race, Difficulty
# from sc2.player import Bot, Computer
# from sc2.position import Point2
# from sc2.ids.unit_typeid import UnitTypeId
# import numpy as np

class AIBot(sc2.BotAI):
    def __init__(self):
        super().__init__()
        # self.agent = Agent("Marine")

    def on_start(self):
        # self.agent.set_marine(self.units[0])
        return super().on_start()

    async def on_step(self, iteration: int):
        # if self.known_enemy_units != []:
            # self.agent.state = "Danger"
        pass

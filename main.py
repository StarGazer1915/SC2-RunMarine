from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
# from Model.AIBot import AIBot

if __name__ == "__main__":
    run_game(maps.get("marine_vs_baneling"),
             [Bot(Race.Protoss, AIBot()),
              Computer(Race.Zerg, Difficulty.Easy)],
             realtime=True)

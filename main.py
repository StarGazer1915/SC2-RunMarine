import numpy as np
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from src.GameBot import GameBot

action_matrix = np.array([[[3, 3], [1, 4]], [[4, 1], [2, 2]]], dtype=np.float16)
run_game(maps.get("marine_vs_baneling_advanced_NoOverlord_MultipleAgents"),
         [
             Bot(Race.Terran, GameBot(action_matrix)),
             Computer(Race.Zerg, Difficulty.Hard)
         ], realtime=True)

# Maps:
# marine_vs_baneling_advanced
# marine_vs_baneling_advanced_noEnemyAI
# marine_vs_baneling_advanced_NoOverlord
# marine_vs_baneling_advanced_NoOverlord_noCliff
# marine_vs_baneling_advanced_NoOverlord_MultipleAgents

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from src.GameBot import GameBot

run_game(maps.get("marine_vs_baneling"),
         [
             Bot(Race.Terran, GameBot()),
             Computer(Race.Zerg, Difficulty.VerryEasy)
         ], realtime=True)

# Maps:
# marine_vs_baneling_advanced
# marine_vs_baneling_advanced_noEnemyAI
# marine_vs_baneling_advanced_NoOverlord
# marine_vs_baneling_advanced_NoOverlord_noCliff

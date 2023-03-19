from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from gameBot import gameBot


def __init__():
    run_game(maps.get("marine_vs_baneling_advanced_NoOverlord"),
             [
                 Bot(Race.Terran, gameBot()),
                 Computer(Race.Zerg, Difficulty.Hard)
             ], realtime=True)

    # Maps:
    # marine_vs_baneling_advanced
    # marine_vs_baneling_advanced_noEnemyAI
    # marine_vs_baneling_advanced_NoOverlord
    # marine_vs_baneling_advanced_NoOverlord_noCliff
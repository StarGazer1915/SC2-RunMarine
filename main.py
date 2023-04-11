import json
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from src.GameBot import GameBot

for i in range(10):
    try:
        with open("action_matrix.json", "r") as f:
            action_matrix = json.load(f)
    except:
        with open("action_matrix_template.json", "r") as f:
            action_matrix = json.load(f)

    try:
        run_game(maps.get("12SquareMarinevsBaneling"),
                    [
                        Bot(Race.Terran, GameBot(action_matrix, i)),
                        Computer(Race.Zerg, Difficulty.Hard)
                    ], realtime=True)
    except Exception as err:
        print(f"Error while running game loop: {err}")



# ========== Maps ========== #
# - marine_vs_baneling_advanced
# - 12SquareMarinevsBaneling
# - marine_vs_baneling_advanced_noEnemyAI
# - marine_vs_baneling_advanced_NoOverlord
# - marine_vs_baneling_advanced_NoOverlord_noCliff
# - marine_vs_baneling_advanced_NoOverlord_MultipleAgents


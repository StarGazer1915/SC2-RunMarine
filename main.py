import json
import time

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from src.GameBot import GameBot

if __name__ == '__main__':
    # epochs/generations
    for i in range(2):
        # check if action_matrix already exist
        try:
            with open("action_matrix.json", "r") as f:
                action_matrix = json.load(f)
        # otherwise create new action_matrix from template
        except:
            with open("action_matrix_template.json", "r") as f:
                action_matrix = json.load(f)
        try:
            # desired map
            map = maps.get("12SquareMarinevsBaneling")
            bot = [Bot(Race.Terran, GameBot(action_matrix, i)), Computer(Race.Zerg, Difficulty.Hard)]
            # run
            run_game(map, bot, realtime=True)
        except Exception as error:
            print(f"Error when running game: {error}")

# ========== Maps ========== #
# - marine_vs_baneling_advanced
# - 12SquareMarinevsBaneling
# - marine_vs_baneling_advanced_noEnemyAI
# - marine_vs_baneling_advanced_NoOverlord
# - marine_vs_baneling_advanced_NoOverlord_noCliff
# - marine_vs_baneling_advanced_NoOverlord_MultipleAgents
# - marine_vs_baneling

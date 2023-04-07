import json
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from src.GameBot import GameBot


# Open the JSON file for reading and load the dictionary
with open("action_matrix.json", "r") as f:
    action_matrix = json.load(f)

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

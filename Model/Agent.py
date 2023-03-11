import sc2


# await self.do(worker.move(self.enemy_start_locations[0]))
# self._agent.agent.attack()
# self._agent.agent.stop()
# self.agent.agent.position
# self.agent.agent.hold_position()
# self.agent.agent.patrol()


class Agent():
    def __init__(self, name: str):
        self.name = name
        self.agent = None
        self.state = "Safe"
        super().__init__()

    def set_marine(self, unit):
        self.agent = unit

    def __str__(self):
        return f"{self.name} is {self.state}."

    def __repr__(self):
        return f"" \
               f"{type(self.agent)} " \
               f"{self.state}"

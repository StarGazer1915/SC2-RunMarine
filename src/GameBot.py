import time

import sc2
from sc2.constants import BANELING, MARINE
from MarineAgent import MarineAgent
import pygame
import numpy as np
from sc2.position import Point2


class GameBot(sc2.BotAI):
    def __init__(self):
        self.use_viz = False
        self.agents = []
        self.vismap_stored = False
        self.vismap_scores = np.array([])
        self.valid_threshold = 0.8
        self.pathing_map = np.array([])
        self.map_y_size = 0
        self.map_x_size = 0
        super().__init__()

    def on_start(self):
        self.init_window()
        self.pathing_map = self.game_info.pathing_grid.data_numpy.astype("float64")
        self.map_y_size = len(self.pathing_map)
        self.map_x_size = len(self.pathing_map[0])
        for agent in self.units.of_type(MARINE):
            self.agents.append(MarineAgent(agent, self.pathing_map, self.map_y_size, self.map_x_size))
        return super().on_start()

    def init_window(self):
        pygame.init()
        self.display = pygame.display
        self.screen = self.display.set_mode((640, 480))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Agent Viewer")
        self.use_viz = True

    # ==================== STATIC FUNCTIONS ==================== #
    def create_circular_mask(self, h, w, center=None, radius=None):
        if center is None:  # use the middle
            center = (int(w / 2), int(h / 2))
        if radius is None:  # use the smallest distance between the center and map edges
            radius = min(center[0], center[1], w - center[0], h - center[1])

        Y, X = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)

        mask = dist_from_center <= radius
        return mask

    def create_baneling_masks(self, known_banelings):
        mask_list = []
        for bane in known_banelings:
            pos = bane.position.rounded
            b_sight_range = bane.sight_range  # default 8.0
            bmask1 = np.flip(self.create_circular_mask(
                self.map_y_size, self.map_x_size, pos, b_sight_range-5.0), 0)
            bmask2 = np.flip(self.create_circular_mask(
                self.map_y_size, self.map_x_size, pos, b_sight_range-2.0), 0)
            bmask3 = np.flip(self.create_circular_mask(
                self.map_y_size, self.map_x_size, pos, b_sight_range), 0)
            mask_list.append([bmask1, bmask2, bmask3])

        return mask_list

    # ==================== ASYNC FUNCTIONS ==================== #
    async def on_step(self, iteration):
        updated_map = self.state.visibility.data_numpy.astype("float64")
        baneling_list = [unit for unit in self.known_enemy_units if unit.name == "Baneling"]
        for agent in self.agents:
            score_mask = np.flip(self.create_circular_mask(self.map_y_size, self.map_x_size,
                                                      agent.unit.position, agent.unit.sight_range), 0)

            known_banes = [b for b in baneling_list if score_mask[b.position.rounded[1]][b.position.rounded[0]]]
            agent.percept_environment(updated_map, score_mask)
            if len(known_banes) > 0:
                agent.apply_baneling_sof(score_mask, self.create_baneling_masks(known_banes))
                time.sleep(0.05)
                movement_mask = np.flip(self.create_circular_mask(
                    self.map_y_size, self.map_x_size, agent.unit.position, agent.unit.sight_range - 2.5), 0)
                await self.do(agent.take_action(movement_mask, known_banes))

            if self.use_viz:
                await self.update_viewer()
            else:
                agent.known_banes = []

    async def update_viewer(self):
        vis_data = self.state.visibility.data_numpy
        creep_data = self.state.creep.data_numpy
        movegrid_data = np.flip(self.game_info.pathing_grid.data_numpy, 0)
        merge_data = vis_data + movegrid_data

        vis_surf = pygame.surfarray.make_surface(vis_data)
        movegrid_surf = pygame.surfarray.make_surface(movegrid_data)
        merge_surf = pygame.surfarray.make_surface(merge_data)
        creep_surf = pygame.surfarray.make_surface(creep_data)

        self.screen.blit(vis_surf, (0, 0))
        self.screen.blit(movegrid_surf, (200, 0))
        self.screen.blit(creep_surf, (0, 210))
        self.screen.blit(merge_surf, (200, 210))

        pygame.display.update()

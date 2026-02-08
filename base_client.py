from game.client.user_client import UserClient
from game.common.avatar import Avatar
from game.common.enums import ObjectType, ActionType
from game.common.map.game_board import GameBoard
from game.common.game_object import GameObject
from game.common.map.occupiable import Occupiable
from game.constants import DIRECTION_TO_MOVE
from game.utils.vector import Vector

import random
import heapq
from typing import List, Tuple, Optional

# -------------------------
# CONFIG
# -------------------------

LOW_POWER = 30
OPPORTUNITY_RADIUS = 3

BASE_VALUES = {
    ObjectType.BATTERY_SPAWNER: 1200,
    ObjectType.COIN_SPAWNER: 500,
    ObjectType.SCRAP_SPAWNER: 800,
    ObjectType.GENERATOR: 2000
}

DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1)]

# -------------------------
# CLIENT
# -------------------------

class Client(UserClient):

    def team_name(self):
        return "Strategic Survivors"

    def spawner_has_item(self, spawner):
        top = self.world.get_top(spawner)
        if not top:
            return False
        return top.object_type != ObjectType.AVATAR

    def take_turn(self, turn: int, world: GameBoard, avatar: Avatar):

        self.avatar = avatar
        self.world = world

        self.scan_world()
        goal = self.choose_goal()
        if goal is None:
            goal = avatar.position

        # Opportunistic coin grab
        micro = self.find_nearby(ObjectType.COIN_SPAWNER, OPPORTUNITY_RADIUS)
        if micro:
            goal = micro

        action, _ = a_star_move(avatar.position, goal, world, avatar)
        return [action, ActionType.INTERACT_CENTER]

    # -------------------------
    # WORLD SCAN
    # -------------------------

    def scan_world(self):
        self.batteries = [
            b for b in self.world.get_objects(ObjectType.BATTERY_SPAWNER)
            if self.spawner_has_item(b)
        ]

        self.coins = [
            c for c in self.world.get_objects(ObjectType.COIN_SPAWNER)
            if self.spawner_has_item(c)
        ]

        self.scrap = [
            s for s in self.world.get_objects(ObjectType.SCRAP_SPAWNER)
            if self.spawner_has_item(s)
        ]
        self.generators = list(self.world.get_objects(ObjectType.GENERATOR))
        self.enemies = []
        self.enemies += list(self.world.get_objects(ObjectType.IAN_BOT))
        self.enemies += list(self.world.get_objects(ObjectType.JUMPER_BOT))
        self.enemies += list(self.world.get_objects(ObjectType.CRAWLER_BOT))
        self.enemies += list(self.world.get_objects(ObjectType.DUMB_BOT))

    # -------------------------
    # GOAL SELECTION
    # -------------------------

    def choose_goal(self):

        candidates = (
                self.batteries +
                self.coins +
                self.scrap +
                self.generators
        )

        best = None
        best_score = -999999

        for obj in candidates:
            if obj.object_type not in BASE_VALUES:
                continue

            dist = self.avatar.position.distance(obj)
            value = BASE_VALUES[obj.object_type]

            # Dynamic weights
            if obj.object_type == ObjectType.BATTERY and self.avatar.power < LOW_POWER:
                value *= 3

            if obj.object_type == ObjectType.GENERATOR:
                value *= 2

            score = value / (dist + 1)

            if score > best_score:
                best_score = score
                best = obj
        if best is None:
            return self.avatar.position
        return best

    # -------------------------
    # MICRO TARGET
    # -------------------------

    def find_nearby(self, obj_type, radius):
        for obj in self.world.get_objects(obj_type):
            if self.avatar.position.distance(obj) <= radius:
                return obj
        return None

# -------------------------
# PATHFINDING
# -------------------------

def a_star_move(start, goal, world, avatar):

    path = danger_a_star(start, goal, world, avatar)

    if not path or len(path) < 2:
        # small random walk so we don't freeze
        direction = random.choice(list(DIRECTION_TO_MOVE.keys()))
        return DIRECTION_TO_MOVE[direction], start + direction

    step = path[1]
    direction = step - start
    return DIRECTION_TO_MOVE[direction], step


def danger_a_star(start, goal, world, avatar):

    start_p = start.as_tuple()
    goal_p = goal.as_tuple()

    frontier = [(0, start_p)]
    came_from = {start_p: None}
    cost = {start_p: 0}

    enemies = []
    enemies += list(world.get_objects(ObjectType.IAN_BOT))
    enemies += list(world.get_objects(ObjectType.JUMPER_BOT))
    enemies += list(world.get_objects(ObjectType.CRAWLER_BOT))
    enemies += list(world.get_objects(ObjectType.DUMB_BOT))

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal_p:
            return reconstruct(came_from, current)

        for dx,dy in DIRECTIONS:
            nx,ny = current[0]+dx, current[1]+dy
            vec = Vector(nx,ny)

            if not world.is_valid_coords(vec):
                continue

            #if not world.can_object_occupy(vec, avatar):
            #    continue

            top = world.get_top(vec)
            if top and not isinstance(top, Occupiable):
                continue

            danger = danger_cost(vec, enemies)
            new_cost = cost[current] + 1 + danger

            if (nx,ny) not in cost or new_cost < cost[(nx,ny)]:
                cost[(nx,ny)] = new_cost
                priority = new_cost + vec.distance(goal)
                heapq.heappush(frontier,(priority,(nx,ny)))
                came_from[(nx,ny)] = current

    return None


def danger_cost(tile, enemies):
    cost = 0
    for e in enemies:
        d = tile.distance(e)
        if d <= 1: cost += 50
        elif d <= 3: cost += 10
    return cost


def reconstruct(came_from, cur):
    path=[]
    while cur:
        path.append(Vector(cur[0],cur[1]))
        cur=came_from[cur]
    path.reverse()
    return path

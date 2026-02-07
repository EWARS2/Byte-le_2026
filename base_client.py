
from game.client.user_client import UserClient
from game.common.avatar import Avatar
from game.common.enums import ObjectType, ActionType
from game.common.map.game_board import GameBoard
from game.constants import *

# Sample custom imports
import heapq
from typing import Dict, List, Tuple, Optional
from game.common.game_object import GameObject
from game.common.map.occupiable import Occupiable

# Custom imports
#import math

class Client(UserClient):

    def __init__(self):
        super().__init__()
        self.called = 0
        self.goal = None

    def team_name(self) -> str:
        """
        Allows the team to set a team name.
        :return: Your team name
        """
        return "Participation Trophy"

    def take_turn(self, turn: int, world: GameBoard, avatar: Avatar) -> list[ActionType]:
        """
        This is where your AI will decide what to do.
        :param turn:        The current turn of the game.
        :param actions:     This is the actions object that you will add effort allocations or decrees to.
        :param world:       Generic world information
        """

        # Setup vars
        self.called += 1
        action1 = action2 = None # Yes this is needed
        position = avatar.position

        # Calc goal
        if self.goal is None or len(world.get(position).get_objects(ObjectType.BATTERY_SPAWNER)) > 0:
            positions_battery = world.get_objects(ObjectType.BATTERY_SPAWNER)

            self.goal = next(iter(positions_battery))
            for i in positions_battery:
                distance_i = position.distance(i)
                distance_goal = position.distance(self.goal)
                if distance_i < distance_goal and distance_i != 0:
                    self.goal = i

        # Calc action1
        action1, position = a_star_move(position, self.goal, world, game_object=avatar)

        # Calc action2
        action2, position = a_star_move(position, self.goal, world, game_object=avatar)

        return [action1, action2]


Position = Tuple[int, int]

DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1)]


def a_star_move(start: Vector, goal: Vector, world, allow_vents: bool = True, game_object: GameObject | None = None) -> ActionType | None:
    path = a_star_path(
        start=start,
        goal=goal,
        world=world,
        allow_vents=allow_vents,
        game_object=game_object
    )

    if not path or len(path) < 2:
        return ActionType.INTERACT_CENTER, start

    next_step: Vector = path[1]
    direction = next_step - start
    action = DIRECTION_TO_MOVE.get(direction)
    return action, start + direction

def a_star_path(start: Vector, goal: Vector, world, allow_vents = True, game_object: GameObject | None = None) -> Optional[List[Vector]]:
    start_p = (start.x, start.y)
    goal_p = (goal.x, goal.y)

    frontier = [(0, start_p)]
    came_from = {start_p: None}
    cost = {start_p: 0}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal_p:
            path = []
            while current is not None:
                x, y = current
                path.insert(0, Vector(x, y))
                current = came_from[current]
            return path

        for dx, dy in DIRECTIONS:
            nxt = (current[0] + dx, current[1] + dy)
            vec = Vector(nxt[0], nxt[1])

            if game_object is not None and not world.can_object_occupy(vec, game_object):
                continue

            if not world.is_valid_coords(vec):
                continue

            top = world.get_top(vec)
            if top and top.object_type != ObjectType.AVATAR:
                # walls block
                if top.object_type == ObjectType.WALL:
                    continue

                # vents block unless allowed
                if top.object_type == ObjectType.VENT and not allow_vents:
                    continue

                # can't pass through non-occupiable
                if not isinstance(top, Occupiable):
                    continue

            new_cost = cost[current] + 1
            if nxt not in cost or new_cost < cost[nxt]:
                cost[nxt] = new_cost
                priority = new_cost + vec.distance(goal)
                heapq.heappush(frontier, (priority, nxt))
                came_from[nxt] = current

    return None
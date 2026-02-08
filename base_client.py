from game.client.user_client import UserClient
from game.common.avatar import Avatar
from game.common.enums import ObjectType#, ActionType
from game.common.map.game_board import GameBoard
from game.constants import *
# Sample custom imports
import heapq
from typing import List, Tuple, Optional, Any, Literal#, Dict
from game.common.game_object import GameObject
from game.common.map.occupiable import Occupiable
from game.utils.vector import Vector
# Custom imports
from math import sqrt
import random

Position = Tuple[int, int]
DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1)]
_tol = 4
retarget = True

class Client(UserClient):
    def __init__(self):
        super().__init__()
        self.goal = None
        self.positions = []
        self.positions_battery = None
        self.positions_coins = None
        self.positions_scrap = None
        self.positions_generators = None
        self.positions_refuges = None
        self.keepalive = 25

    def team_name(self) -> str:
        """
        Allows the team to set a team name.
        :return: Your team name
        """
        return "Participation Trophy"

    def take_turn(self, turn: int, world: GameBoard, avatar: Avatar) -> list[ActionType]:
        """
        This is where your AI will decide what to do.
        :param avatar:
        :param turn:        The current turn of the game.
        :param actions:     This is the actions object that you will add effort allocations or decrees to.
        :param world:       Generic world information
        """
        global retarget

        # Collect constants
        if turn == 1:
            self.positions_battery = list(world.get_objects(ObjectType.BATTERY_SPAWNER))
            self.positions_coins = list(world.get_objects(ObjectType.COIN_SPAWNER))
            self.positions_scrap = list(world.get_objects(ObjectType.SCRAP_SPAWNER))
            self.positions_generators = list(world.get_objects(ObjectType.GENERATOR))
            #self.positions_refuges = list(world.get_objects(ObjectType.REFUGE))
            self.positions = self.positions_battery + self.positions_coins + self.positions_scrap\
                             + self.positions_generators

        # Setup vars
        position = avatar.position
        self.keepalive -= 1


        # Calc goal
        #top = world.get_top(position)
        if retarget or self.goal == position or self.keepalive <= 1:
            retarget = False
            self.keepalive = 25

            if avatar.power < 35:
                self.update_target(self.positions_battery, avatar)
            else:
                self.goal = random.choice(self.positions)




        # Calc action1
        action1, position = a_star_move(position, self.goal, world, game_object=avatar)
        # Calc action2
        action2, position = a_star_move(position, self.goal, world, game_object=avatar)
        return [action1, action2]

    def update_target(self, positions, avatar: Avatar):
        position = avatar.position
        self.goal = positions[0]
        for i in positions:
            distance_i = position.distance(i)
            if distance_i < position.distance(self.goal) and distance_i != 0:
                self.goal = i
        return

def a_star_move(start: Vector, goal: Vector, world, allow_vents: bool = True, game_object: GameObject | None = None) -> \
tuple[Literal[ActionType.INTERACT_CENTER], Vector] | tuple[Any, Vector]:
    path = a_star_path(
        start=start,
        goal=goal,
        world=world,
        allow_vents=allow_vents,
        game_object=game_object
    )

    # Get list of objects to avoid
    enemies = world.get_objects(ObjectType.IAN_BOT)
    enemies.update(world.get_objects(ObjectType.JUMPER_BOT))
    enemies.update(world.get_objects(ObjectType.DUMB_BOT))
    enemies.update(world.get_objects(ObjectType.CRAWLER_BOT))
    enemies = list(enemies)

    # Find closest enemy
    closest = enemies[0]
    for i in enemies:
        distance_i = start.distance(i)
        if distance_i < start.distance(closest):
            closest = i

    # Get distance
    #dist = start.add_to_vector(closest.negative())
    #abs_dist = sqrt(dist.as_tuple()[0] ** 2 + dist.as_tuple()[1] ** 2)
    # TODO : This potentially can be sped up
    dist = start.distance(closest)

    if dist <= _tol: # Avoid enemy
        direction = (start - closest) - (goal - start)
        my_x, my_y = direction.as_tuple()
        abs_x = abs(my_x)
        abs_y = abs(my_y)
        if abs_x > abs_y:
            direction = Vector(int(my_x/abs_x), 0)
        else:
            direction = Vector(0, int(my_y/abs_y))
        action = DIRECTION_TO_MOVE.get(direction)

        # If cornered, strafe
        top = world.get_top(start + direction)
        if not isinstance(top, Occupiable):
            if abs_x < abs_y:
                direction = Vector(int(my_x / abs_x), 0)
            else:
                direction = Vector(0, int(my_y / abs_y))
            action = DIRECTION_TO_MOVE.get(direction)

        return action, start + direction
    elif not path or len(path) < 2: # Reached goal
        return ActionType.INTERACT_CENTER, start
    else: # Take step
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
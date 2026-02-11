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

Position = Tuple[int, int]
DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1)]
_tol = 4
retarget = True

class Client(UserClient):
    def __init__(self):
        super().__init__()
        self.goal = None
        self.positions_battery = None
        self.positions_coins = None
        self.positions_scrap = None
        self.positions_generators = None
        self.positions_refuges = None
        self.test = 0

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
            self.positions_refuges = list(world.get_objects(ObjectType.REFUGE))
            self.target_coin = None

        position = avatar.position
        # Locate nearest scrap
        scrap = world.get_objects(ObjectType.SCRAP_SPAWNER)
        nearest_scrap = Vector(100, 100)
        for s in scrap:
            if s.distance(position) < nearest_scrap.distance(position):
                nearest_scrap = s
        direction_to_nearest_scrap = position.direction_to(nearest_scrap)

        # Locate nearest battery
        battery = world.get_objects(ObjectType.BATTERY_SPAWNER)
        nearest_battery = Vector(100, 100)
        backup_battery = Vector(100, 100)
        for b in battery:
            if b.distance(position) < nearest_battery.distance(position):
                backup_battery = nearest_battery
                nearest_battery = b
        direction_to_nearest_battery = position.direction_to(nearest_battery)
        direction_to_backup_battery = position.direction_to(backup_battery)

        # Locate nearest gen
        gen = world.get_objects(ObjectType.GENERATOR)
        nearest_gen = Vector(100, 100)
        for g in gen:
            if g.distance(position) < nearest_gen.distance(position):
                nearest_gen = g
        direction_to_nearest_gen = position.direction_to(nearest_gen)

        # Locate nearest coin
        coin = world.get_objects(ObjectType.COIN_SPAWNER)
        nearest_coin = Vector(100, 100)
        backup_coin = Vector(100,100)
        for c in coin:
            if c.distance(position) < nearest_coin.distance(position):
                backup_coin = nearest_coin
                nearest_coin = c
        if position.distance(nearest_coin) != 0:
            direction_to_nearest_coin = position.direction_to(nearest_coin)
        else:
            direction_to_nearest_coin = position.direction_to(backup_coin)

        world.get_top(avatar.position.add_y(-1))

        vent = ObjectType.VENT
        can_move_right = world.can_object_occupy(position.add_x(1), avatar) and not world.object_is_found_at(
            position.add_x(1), vent)
        can_move_2_right = can_move_right and world.can_object_occupy(position.add_x(2),
                                                                      avatar) and not world.object_is_found_at(
            position.add_x(2), vent)
        can_move_left = world.can_object_occupy(position.add_x(-1), avatar) and not world.object_is_found_at(
            position.add_x(-1), vent)
        can_move_2_left = can_move_left and world.can_object_occupy(position.add_x(-2),
                                                                    avatar) and not world.object_is_found_at(
            position.add_x(-2), vent)
        can_move_up = world.can_object_occupy(position.add_y(-1), avatar) and not world.object_is_found_at(
            position.add_y(-1), vent)
        can_move_2_up = can_move_up and world.can_object_occupy(position.add_y(-2),
                                                                avatar) and not world.object_is_found_at(position.add_y(-2),
                                                                                                         vent)
        can_move_down = world.can_object_occupy(position.add_y(1), avatar) and not world.object_is_found_at(
            position.add_y(1), vent)
        can_move_2_down = can_move_down and world.can_object_occupy(position.add_y(2),
                                                                    avatar) and not world.object_is_found_at(
            position.add_y(2), vent)

        action1 = ActionType.INTERACT_CENTER
        action2 = ActionType.INTERACT_CENTER

        enemies = []
        for i in [ObjectType.IAN_BOT, ObjectType.JUMPER_BOT,
                  ObjectType.DUMB_BOT, ObjectType.CRAWLER_BOT]:
            enemies.extend(list(world.get_objects(i)))

        closest = enemies[0]
        for i in enemies:
            distance_i = position.distance(i)
            if distance_i < position.distance(closest):
                closest = i

        movement_direction = Vector(0, 0)
        if avatar.power < 70:
            movement_direction = direction_to_nearest_battery
        else: movement_direction = direction_to_nearest_coin

        dist = avatar.position.add_to_vector(closest.negative())
        dist = sqrt(dist.as_tuple()[0] ** 2 + dist.as_tuple()[1] ** 2)
        if dist <= 6:
            away = avatar.position.direction_to(closest).negative()
            if away == Vector(1, 1):
                action1 = ActionType.MOVE_RIGHT
                action2 = ActionType.MOVE_DOWN
            elif away == Vector(-1, 1):
                action1 = ActionType.MOVE_LEFT
                action2 = ActionType.MOVE_DOWN
            elif away == Vector(1, -1):
                action1 = ActionType.MOVE_RIGHT
                action2 = ActionType.MOVE_UP
            elif away == Vector(-1, -1):
                action1 = ActionType.MOVE_LEFT
                action2 = ActionType.MOVE_UP
            else:
                action1 = convert_vector_to_move(away)
                action2 = convert_vector_to_interact(away)

        if movement_direction == Vector(1, 1):
            action1 = ActionType.MOVE_RIGHT
            action2 = ActionType.MOVE_DOWN
        elif movement_direction == Vector(-1, 1):
            action1 = ActionType.MOVE_LEFT
            action2 = ActionType.MOVE_DOWN
        elif movement_direction == Vector(1, -1):
            action1 = ActionType.MOVE_RIGHT
            action2 = ActionType.MOVE_UP
        elif movement_direction == Vector(-1, -1):
            action1 = ActionType.MOVE_LEFT
            action2 = ActionType.MOVE_UP
        elif nearest_gen.distance(position) < 2:
            action1 = convert_vector_to_move(movement_direction)
            action2 = convert_vector_to_interact(movement_direction)
        elif nearest_battery.distance(position) < 2:
            action1 = convert_vector_to_move(movement_direction)
        else:
            action1 = convert_vector_to_move(movement_direction)


        if turn in [1, 2, 3, 4, 5, 6]:
            action1 = ActionType.MOVE_DOWN
            action2 = ActionType.MOVE_RIGHT
        if turn == 7:
            action1 = ActionType.MOVE_DOWN
            action2 = ActionType.INTERACT_CENTER
        if turn in [8, 9]:
            action1 = ActionType.MOVE_LEFT
            action2 = ActionType.MOVE_LEFT
        if turn == 10:
            action1 = ActionType.MOVE_LEFT
            action2 = ActionType.INTERACT_LEFT
        if turn in [11, 12]:
            action1 = ActionType.MOVE_RIGHT
            action2 = ActionType.MOVE_UP

        # TO COLLECT SECOND COIN, CONSIDERED UNSAFE
        if turn in [13,14, 15, 16]:
            action1 = ActionType.MOVE_RIGHT
            action2 = ActionType.MOVE_UP
        if turn in [17, 18, 19]:
            action1 = ActionType.MOVE_RIGHT
            action2 = ActionType.MOVE_RIGHT

        if action1 == None:
            action1 = ActionType.INTERACT_CENTER
        if action2 == None:
            action2 = ActionType.INTERACT_CENTER

        return [action1, action2]

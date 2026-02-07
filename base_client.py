from game.client.user_client import UserClient
from game.common.avatar import Avatar
from game.common.enums import ObjectType, ActionType
from game.common.map.game_board import GameBoard
from game.constants import *

# all allowed imports
import game.common.enums
import math
import numpy
import scipy
import pandas
import itertools
import functools
import random
import game.constants
import game.common.avatar
import game.common.map.game_board
import game.common.map.occupiable
import game.fnaacm.stations.generator
import game.utils.vector



class Client(UserClient):

    def __init__(self):
        super().__init__()

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
        actions = []
        # How far is <here> from <there>?
        # distance: int = here.distance(there)



        # Thundar moves every turn
        if 250 <= turn <= 300:
            # logic for when the computer is active
            computer_active = True
        else:
            computer_active = False

        if turn % 2 == 0:
            # true if ian is going to move the next turn
            ian_moves = True
        else:
            ian_moves = False

        if turn % 3 == 0:
            # when doe is going to move
            doe_moves = True
        else:
            doe_moves = False

        if turn % 4 == 0:
            # When Crawler is going to move
            crawler_moves = True
        else:
            crawler_moves = False



        return actions


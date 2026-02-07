
from game.client.user_client import UserClient
from game.common.avatar import Avatar
from game.common.enums import ObjectType, ActionType
from game.common.map.game_board import GameBoard
from game.constants import *

# Custom imports
import math


class Client(UserClient):

    def __init__(self):
        super().__init__()
        self.called = 0

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

        self.called += 1

        action1 = ActionType.MOVE_DOWN
        action2 = ActionType.MOVE_RIGHT

        # Get position of player
        #position = Avatar.position.
        #print(position)

        # Get position of goal

        # Check surroundings






        return [action1, action2]
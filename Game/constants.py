from enum import Enum

BLACK = 0
WHITE = 1

class ActiveFrame(Enum):
    MAIN = 1
    IN_GAME = 2
    HOST = 3
    JOIN = 4
    LOBBY = 5

class GameType(Enum):
    NONE = 1
    AI = 2
    NETWORK = 3

class NetworkHost(Enum):
    SERVER = 1
    CLIENT = 2

class NetworkIns(Enum):
    NEW_GAME = 1
    UPDATE_TIMER = 2
    MOVE_PIECE = 3
    UPGRADE_PAWN = 4
    DECLARE_WINNER = 5
    REJOINED_LOBBY = 6

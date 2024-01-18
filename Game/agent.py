import threading
from Game.model import *

class Agent(ABC):

    def __init__(self) -> None:
        self.thread = None

    def get_action(self, model: Model, do_with):
        self.thread = threading.Thread(target=self.do_get_action, args=(model, do_with))
        self.thread.start()

    @abstractmethod
    def do_get_action(self, model: Model, do_with):
        pass

    def evaluate(self, model: Model) -> int:
        '''
        Calculate and return a reward based on the cumulative value of live pieces.
        Black is the maximizing player. Reward positive points for black pieces.
        Reward negative points for white pieces.
        '''
        reward = 0
        for row in model.board:
            for piece in row:
                if piece is None: continue

                if isinstance(piece, King): temp_reward = 100
                elif isinstance(piece, Queen): temp_reward = 10
                elif isinstance(piece, Pawn): temp_reward = 1
                elif isinstance(piece, Rook): temp_reward = 3
                elif isinstance(piece, Knight): temp_reward = 3
                elif isinstance(piece, Bishop): temp_reward = 3

                if piece.color == BLACK: reward += temp_reward
                else: reward -= temp_reward

        return reward

    def sim_move(self, old_model: Model, old_piece: Piece, location: (int, int)) -> list[list[Piece]]:
        model = old_model.copy()
        piece = model.get_piece((old_piece.row, old_piece.column))
        other_piece = model.get_piece(location)

        #Handle castling move
        if len(location) == 3:
            if isinstance(piece, King):
                king = piece
                rook = other_piece
            else:
                king = other_piece
                rook = piece
            model.set_piece(None, (king.row, king.column))
            model.set_piece(king, (king.row, king.column + location[2]))
            rook_step = 1 if location[2] < 0 else -1
            model.set_piece(None, (rook.row, rook.column))
            model.set_piece(rook, (king.row, king.column + rook_step))
            king.has_moved = True
            rook.has_moved = True

        #Normal move
        else:

            #Add piece to be removed to the pieces lost dict
            if other_piece:
                other_piece.remove_from_color_list()
                piece_name = type(other_piece).__name__ + "s"
                model.pieces_lost[other_piece.color][piece_name] += 1

            #Move piece
            model.set_piece(None, (piece.row, piece.column))
            model.set_piece(piece, location)
            piece.has_moved = True

        # pass turn
        if model.turn == BLACK:
            model.turn = WHITE
            king = model.white_king
        else:
            model.turn = BLACK
            king = model.black_king

        return model


    def game_is_done(self, model: Model, turn: int) -> bool:
        pieces = model.black_pieces if turn == BLACK else model.white_pieces
        for piece in pieces:
            if piece is None: continue
            if len(piece.get_locations()) > 0: return False
        return True


class ExpectimaxAgent(Agent):

    def __init__(self, depth) -> None:
        super().__init__()
        self.depth = depth

    def do_get_action(self, model: Model, do_with):
        old, new, _ = self.expectimax(model, self.depth, BLACK)
        do_with(old, new)

    def expectimax(self, model: Model, ply: int, turn: int) -> ((int, int), float):

        # Base case
        if ply == 0 or self.game_is_done(model, turn):
            return (None, None, self.evaluate(model))

        # If this is the maximizing agent (BLACK)
        if turn == BLACK:
            maxAction = (None, None, float('-inf'))
            for piece in model.black_pieces:
                if piece is None: continue
                for location in piece.get_locations():
                    new_model = self.sim_move(model, piece, location)
                    stateAction = self.expectimax(new_model, ply, WHITE)
                    if stateAction[2] > maxAction[2]:
                        maxAction = ((piece.row, piece.column), location, stateAction[2])
                    del new_model
            return maxAction

        # If this is the minimizing agent (WHITE)
        else:
            total_reward = 0
            count = 0
            for piece in model.white_pieces:
                if piece is None: continue
                for location in piece.get_locations():
                    new_model = self.sim_move(model, piece, location)
                    total_reward += self.expectimax(new_model, ply - 1, BLACK)[2]
                    count += 1
                    del new_model
            return (None, None, total_reward / count)

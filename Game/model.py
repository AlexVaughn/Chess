from abc import ABC, abstractmethod
import copy
from Game.constants import *

class Model:

    def __init__(self, controller):
        self.controller = controller
        self.board = None
        self.pieces_lost = None
        self.black_king = None
        self.white_king = None
        self.black_pieces = None
        self.white_pieces = None
        self.turn = WHITE

    def copy(self) -> 'Model':
        model = Model(None)
        model.board = []
        model.black_pieces = []
        model.white_pieces = []

        for row in self.board:
            new_row = []
            for piece in row:

                if piece is None:
                    new_row.append(None)
                    continue

                new_piece = piece.copy()
                new_piece.model = model
                new_row.append(new_piece)
                # set king
                if isinstance(new_piece, King):
                    if new_piece.color == BLACK: model.black_king = new_piece
                    else: model.white_king = new_piece
                # add colors
                if new_piece.color == BLACK: model.black_pieces.append(new_piece)
                else: model.white_pieces.append(new_piece)

            model.board.append(new_row)

        model.pieces_lost = copy.deepcopy(self.pieces_lost)
        model.turn = self.turn
        return model


    def new_game(self):
        '''
        Start a new game. Update turn, board, pieces_lost.
        '''
        self.turn = WHITE
        self.black_king = King(self, BLACK, 0, 4)
        self.white_king = King(self, WHITE, 7, 4)
        self.board = [
            [Rook(self, BLACK, 0, 0), Knight(self, BLACK, 0, 1), Bishop(self, BLACK, 0, 2), Queen(self, BLACK, 0, 3),
                self.black_king, Bishop(self, BLACK, 0, 5), Knight(self, BLACK, 0, 6), Rook(self, BLACK, 0, 7)],
            [Pawn(self, BLACK, 1, i) for i in range(8)],
            [None]*8,
            [None]*8,
            [None]*8,
            [None]*8,
            [Pawn(self, WHITE, 6, i) for i in range(8)],
            [Rook(self, WHITE, 7, 0), Knight(self, WHITE, 7, 1), Bishop(self, WHITE, 7, 2), Queen(self, WHITE, 7, 3),
                self.white_king, Bishop(self, WHITE, 7, 5), Knight(self, WHITE, 7, 6), Rook(self, WHITE, 7, 7)]
        ]
        self.pieces_lost = {
            WHITE:{
                "Pawns": 0,
                "Rooks": 0,
                "Knights": 0,
                "Bishops": 0,
                "Queens": 0
            },
            BLACK:{
                "Pawns": 0,
                "Rooks": 0,
                "Knights": 0,
                "Bishops": 0,
                "Queens": 0
            }
        }
        #Set black pieces list
        self.black_pieces = []
        for row in self.board[:2]:
            for piece in row:
                self.black_pieces.append(piece)

        #Set white pieces list
        self.white_pieces = []
        for row in self.board[6:]:
            for piece in row:
                self.white_pieces.append(piece)


    def get_piece(self, location) -> 'Piece':
        '''
        Return the piece on the board at location (row, column).
        '''
        return self.board[location[0]][location[1]]


    def set_piece(self, piece, location):
        '''
        Assign given piece to given location (row, column).
        '''
        self.board[location[0]][location[1]] = piece
        if piece:
            piece.row = location[0]
            piece.column = location[1]


    def move_piece(self, piece, location):
        '''
        Move the given piece to the given location on the board. Update pieces lost dict.
        '''
        other_piece = self.get_piece(location)

        #Handle castling move
        if len(location) == 3:
            if isinstance(piece, King):
                king = piece
                rook = other_piece
            else:
                king = other_piece
                rook = piece
            self.set_piece(None, (king.row, king.column))
            self.set_piece(king, (king.row, king.column + location[2]))
            rook_step = 1 if location[2] < 0 else -1
            self.set_piece(None, (rook.row, rook.column))
            self.set_piece(rook, (king.row, king.column + rook_step))
            king.has_moved = True
            rook.has_moved = True

        #Normal move
        else:

            #Add piece to be removed to the pieces lost dict
            if other_piece:
                other_piece.remove_from_color_list()
                piece_name = type(other_piece).__name__ + "s"
                self.pieces_lost[other_piece.color][piece_name] += 1
                self.controller.update_lost_piece(other_piece.color, piece_name,
                    self.pieces_lost[other_piece.color][piece_name])

            #Move piece
            self.set_piece(None, (piece.row, piece.column))
            self.set_piece(piece, location)
            piece.has_moved = True


    def check_pawn_end(self, piece) -> bool:
        '''
        Returns true if pawn reached the edge of the board
        '''
        if (isinstance(piece, Pawn) and piece.color == BLACK and piece.row == 7
        or isinstance(piece, Pawn) and piece.color == WHITE and piece.row == 0):
            return True
        return False


    def transform_pawn(self, piece, new_type):
        '''
        Place a new specified piece where a pawn stands
        '''
        if new_type == "Queen": new_piece = Queen(self, piece.color, piece.row, piece.column)
        elif new_type == "Rook": new_piece = Rook(self, piece.color, piece.row, piece.column)
        elif new_type == "Knight": new_piece = Knight(self, piece.color, piece.row, piece.column)
        elif new_type == "Bishop": new_piece = Bishop(self, piece.color, piece.row, piece.column)
        self.set_piece(new_piece, (piece.row, piece.column))

        #change piece in color list
        color_list = self.black_pieces if piece.color == BLACK else self.white_pieces
        for i in range(len(color_list)):
            if color_list[i] == piece:
                color_list[i] = new_piece
                break


    def pass_turn(self):
        '''
        Pass turn to the next player, check for checkmate and stalemate.
        '''
        if self.turn == BLACK:
            self.turn = WHITE
            king = self.white_king
        else:
            self.turn = BLACK
            king = self.black_king

        #Count possible moves available
        moves = []
        for pieces in self.board:
            for piece in pieces:
                if piece and piece.color == self.turn:
                    moves += piece.get_locations()

        #If the player can't move, it's either checkmate or stalemate
        if len(moves) == 0:
            if king.in_check(): self.controller.end_game("Checkmate")
            else: self.controller.end_game("Stalemate")


class Piece(ABC):

    def __init__(self, model, color, row, column):
        self.model = model
        self.color = color
        self.row = row
        self.column = column
        self.has_moved = False


    def copy(self) -> 'Piece':
        new_copy = type(self)(None, self.color, self.row, self.column)
        new_copy.has_moved = self.has_moved
        return new_copy


    def remove_from_color_list(self):
        '''
        Removes this pieces from its color list, its no longer alive.
        '''
        color_list = self.model.black_pieces if self.color == BLACK else self.model.white_pieces
        for i in range(len(color_list)):
            if color_list[i] == self:
                color_list[i] = None
                break


    @abstractmethod
    def get_tentative(self) -> list:
        '''
        Returns a list of locations a piece can tentatively move to; list of tuple(row, column).
        '''
        pass


    def in_board_range(self, location) -> bool:
        '''
        Receives a tuple of 2 ints (row, column), returns true if the location is in range of the board list.
        '''
        return location[0] >= 0 and location[0] <= 7 and location[1] >= 0 and location[1] <= 7


    def get_linear_tentative(self, pre_tentative) -> list:
        '''
        Receive a list of semi-tentative locations this piece could move to and construct the true
        tentative list. Basically casts a ray in a direction, adds locations to the list until
        it hits another object. Allows the first tile hit belonging to the opposite color to be a
        moveable location. While not allowing the first tile hit that belongs to this pieces color to
        be a moveable location. This makes it easy to calculate the allowed locations for pieces that
        work in a line-of-sight (queen, rook, bishop).
        '''
        tentative = []
        for t in pre_tentative:
            for i in t:
                if self.model.get_piece(i):
                    if self.model.get_piece(i).color == self.color: break
                    else:
                        tentative.append(i)
                        break
                tentative.append(i)
        return tentative


    def get_locations(self, tentative=None, first_call=True, castling=False) -> list:
        '''
        Search a list of tentative locations this piece can move to. Compile and return a new list
        of locations after simulating each move and checking if it would leave the king in check.
        first_call and castling are used to avoid recursion.
        '''
        if not tentative: tentative = self.get_tentative()
        locations = []

        for loc in tentative:

            #Cant overtake a king
            if first_call and (loc == (self.model.black_king.row, self.model.black_king.column)
            or loc == (self.model.white_king.row, self.model.white_king.column)):
                continue

            #Save state
            original_loc = (self.row, self.column)
            org_piece = self.model.get_piece(loc)

            #Simulate move
            self.model.set_piece(None, (self.row, self.column))
            self.model.set_piece(self, loc)

            #Check if king is in check
            king = self.model.black_king if self.color == BLACK else self.model.white_king
            if first_call:
                if not king.in_check(): locations.append(loc)
            else: locations.append(loc)

            #Restore state
            self.model.set_piece(org_piece, loc)
            self.model.set_piece(self, original_loc)

        if not castling and first_call and ((isinstance(self, King) or isinstance(self, Rook))):
            locations += self.get_castling_locations()

        return locations


    def get_castling_locations(self) -> list:
        '''
        Adds castling locations to the tentative list for rooks and kings.
        Castling allows the king to move two spaces to the east or west
        and the rook moves to the opposite side of the king from where it came.
        Castling conditions:
        1. Both the king and the rook must not have moved yet
        2. There must not be any pieces in between the king and the rook
        3. King cannot be in check
        4. King cannot be in check after castling (this will be verified in the self.get_locations() call)
        5. King cannot move through locations that would result in a check
        '''
        castling_locations = []
        king = self.model.black_king if self.color == BLACK else self.model.white_king

        #Verify king has not moved and is not in check
        if king.has_moved or king.in_check(): return []

        #Left rook
        rook = self.model.get_piece((king.row, king.column-4))
        if self is rook or isinstance(self, King):
            if isinstance(rook, Rook) and not rook.has_moved:

                path_locations = [(king.row, king.column-i-1) for i in range(3)
                    if not self.model.get_piece((king.row, king.column-i-1))]

                if len(path_locations) == 3:

                    if len(king.get_locations(path_locations, castling=True)) == 3:

                        if isinstance(self, King):
                            castling_locations.append((rook.row, rook.column, -2))
                        else:
                            castling_locations.append((king.row, king.column, -2))

        #Right rook
        rook = self.model.get_piece((king.row, king.column+3))
        if self is rook or isinstance(self, King):
            if isinstance(rook, Rook) and not rook.has_moved:

                path_locations = [(king.row, king.column+i+1) for i in range(2)
                    if not self.model.get_piece((king.row, king.column+i+1))]

                if len(path_locations) == 2:

                    if len(king.get_locations(path_locations, castling=True)) == 2:

                        if isinstance(self, King):
                            castling_locations.append((rook.row, rook.column, 2))
                        else:
                            castling_locations.append((king.row, king.column, 2))

        return castling_locations


class Pawn(Piece):

    def get_tentative(self) -> list:
        '''
        Returns a list of locations a piece can tentatively move to; list of tuple(row, column).
        '''
        tentative = []
        step = 1 if self.color == BLACK else -1

        #Add forward 1 step
        loc = (self.row+step, self.column)
        if self.in_board_range(loc):
            piece = self.model.get_piece(loc)
            if not piece:
                tentative.append(loc)

                #Add forward 2 steps
                loc2 = (self.row+step*2, self.column)
                if self.in_board_range(loc2):
                    piece2 = self.model.get_piece(loc2)
                    if not self.has_moved and not piece2: tentative.append(loc2)

        #Add adjacent forward moves
        locations = [(self.row+step, self.column-1), (self.row+step, self.column+1)]
        for loc in locations:
            if self.in_board_range(loc):
                piece = self.model.get_piece(loc)
                if piece and piece.color != self.color:
                    tentative.append(loc)

        return tentative


class Rook(Piece):

    def get_tentative(self) -> list:
        '''
        Returns a list of locations a piece can tentatively move to; list of tuple(row, column).
        '''
        return self.get_linear_tentative([
            [(self.row, self.column+i+1) for i in range(8) if self.in_board_range((self.row, self.column+i+1))],
            [(self.row, self.column-i-1) for i in range(8) if self.in_board_range((self.row, self.column-i-1))],
            [(self.row+i+1, self.column) for i in range(8) if self.in_board_range((self.row+i+1, self.column))],
            [(self.row-i-1, self.column) for i in range(8) if self.in_board_range((self.row-i-1, self.column))]
        ])


class Knight(Piece):

    def get_tentative(self) -> list:
        '''
        Returns a list of locations a piece can tentatively move to; list of tuple(row, column).
        '''
        tentative = []
        locations = [(2, -1), (2, 1), (1, -2), (1, 2), (-1, -2), (-1, 2), (-2, -1), (-2, 1)]
        for i in locations:
            loc = (self.row+i[0], self.column+i[1])
            if self.in_board_range(loc):
                piece = self.model.get_piece(loc)
                if not piece or (piece and piece.color != self.color):
                    tentative.append(loc)
        return tentative


class Bishop(Piece):

    def get_tentative(self) -> list:
        '''
        Returns a list of locations a piece can tentatively move to; list of tuple(row, column).
        '''
        return self.get_linear_tentative([
            [(self.row-i-1, self.column+i+1) for i in range(8) if self.in_board_range((self.row-i-1, self.column+i+1))],
            [(self.row+i+1, self.column+i+1) for i in range(8) if self.in_board_range((self.row+i+1, self.column+i+1))],
            [(self.row+i+1, self.column-i-1) for i in range(8) if self.in_board_range((self.row+i+1, self.column-i-1))],
            [(self.row-i-1, self.column-i-1) for i in range(8) if self.in_board_range((self.row-i-1, self.column-i-1))]
        ])


class Queen(Piece):

    def get_tentative(self) -> list:
        '''
        Returns a list of locations a piece can tentatively move to; list of tuple(row, column).
        '''
        return self.get_linear_tentative([
            [(self.row, self.column+i+1) for i in range(8) if self.in_board_range((self.row, self.column+i+1))],
            [(self.row, self.column-i-1) for i in range(8) if self.in_board_range((self.row, self.column-i-1))],
            [(self.row+i+1, self.column) for i in range(8) if self.in_board_range((self.row+i+1, self.column))],
            [(self.row-i-1, self.column) for i in range(8) if self.in_board_range((self.row-i-1, self.column))],
            [(self.row-i-1, self.column+i+1) for i in range(8) if self.in_board_range((self.row-i-1, self.column+i+1))],
            [(self.row+i+1, self.column+i+1) for i in range(8) if self.in_board_range((self.row+i+1, self.column+i+1))],
            [(self.row+i+1, self.column-i-1) for i in range(8) if self.in_board_range((self.row+i+1, self.column-i-1))],
            [(self.row-i-1, self.column-i-1) for i in range(8) if self.in_board_range((self.row-i-1, self.column-i-1))]
        ])


class King(Piece):

    def get_tentative(self) -> list:
        '''
        Returns a list of locations a piece can tentatively move to; list of tuple(row, column).
        '''
        tentative = []
        for i in range(3):
            for j in range(3):
                loc = (self.row-1+i, self.column-1+j)
                if i == 1 and j == 1 or not self.in_board_range(loc): continue
                piece = self.model.get_piece(loc)
                if not piece or piece and piece.color != self.color:
                    tentative.append(loc)
        return tentative


    def in_check(self) -> bool:
        '''
        Search all possible moves of all opposing pieces and see if they can attack the king.
        '''
        for row in self.model.board:
            for piece in row:
                if not piece or piece is self or piece.color == self.color: continue
                if (self.row, self.column) in piece.get_locations(first_call=False): return True
        return False

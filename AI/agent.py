from Game.model import *
from AI.train_model import Linear_QNet, QTrainer
import torch

class Agent:

    def __init__(self, game_model, data_extract=False, is_training=False):
        self.game_model = game_model
        self.model_file = "AI\\ai_model.pt"
        self.upgrade_type = None    #for pawn upgrade
        
        if not data_extract:
            self.model = Linear_QNet(self.model_file, 4288, 8576, 1024) #input_size, hidden_layer_size, possible_moves
            self.trainer = QTrainer(self.model, is_training)
        

    def get_state(self) -> torch.Tensor:
        '''
        State consits of the following for each piece:
        64 indecies for where the piece can move to
        64 indecies for where the piece is standing
        6 indecies to represent the piece type

        (64 + 64 + 6) * 32 pieces = 4288
        Black pieces are first, followed by white pieces
        '''
        state = []
        for piece in self.game_model.black_pieces + self.game_model.white_pieces:
            state += self.get_piece_view(piece)
            state += self.get_piece_type_hot(piece)
        return torch.tensor(state, dtype=torch.float)


    def get_piece_view(self, piece) -> list:
        '''
        Returns a list made up of two boards:
        one with 1's where the piece could move, 0's for everything else
        The other, 1 for where the piece is currently, 0's everywhere else
        '''
        move_board = [0]*64
        standing_board = [0]*64
        if piece:
            
            for loc in piece.get_locations():
                index = loc[0]*8 + loc[1]   #row, column
                move_board[index] = 1
            
            index = piece.row*8 + piece.column
            standing_board[index] = 1
        
        return move_board + standing_board


    def get_piece_type_hot(self, piece) -> list:
        '''
        Create a one-hot encoding to represent the piece type
        '''
        piece_dict = {
            Rook: 0,
            Knight: 1,
            Bishop: 2,
            Queen: 3,
            King: 4,
            Pawn: 5
        }
        piece_type = [0]*6
        if piece: piece_type[piece_dict[type(piece)]] = 1
        return piece_type


    def get_action_from_model(self, state) -> "Piece, int, int":
        '''
        Returns the piece to be moved, the row to move, the column to move
        based on the given state of the game.
        '''
        prediction = self.model(state)
        
        while True:

            #Get best move
            move_index = torch.argmax(prediction).item()
            if prediction[move_index] == float("-inf"):
                print("no legal moves were found")
                raise ValueError
            
            piece_index = (move_index) // 64   #group to piece
            row = (move_index % 64) // 8       #group to row
            column = (move_index % 64) % 8     #group to column
            piece = self.game_model.white_pieces[piece_index]  #get the piece obj

            #Determine if move is valid
            if not piece:
                prediction[move_index] = float("-inf")
                continue

            to_move = (row, column)
            for loc in piece.get_locations():
                if to_move == (loc[0], loc[1]):
                    return piece, row, column
            prediction[move_index] = float("-inf")


    def get_action_from_data(self, game) -> "torch.Tensor, Piece, int, int, float, int":
        '''
        Receives a string of moves from 1 game, yields the moves tensor that
        matches the output layer of the model, the piece to be moved, row to move,
        column to move, the reward, and if game is done.
        '''
        game_moves = game.split(",")
        result = game_moves[0]
        game_moves = game_moves[1:]
        done = 0
        
        #Loop through each move in a game
        for m in enumerate(game_moves):

            #Determine if this is the last move
            if m[0] == len(game_moves)-1:
                done = 1
            
            #Interpret chess notation, if bad data, break loop to go to next game
            try:
                moves, piece, row, column, reward = self.interpret_move(m[1])
            except:
                yield None, None, 0, 0, 0, -1
                break

            #Change reward if game is over
            if done:
                if result == "W": reward = 1
                elif result == "B": reward = -1
                else: reward = 0

            yield moves, piece, row, column, reward, done
                        

    def interpret_move(self, move) -> "torch.Tensor, Piece, int, int, float":
        '''
        King = K, Queen = Q, Bishop = B, Knight = N, Rook = R, Pawn = no notation.
        Capturing an enemy piece sees an "x" placed between the piece moved and the square the captured piece was upon.
        When the opponent's king is threatened by check, a "+" sign is added to the end of the notation.
        Castling kingside is written as "O-O". Castling queenside is notated with "O-O-O"
        "=" means pawn promotion ex: b8=Q means pawn at b8 is upgraded to Queen
        https://www.ichess.net/blog/chess-notation/
        '''
        piece_dict = {
            "K": King,
            "Q": Queen,
            "B": Bishop,
            "N": Knight,
            "R": Rook,
            "P": Pawn
        }
        color = BLACK if move[0] == "B" else WHITE
        move = move.strip().split(".")[1]
        piece_captured = False
        enemy_in_check = False
        
        #Handle pawn upgrade
        if "=" in move:
            self.upgrade_type = piece_dict[move[-1]]
            move = move[:-2]

        #Mark capture a piece
        if "x" in move:
            piece_captured = True
            move = move.replace("x", "")

        #Mark enemy king in check
        if "+" in move:
            enemy_in_check = True
            move = move.replace("+", "")

        #Handle castling moves
        if move[0] == "O":
            if color == BLACK:
                piece = self.game_model.black_king
                piece_index = 4
                row = 0
            else:
                piece = self.game_model.white_king
                piece_index = 12
                row = 7
            
            if move == "O-O": column = 7
            elif move == "O-O-O": column = 0

        #Handle regular move
        else:

            #Change chess notation (row, column) to match game models indecies
            loc = move[-2:]
            move = move[:-2]
            row = -int(loc[1]) + 8
            column = ord(loc[0]) - 97

            #Get piece type
            if len(move) > 0 and move[0].isupper():
                piece_type = piece_dict[move[0]]
                move = move[1:]
            else:
                piece_type = piece_dict["P"]

            #Get possible identifier to remove move ambiguity
            if len(move) > 0:
                try: identifier = (1, -int(move[0]) + 8)     #row = 1
                except: identifier = (2, ord(move[0]) - 97)  #column = 2
                move = move[1:]
            else: identifier = (0, 0)                        #none = 0

            assert len(move) == 0
        
            #Get the piece object and the index the piece is located at in the colors list of pieces
            piece_index, piece = self.get_piece_by_location(color, piece_type, (row, column), identifier)


        #Create move tensor to match the output layer of the model
        if color == WHITE:
            move_index = piece_index*64 + row*8 + column
            moves = torch.zeros(1024, dtype=torch.float)
            moves[move_index] = 1
        else:
            moves = None

        reward = self.calc_move_reward(piece_captured, enemy_in_check, (row, column))

        return moves, piece, row, column, reward
        
        
    def get_piece_by_location(self, color, piece_type, loc, identifier) -> "int, Piece":
        '''
        Determine which piece is to be moved, Assures there is no move ambiguity
        returns the piece specified by chess notation
        
        identifier[0] specifies the piece is identified by row or column
        identifier[1] specifies the row/column the piece is standing in
        '''
        color_list = self.game_model.black_pieces if color == BLACK else self.game_model.white_pieces
        pieces = []
        for piece in enumerate(color_list):
            if type(piece[1]) == piece_type:
                
                for i in piece[1].get_locations():
                    if loc == (i[0], i[1]):

                        if (identifier[0] == 0
                        or (identifier[0] == 1 and piece[1].row == identifier[1])
                        or (identifier[0] == 2 and piece[1].column == identifier[1])):
                            pieces.append(piece)
        
        assert len(pieces) == 1  #There is ambiguity if this is > 1
        
        return pieces[0]


    def calc_move_reward(self, piece_captured, enemy_in_check, loc) -> float:
        '''
        Determine reward for putting the enemy king in check and/or
        which piece type is being captured, return the appropriate reward
        '''
        capture = {
            Queen: 0.3,
            Bishop: 0.2,
            Knight: 0.2,
            Rook: 0.2,
            Pawn: 0.1
        }
        reward = 0
        
        if piece_captured:
            piece = self.game_model.get_piece(loc)
            reward += capture[type(piece)]
        
        if enemy_in_check:
            reward += 0.1
        
        return reward


    def include_castling_if(self, piece, loc) -> "int, int":
        '''
        Edit loc to include castling instruction if castling
        '''
        if isinstance(piece, King) and not piece.has_moved:
            other_piece = self.game_model.get_piece(loc)
            
            if (other_piece and other_piece.color == piece.color
            and isinstance(other_piece, Rook) and not other_piece.has_moved):
                for i in piece.get_locations():
                    if loc == (i[0], i[1]):
                        loc = i
                        break
        return loc


    def send_move(self, piece, loc):
        '''
        Sends move to the game model to perform the specified move
        '''
        loc = self.include_castling_if(piece, loc)
        self.game_model.move_piece(piece, loc)

        #upgrade the pawn if marked
        if self.upgrade_type is not None:
            self.game_model.transform_pawn(piece, self.upgrade_type.__name__)
            self.upgrade_type = None


    def get_model_input_data(self, game_data):
        '''
        A generator that returns the data to feed into the training model:
        (state_last, state_new, moves_w, reward_w, done)

        White is the models playing color. Get whites move and blacks responding
        move. The start state will be before white makes its move and the end state
        is after black makes its move in response. This way the model may learn the 
        consequences of its actions. The environment that white is in includes black
        moving, which is essentially the environments reaction to any action white
        makes. It is not solely, for example, a pawn being at a new location because
        white moved it.
        '''
        self.game_model.new_game()
        data_gen = self.get_action_from_data(game_data)

        while True:

            state_last = self.get_state()                                       #Get start state
            moves_w, piece_w, row_w, column_w, reward_w, done = next(data_gen)  #Get white's move
            if done == -1: break
            self.send_move(piece_w, (row_w, column_w))                          #Perform white move
            if done:
                state_new = self.get_state()
                yield state_last, state_new, moves_w, reward_w, done
                break

            moves_b, piece_b, row_b, column_b, reward_b, done = next(data_gen)  #Get black's move
            if done == -1: break
            self.send_move(piece_b, (row_b, column_b))                          #Perform black move

            #If black got a reward, that is bad for white, set whites reward to the negative of blacks reward
            if reward_b > 0:
                reward_w = -reward_b
            
            state_new = self.get_state()
            yield state_last, state_new, moves_w, reward_w, done

            if done: break

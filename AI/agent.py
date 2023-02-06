import torch, os, sys, pickle
from AI.train_model import Linear_QNet, QTrainer
from Game.model import *
from Game.constants import *
from collections import deque
import matplotlib.pyplot as plt
from IPython import display

class TrainingState:
    
    def __init__(self):
        self.n_games = 0
        self.recent_moves = deque(maxlen=100)
        self.move_count = 0
        self.game_loss = 0
        self.loss = 0
        self.losses = []

    def plot(self):
        plt.ion()
        sys.stdout = open(os.devnull, 'w')  #disable printing to console
        display.clear_output(wait=True)
        display.display(plt.gcf())
        plt.clf()
        plt.title('Training...')
        plt.xlabel('Number of Games')
        plt.ylabel('Loss')
        plt.plot(self.losses, label="loss")
        plt.legend()
        plt.ylim(ymin=0)
        plt.text(len(self.losses)-1, self.losses[-1], str(self.losses[-1]))
        plt.show(block=False)
        plt.pause(.01)
        sys.stdout = sys.__stdout__ #enable printing to console


class Agent:

    def __init__(self, game_model, is_training=False):
        self.game_model = game_model
        self.is_training = is_training
        self.upgrade_type = None
        self.data_file = "AI\\chess_moves.txt"
        self.model_file = "AI\\ai_model.pt"
        self.training_state_file = "AI\\training_state.pickle"
        self.training_state = TrainingState()
        self.model = Linear_QNet(self.model_file, 4288, 8576, 1024)  #input_size, hidden_layer_size, possible_moves
        self.trainer = QTrainer(self.model)

        if torch.cuda.is_available(): self.device = torch.device("cuda:0")
        else: self.device = torch.device("cpu")
        
        self.load_state()
        self.model.to(self.device)


    def save_state(self):

        self.model.save()
        print("Saved Model")

        with open(self.training_state_file, 'wb') as file:
            pickle.dump(self.training_state, file, protocol=pickle.HIGHEST_PROTOCOL)
        print("Saved Training state object")


    def load_state(self):

        if os.path.exists(self.model_file):
            self.model.load()
            print("Model Loaded.")
        else:
            print("Did not load model")

        if self.is_training and os.path.exists(self.training_state_file):
            with open(self.training_state_file, 'rb') as file:
                self.training_state = pickle.load(file)
            print("Training state object loaded")
        else:
            print("Did not load training state object")


    def new_game(self):
        '''
        Start a new game, reset model board
        '''
        self.game_model.new_game()
        
        if self.training_state.move_count != 0:
            self.training_state.loss += self.training_state.game_loss / self.training_state.move_count
        self.training_state.game_loss = 0
        self.training_state.move_count = 0
        
        if self.training_state.n_games % 100 == 0:
            print(f"Game {self.training_state.n_games}")
            if self.training_state.loss != 0:
                self.training_state.loss /= 100
                self.training_state.losses.append(self.training_state.loss)
                self.training_state.loss = 0
                self.training_state.plot()
            
            self.save_state()
        
        self.training_state.n_games += 1


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

        return torch.tensor(state, dtype=torch.float).to(self.device)


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


    def get_action_from_data(self) -> "torch.Tensor, Piece, int, int, float, int":
        '''
        A generator that reads a data file of moves, yields the moves tensor that
        matches the output layer of the model, the piece to be moved, row to move,
        column to move, the reward, and if game is done.

        Black will perform move here automatically
        White's move needs to be performed outside of this function call
        '''

        with open(self.data_file, "r") as file:
            next(file)  #skip header
            
            #skip ahead to n_games if a model was loaded to resume training
            for i in range(self.training_state.n_games):
                next(file)

            #Loop through each game (each line)
            for i in file.readlines():
                game_moves = i.split(",")
                result = game_moves[0]
                game_moves = game_moves[1:]
                
                #Loop through each move in a game
                done = 0
                last_is_white = game_moves[-1][0] == "W"
                for m in enumerate(game_moves):

                    self.training_state.recent_moves.append(m[1])

                    #Determine if this is the last move
                    if ((last_is_white and m[0] == len(game_moves)-1)
                    or (not last_is_white and m[0] == len(game_moves)-2)):
                        done = 1
                    
                    #Perform blacks move
                    if m[0] % 2 == 1:
                        try: piece_index, piece, row, column, reward = self.interpret_move(m[1])
                        except:
                            yield None, None, 0, 0, 0, -1
                            break
                        self.send_move(piece, (row, column))

                    #Yield white's move
                    else:
                        try: piece_index, piece, row, column, reward = self.interpret_move(m[1])
                        except:
                            yield None, None, 0, 0, 0, -1
                            break
                        move_index = piece_index*64 + row*8 + column
                        moves = torch.zeros(1024, dtype=torch.float).to(self.device)
                        moves[move_index] = 1
                        
                        #Change result if game is over
                        if done:
                            if result == "W": reward = 1
                            elif result == "B": reward = -1
                            else: reward = 0

                        yield moves, piece, row, column, reward, done
                        
                    if done: break


    def interpret_move(self, move) -> "Piece, int, int, int, float":
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
        reward = 0.0
        move = move.strip().split(".")[1]
        
        #handle pawn upgrade
        if "=" in move:
            self.upgrade_type = piece_dict[move[-1]]
            move = move[:-2]

        #Calc reward
        if "x" in move:
            reward += 0.1
            move = move.replace("x", "")

        if "+" in move:
            reward += 0.1
            move = move.replace("+", "")

        #handle castling moves
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
            
            return piece_index, piece, row, column, reward

        #change chess notation (row, column) to match game models indecies
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
        piece_index, piece = self.get_piece_by_location(color, piece_type, (row, column), identifier)

        return piece_index, piece, row, column, reward
        
        
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


    def train(self):

        self.new_game()
        state_last = None
        for moves, piece, row, column, reward, done in self.get_action_from_data():
            self.training_state.move_count += 1

            if done == -1:
                print(f"Bad data detected, skipping the rest of game {self.training_state.n_games}")
                self.new_game()
                state_last = None
                continue

            if state_last is None: state_last = self.get_state()
            self.send_move(piece, (row, column))
            state_new = self.get_state()
            self.training_state.game_loss += self.trainer.train_step(state_last, state_new, moves, reward, done)
            state_last = state_new

            if done:
                self.new_game()
                state_last = None


class TrainController:

    def __init__(self) -> None:
        self.model = Model(self)

    def update_lost_piece(*args):
        pass

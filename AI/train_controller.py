import multiprocessing
from AI.agent import Agent
from AI.training_state import TrainingState
from Game.model import Model


class TrainController:

    def __init__(self) -> None:
        self.data_file = "AI\\chess_moves.txt"
        self.batch_size = 1000
        self.training_agent = Agent(None, is_training=True)
        self.ts = TrainingState()
        self.fake_controller = FakeGameController()
        self.training_agent.model.load()
        self.ts.load_state()


    def train(self):
        '''
        Read data from file, send to processes, processes 
        interpret data and return input data for the training model,
        train model on data.
        '''
        self.ts.plot()
        line_gen = self.get_next_lines()
        pool = multiprocessing.Pool()
        print(f"Device: {self.training_agent.trainer.device}")
        
        while True:
            print(f"Game: {self.ts.n_games}")

            #Pull data from file and interpret
            print("Processing data...")
            try: game_data = next(line_gen)
            except StopIteration: break
            result = pool.map(self.process_data, game_data)
            
            #Train on the resulting data in the batch
            print("Training...")
            for steps in result:
                for state_last, state_new, moves, reward, done in steps:
                    self.ts.loss += self.training_agent.trainer.train_step(state_last, state_new, moves, reward, done)
                    self.ts.step_count += 1
            
            self.ts.update_variables(self.batch_size)
            self.ts.plot()
            self.training_agent.model.save()
            self.ts.save_state()
            del result

        pool.close()


    def get_next_lines(self) -> list:
        '''
        Generator, yields a list of self.batch_size number of lines of game
        data each time this is called. Each line is one game.
        '''
        with open(self.data_file, "r") as file:
            next(file)  #skip header
            
            #skip ahead to n_games if a model was loaded to resume training
            for _ in range(self.ts.n_games):
                next(file)

            #get batch_size number of lines
            game_data = []
            while True:
                
                if len(game_data) == self.batch_size:
                    yield game_data
                    game_data = []
                
                try:
                    game_data.append(next(file))
                
                except StopIteration:
                    yield game_data
                    game_data = []
                    break


    def process_data(self, game_data):
        '''
        Each process will "play" multiple games. They will create a
        game_model and an agent to determine the sequence of states
        that occur during a game.

        Interprets the received data and gets the states for each step
        in the games moves. Puts all these states into 1 list per game,
        adds the list to self.game_states. self.game_states is now ready
        to be consumed by the training model.

        Each process will get self.batch_size/self.n_groups number of games
        '''
        model = Model(self.fake_controller)
        agent = Agent(model, data_extract=True)
        data_gen = agent.get_model_input_data(game_data)
        input_data = []
        while True:
            try: input_data.append(next(data_gen))
            except StopIteration: break
        del model
        del agent
        return input_data


class FakeGameController:
    def update_lost_piece(*args):
        pass

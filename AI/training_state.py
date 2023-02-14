import matplotlib.pyplot as plt
from IPython import display
import os, sys, pickle

class TrainingState:
    
    def __init__(self):
        self.ts_file = "AI\\training_state.pickle"
        self.n_games = 0
        self.step_count = 0
        self.loss = 0
        self.losses = [0]
        self.x = [0]
        plt.ion()

    
    def save_state(self):
        with open(self.ts_file, 'wb') as file:
            pickle.dump(self, file, protocol=pickle.HIGHEST_PROTOCOL)
        print("Saved Training state object")


    def load_state(self):
        if os.path.exists(self.ts_file):
            with open(self.ts_file, 'rb') as file:
                loaded = pickle.load(file)
                self.ts_file = loaded.ts_file
                self.n_games = loaded.n_games
                self.step_count = loaded.step_count
                self.loss = loaded.loss
                self.losses = loaded.losses
                self.x = loaded.x
            print("Training state object loaded")
        else:
            print("Did not load training state object")


    def update_variables(self, n_games):
        if self.step_count == 0: self.step_count = 1
        self.losses.append(self.loss/self.step_count)
        self.loss = 0
        self.step_count = 0
        self.n_games += n_games
        self.x.append(self.n_games)


    def plot(self):
        sys.stdout = open(os.devnull, 'w')  #disable printing to console
        display.clear_output(wait=True)
        display.display(plt.gcf())
        plt.clf()
        plt.title("Loss vs. n Games")
        plt.ylabel("Loss")
        plt.xlabel("Number of Games")
        plt.plot(self.losses, label="Loss")
        plt.xticks(range(len(self.x)), self.x)
        plt.legend()
        plt.ylim(ymin=0)
        plt.text(len(self.losses)-1, self.losses[-1], str(self.losses[-1]))
        plt.show(block=False)
        plt.pause(.01)
        sys.stdout = sys.__stdout__ #enable printing to console

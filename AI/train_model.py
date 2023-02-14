import torch, os
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F


class Linear_QNet(nn.Module):
    def __init__(self, model_file, input_size, hidden_size, output_size):
        self.model_file = model_file
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.relu(self.linear1(x))
        x = self.linear2(x)
        return x

    def save(self):
        torch.save(self.state_dict(), self.model_file)

    def load(self):
        if os.path.exists(self.model_file):
            self.load_state_dict(torch.load(self.model_file))
            print("Model Loaded.")
        else:
            print("Did not load model")
        

class QTrainer:
    '''
    Uses bellman equation to calculate new Q values
    '''
    def __init__(self, model, is_training):
        self.model = model
        self.lr = 0.0001
        self.gamma = 0.9    #discount rate
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        self.criterion = nn.MSELoss()
        
        if is_training and torch.cuda.is_available():
            self.device = torch.device("cuda:0")
        else:
            self.device = torch.device("cpu")
        self.model.to(self.device)


    def train_step(self, state_last, state_new, action, reward, done):

        state_last = state_last.to(self.device)
        state_new = state_new.to(self.device)
        reward = torch.tensor(reward, dtype=torch.float)

        if len(state_last.shape) == 1:   # (1, x)
            state_last = torch.unsqueeze(state_last, 0)
            state_new = torch.unsqueeze(state_new, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            done = (done, )
        
        #Predicted Q values with current state
        pred = self.model(state_last)
        target = pred.clone()

        for i in range(len(done)):
            if not done:                                        #If the game ended, the last state does not predict the next state
                pred_q = torch.max(self.model(state_new[i]))
                Q_new = reward + self.gamma*pred_q
            else:
                Q_new = reward[i]
            target[0][torch.argmax(action[0]).item()] = Q_new   #max returns highest value, argmax returns highest values index
    
        self.optimizer.zero_grad()
        loss = self.criterion(pred, target)
        loss.backward()
        self.optimizer.step()

        return loss.item()

from AI.agent import *

def show_board():
    global ai_controller
    from Game.view import App
    app = App()
    app.hide_menu_frame()
    app.show_ingame_frame()
    
    for i in range(len(ai_controller.model.board)):
        for j in range(len(ai_controller.model.board[i])):
            piece = ai_controller.model.get_piece((i,j))
            app.update_tile((i,j), *app.controller.get_image(piece))

    app.mainloop()


if __name__ == '__main__':
    global ai_controller
    ai_controller = TrainController()
    agent = Agent(ai_controller.model, is_training=True)
    try:
        agent.train()
    except:
        print("Game:", agent.training_state.n_games)
        print(agent.training_state.recent_moves)
        show_board()
        raise RuntimeError

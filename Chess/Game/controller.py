from Game.model import Model
from Game.constants import *
from Game.timer import Timer
from Game.network import *
from AI.agent import Agent

class Controller:

    def __init__(self, app):
        self.view = app
        self.model = Model(self)
        self.game_type = GameType(GameType.NONE.value)
        self.agent = Agent(self.model)
        self.time_limit = 93  #Add 3 seconds to desired seconds to account for a timer buffer
        self.timer = Timer(1, self.time_limit, func=self.view.update_timer, func_args=(WHITE,), 
            final_func=self.end_game, final_args=("Timer",))
        self.player_color = BLACK
        self.selected_locations = []
        self.piece_selected = None
        self.pawn_to_upgrade = None
        self.online_player = None
        self.win_con = None
        self.win_color = None
        

    def new_game(self):
        '''
        Setup a new gameplay loop.
        '''
        self.win_con = None
        self.win_color = None
        self.clear_selection()
        self.model.new_game()
        self.view.new_game()
        self.update_board_tiles()
        self.timer.reset()

        if self.online_player:
            self.game_type = GameType.NETWORK.value
            
            if isinstance(self.online_player.host, Server):
                self.timer.resume()
                self.send_ins(NetworkIns.NEW_GAME.value)
            elif isinstance(self.online_player.host, Client):
                self.timer.final_func = None

        else:
            self.timer.func_args=(WHITE,)
            self.timer.final_func = self.end_game
            self.timer.resume()
            if self.model.turn != self.player_color: self.agent_move()


    def update_board_tiles(self):
        '''
        Updates the visuals for each tile on the board according to the model
        '''
        for i in range(len(self.model.board)):
            for j in range(len(self.model.board[i])):
                piece = self.model.get_piece((i,j))
                self.view.update_tile((i,j), *self.get_image(piece))


    def pass_turn(self):
        '''
        Called when a player has moved a piece, signaling the end of their turn.
        '''
        self.model.pass_turn()
        self.view.pass_turn(self.model.turn)
        if not self.view.popup_quit:
            self.timer.reset(new_args=(self.model.turn, ))
            self.timer.resume()
        
        if (self.game_type == GameType.AI.value
        and self.model.turn != self.player_color):
            self.agent_move()


    def get_image(self, piece) -> tuple:
        '''
        Receive a piece object, return its corresponding image from view.
        '''
        if not piece: return None, None
        else: return piece.color, type(piece).__name__


    def clear_selection(self):
        '''
        Deselect a piece that is highlighted on the board, forget the piece that is currently selected.
        '''
        self.piece_selected = None
        self.selected_locations = []
        self.view.remove_highlights()


    def tile_clicked(self, tile):
        '''
        Event handler for when a tile is clicked by the left mouse button.
        Left clicking a tile will highlight it only if there is a piece there,
        it will also highlight the tiles that the piece can move to.
        The second click will move a piece from the selected tile to the second selected tile
        '''
        if self.model.turn != self.player_color:
            return

        sel_location = (tile.row, tile.column)
        piece = self.model.get_piece(sel_location)
        loc_in_selected = False

        #Determine if location is in the selected locations list
        #Set location to 'i' because 'i' might have a castling instruction
        for i in self.selected_locations:
            if (i[0], i[1]) == sel_location:
                sel_location = i
                loc_in_selected = True

        #Move a piece
        if self.piece_selected and loc_in_selected:
            old_location = (self.piece_selected.row, self.piece_selected.column)
            self.perform_move(old_location, sel_location)

            if self.model.check_pawn_end(self.piece_selected):
                self.pawn_to_upgrade = self.piece_selected
                self.view.get_upgrade_pawn(self.model.turn)  #This updates the tile the pawn moved to
                self.send_ins(NetworkIns.UPGRADE_PAWN.value, old_location, sel_location)
            else:
                self.send_ins(NetworkIns.MOVE_PIECE.value, old_location, sel_location)

            self.clear_selection()
            self.pass_turn()

        #Select a piece
        elif piece and self.piece_selected is not piece and piece.color == self.model.turn:
            self.clear_selection()
            self.view.highlight(tile, "blue")
            self.piece_selected = piece
            self.selected_locations = piece.get_locations()
            for loc in self.selected_locations:
                self.view.highlight(self.view.get_tile(loc), "green")

        #Deselect piece
        else:
            self.clear_selection()


    def perform_move(self, old_location, new_location):
        '''
        Moves the piece at old_location to new_location and update visuals
        '''
        piece = self.model.get_piece(old_location)
        self.model.move_piece(piece, new_location)
        
        #Castling
        if len(new_location) == 3:
            for loc in [(piece.row, i) for i in range(0, 8)]:
                p = self.model.get_piece(loc)
                self.view.update_tile(loc, *self.get_image(p))
        
        #Normal Move
        else:
            self.view.update_tile(old_location, None, None)
            self.view.update_tile(new_location, *self.get_image(piece))


    def upgrade_pawn(self, new_type):
        '''
        Called from view, once the user has selected which piece the pawn should be upgraded to.
        '''
        self.model.transform_pawn(self.pawn_to_upgrade, new_type)
        loc = (self.pawn_to_upgrade.row, self.pawn_to_upgrade.column)
        self.view.update_tile(loc, *self.get_image(self.model.get_piece(loc)))
        self.pawn_to_upgrade = None


    def update_lost_piece(self, color, piece_name, new_value):
        '''
        Tells the view to update visuals for the pieces lost count
        '''
        self.view.update_pieces_lost(color, piece_name, new_value)


    def end_game(self, win_con, override_winner=None):
        '''
        Called by model, timer, and controller, when a player has won the game.
        '''
        self.timer.pause()
        if (self.online_player and isinstance(self.online_player.host, Server) and 
        self.online_player.receiving_instruction and win_con == "Timer"):
            return

        self.win_con = win_con
        if override_winner is not None:
            self.win_color = override_winner
        else:
            self.win_color = WHITE if self.model.turn == BLACK else BLACK
        
        if self.online_player and self.online_player.host and win_con == "Timer":
            self.send_ins(NetworkIns.DECLARE_WINNER.value)
        
        self.view.show_winner(self.win_color, self.win_con)


    def play_vs_ai(self):
        '''
        Went view play button is clicked from main menu
        '''
        self.game_type = GameType.AI.value
        self.new_game()


    def agent_move(self):
        '''
        Gets the move from the AI and performs the move
        '''
        state = self.agent.get_state()
        piece, row, column = self.agent.get_action_from_model(state)
        old_location = (piece.row, piece.column)
        new_location = self.agent.include_castling_if(piece, (row, column))
        self.perform_move(old_location, new_location)
        if self.model.check_pawn_end(piece):
            self.pawn_to_upgrade = piece
            self.upgrade_pawn("Queen")
        self.pass_turn()


    def set_lobby_both_connected(self):
        '''
        Updates players connected list in the view when both hosts are in the lobby
        '''
        color = "White" if self.online_player.color == WHITE else "Black"
        other_color = "White" if self.online_player.color == BLACK else "Black"
        self.view.menu.update_connected(1, f"{self.online_player.host.server_ip} ({other_color})")
        self.view.menu.update_connected(2, f"{self.online_player.host.client_ip} ({color})")


    def play_again(self):
        '''
        Called when the play again button is pressed in the popup postgame
        '''           
        if self.online_player:

            if not self.online_player.host.socket_live:
                self.return_to_main()
                return

            if isinstance(self.online_player.host, Server):
                self.view.menu.update_connected(2, "Connecting...")
                self.view.menu.start_button.configure(state="disabled")
                self.send_ins(NetworkIns.REJOINED_LOBBY.value)

            elif isinstance(self.online_player.host, Client):
                self.view.menu.update_connected(1, "Connecting...")

            self.view.hide_ingame_frame()
            self.view.show_menu_frame()
            self.view.menu.hide_main_menu()
            self.view.menu.show_lobby_menu()

        else:
            self.new_game()


    def return_to_main(self):
        '''
        Called when the return to main button is pressed in the popup postgame
        or when play again is clicked but the connection is now closed
        '''
        self.game_type = GameType.NONE.value
        self.view.hide_ingame_frame()
        self.view.show_menu_frame()
        self.close_connections()


    def client_join_status(self, status):
        '''
        Client notifies controller whether the client was able to join a lobby
        '''
        if status:
            self.view.menu.hide_join_menu()
            self.view.menu.show_lobby_menu()
            self.set_lobby_both_connected()
        else:
            self.view.menu.connect_button.configure(state="active")
            self.view.menu.join_back_button.configure(state="active")


    def server_join_status(self, status):
        '''
        Server notifies controller that a client has joined the loby
        '''
        if self.view.active_frame == ActiveFrame.LOBBY.value:
            if status:
                other_color = "White" if self.online_player.color == BLACK else "Black"
                self.view.menu.update_connected(2, f"{self.online_player.host.client_ip} ({other_color})")
                self.view.menu.start_button.configure(state="active")
            else:
                self.view.menu.update_connected(2, "Open")
                self.view.menu.start_button.configure(state="disabled")


    def connection_ended(self):
        '''
        Server or Client notifies controller that their connection has ended
        '''
        if self.view.active_frame == ActiveFrame.LOBBY.value:
            self.view.menu.hide_lobby_menu()
            self.view.menu.show_main_menu()

        elif self.view.active_frame == ActiveFrame.IN_GAME.value:
            self.end_game("Disconnected", override_winner=self.online_player.color)


    def join_game(self, port, server_ip):
        '''
        Connects client to a server.
        '''
        self.player_color = BLACK
        self.online_player = OnlinePlayer(self, self.player_color, NetworkHost.CLIENT.value, int(port), server_ip)


    def host_on_port(self, port):
        '''
        Verify port is in range and create server object
        '''
        port = int(port)
        if port >= 49152 and port <= 65536:
            self.view.menu.hide_host_menu()
            self.view.menu.show_lobby_menu()
            self.player_color = WHITE
            self.online_player = OnlinePlayer(self, self.player_color, NetworkHost.SERVER.value, port)
            color = "White" if self.online_player.color == WHITE else "Black"
            self.view.menu.update_connected(1, f"{self.online_player.host.server_ip} ({color})")
            self.view.menu.update_connected(2, "Open")


    def close_connections(self):
        '''
        Gracefully close the server and client connections and join threads
        '''
        if self.online_player:
            if self.online_player.host:
                self.online_player.disconnect()
            del self.online_player
            self.online_player = None
        self.game_type = GameType.NONE.value


    def update_network_timer(self, value):
        '''
        Updates the timer only for the client, according to the servers timer
        '''
        if isinstance(self.online_player.host, Client):
            self.timer.set_current_interval(value)
            self.view.update_timer(self.model.turn)


    def send_ins(self, value, *args):
        '''
        Packages information and sends to other host
        '''
        if self.game_type == GameType.NETWORK.value:
            
            if value == NetworkIns.NEW_GAME.value:
                self.online_player.send_as_bytes(value, self.timer.get_current_interval())

            elif value == NetworkIns.UPDATE_TIMER.value:
                self.online_player.send_as_bytes(value, self.timer.get_current_interval())
        
            elif value == NetworkIns.MOVE_PIECE.value:
                self.online_player.send_as_bytes(value, self.timer.get_current_interval(), *args)

            elif value == NetworkIns.UPGRADE_PAWN.value:
                piece_type = type(self.model.get_piece(args[1])).__name__
                self.online_player.send_as_bytes(value, self.timer.get_current_interval(), *args, piece_type)

            elif value == NetworkIns.DECLARE_WINNER.value:
                self.online_player.send_as_bytes(value, self.timer.get_current_interval(), self.win_con, self.win_color)

            elif value == NetworkIns.REJOINED_LOBBY.value:
                self.online_player.send_as_bytes(value, *args)


    def execute_instructions(self, data):
        '''
        Execute the instructions received from the client/server
        '''
        if data[0] == NetworkIns.NEW_GAME.value:
            self.new_game()

        elif data[0] == NetworkIns.UPDATE_TIMER.value:
            self.update_network_timer(data[1])

        elif data[0] == NetworkIns.MOVE_PIECE.value:
            self.update_network_timer(data[1])
            self.perform_move((data[2], data[3]), tuple(data[4:])) #could be castling move, last tuple would be len 3
            self.pass_turn()

        elif data[0] == NetworkIns.UPGRADE_PAWN.value:
            self.update_network_timer(data[1])
            self.perform_move((data[2], data[3]), (data[4], data[5]))
            self.pawn_to_upgrade = self.model.get_piece((data[4], data[5]))
            self.upgrade_pawn(data[6])
            self.pass_turn()

        elif data[0] == NetworkIns.DECLARE_WINNER.value:
            self.update_network_timer(data[1])
            self.view.update_timer(self.model.turn)
            self.end_game(data[2], data[3])

        #Server repeatedly says to client, "I'm in new lobby, are you in lobby?" until client in lobby or disconnects
        elif data[0] == NetworkIns.REJOINED_LOBBY.value:
            
            if isinstance(self.online_player.host, Client):
                in_lobby = 1 if self.view.active_frame == ActiveFrame.LOBBY.value else 0
                self.send_ins(NetworkIns.REJOINED_LOBBY.value, in_lobby)
                self.set_lobby_both_connected()
            
            elif isinstance(self.online_player.host, Server):
                if data[1] == 0:
                    self.send_ins(NetworkIns.REJOINED_LOBBY.value)
                elif data[1] == 1:
                    self.set_lobby_both_connected()
                    self.view.menu.start_button.configure(state="active")

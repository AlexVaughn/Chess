import tkinter as tk
from PIL import Image, ImageTk
from Game.controller import Controller
from Game.constants import *

BG_COLOR = '#282828'
BASE_BOARD_COLOR = "black"
BOARD_COLOR_1 = "#ebd1a5"
BOARD_COLOR_2 = "#412614"
TURN_BORDER_COLOR = "white"
WARNING_COLOR = "red"
ASSESTS_PATH  = "Assets/"


class App(tk.Tk):

    def __init__(self):
        
        self.controller = Controller(self)
        self.highlighted = []
        self.tiles = []
        self.popup_quit = None
        self.active_frame = ActiveFrame(ActiveFrame.MAIN.value)

        #Initialize window properties
        self.width = 1200
        self.height = 700
        self.padding = 30
        self.board_len = self.height - self.padding*2
        super().__init__()
        self.title("Chess")
        self.configure(bg=BG_COLOR)
        self.wm_minsize(self.width, self.height)
        self.resizable(width=False, height=False)
        self.protocol("WM_DELETE_WINDOW", self.close)   #Calls self.close() when the root window is closed
        self.geometry("{}x{}+{}+{}".format(self.width, self.height,
            int(self.winfo_screenwidth()/2 - self.width/2),
            int(self.winfo_screenheight()/2 - self.height/2)))
        
        #Load images
        self.image_len = 50
        self.images = {
            WHITE:{
                "Pawn": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "w_pawn.png").resize((self.image_len, self.image_len))),
                "Rook": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "w_rook.png").resize((self.image_len, self.image_len))),
                "Knight": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "w_knight.png").resize((self.image_len, self.image_len))),
                "Bishop": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "w_bishop.png").resize((self.image_len, self.image_len))),
                "Queen": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "w_queen.png").resize((self.image_len, self.image_len))),
                "King": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "w_king.png").resize((self.image_len, self.image_len))),
            },
            BLACK:{
                "Pawn": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "b_pawn.png").resize((self.image_len, self.image_len))),
                "Rook": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "b_rook.png").resize((self.image_len, self.image_len))),
                "Knight": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "b_knight.png").resize((self.image_len, self.image_len))),
                "Bishop": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "b_bishop.png").resize((self.image_len, self.image_len))),
                "Queen": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "b_queen.png").resize((self.image_len, self.image_len))),
                "King": ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "b_king.png").resize((self.image_len, self.image_len))),
            },
            None:{None: ""}
        }
   
        self.color_settings = {
            WHITE:{
                "text": "White",
                "image_color": 'w',
                "bg": BOARD_COLOR_1,
                "fg": BOARD_COLOR_2
            },
            BLACK:{
                "text": "Black",
                "image_color": 'b',
                "bg": BOARD_COLOR_2,
                "fg": BOARD_COLOR_1
            }
        }

        #Fill window with content
        self.main_frame = tk.Frame(self, bg=BG_COLOR)
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        self.menu = Menu(self.main_frame, self.width, self.height)
        self.ingame_frame = tk.Frame(self.main_frame, bg=BG_COLOR)      
        self.white_panel = Panel(self.ingame_frame, WHITE)
        self.board = Board(self.ingame_frame, self.board_len)
        self.black_panel = Panel(self.ingame_frame, BLACK)
        self.show_ingame_frame()
        self.hide_ingame_frame()
        self.show_menu_frame()

        self.pieces_lost = {
            WHITE:{
                "Pawns": self.white_panel.pawns_text,
                "Rooks": self.white_panel.rooks_text,
                "Knights": self.white_panel.knights_text,
                "Bishops": self.white_panel.bishops_text,
                "Queens": self.white_panel.queens_text
            },
            BLACK:{
                "Pawns": self.black_panel.pawns_text,
                "Rooks": self.black_panel.rooks_text,
                "Knights": self.black_panel.knights_text,
                "Bishops": self.black_panel.bishops_text,
                "Queens": self.black_panel.queens_text
            }
        }


    def start(self):
        '''
        Starts the app
        '''
        self.controller.timer.start()
        self.controller.timer.pause()
        self.mainloop()


    def close(self):
        '''
        Closes the app
        '''
        self.closing_app = True
        self.controller.timer.cancel() #This should be called first because timer calls gui functions
        self.controller.close_connections()
        self.destroy()


    def show_menu_frame(self):
        '''
        Display the main menu
        '''
        self.menu.show_main_menu()
        self.menu.pack(expand=True, fill=tk.BOTH)
        self.menu.pack_propagate(0)
        self.active_frame = 1


    def hide_menu_frame(self):
        '''
        Hide the main menu
        '''
        self.menu.pack_forget()


    def show_ingame_frame(self):
        '''
        Display the in game frame
        '''
        self.ingame_frame.pack(expand=True, fill=tk.BOTH, padx=self.padding, pady=self.padding)
        self.ingame_frame.pack_propagate(0)        
        self.white_panel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.white_panel.pack_propagate(0)
        self.board.pack(side=tk.LEFT, fill=tk.BOTH, padx=self.padding)
        self.board.pack_propagate(0)
        self.black_panel.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self.black_panel.pack_propagate(0)
        self.active_frame = 2


    def hide_ingame_frame(self):
        '''
        Hide the in game frame
        '''
        self.ingame_frame.pack_forget()
        self.white_panel.pack_forget()
        self.board.pack_forget()
        self.black_panel.pack_forget()


    def new_game(self):
        '''
        Update visuals for a new game
        '''
        self.menu.hide_lobby_menu()
        self.hide_menu_frame()
        self.show_ingame_frame()

        minutes = (self.controller.time_limit - 3) // 60
        seconds = (self.controller.time_limit - 3) % 60
        self.white_panel.timer_text.configure(text="Timer   %d:%02d" % (minutes, seconds),
            fg=self.color_settings[WHITE]['fg'])
        self.white_panel.configure(bg=TURN_BORDER_COLOR)
        self.black_panel.timer_text.configure(text="Timer   0:00", fg=self.color_settings[BLACK]['fg'])
        self.black_panel.configure(bg=self.color_settings[BLACK]['bg'])

        #Reset pieces lost
        for k1 in self.pieces_lost:
            for k2 in self.pieces_lost[k1]:
                self.pieces_lost[k1][k2].configure(text="0")


    def get_tile(self, location) -> "Tile":
        '''
        Returns the tile at the given location.
        '''
        return self.tiles[location[0]][location[1]]


    def update_tile(self, location, color, piece_name):
        '''
        Update the visuals for the tile at given (row, column) with given image key.
        '''
        self.tiles[location[0]][location[1]].label.configure(image=self.images[color][piece_name])


    def highlight(self, tile, color):
        '''
        Highlights the given tile with the given color, adds tile to highlighted list.
        '''
        tile.label.configure(highlightbackground=color, highlightthickness=3)
        self.highlighted.append(tile)


    def remove_highlights(self):
        '''
        Removes highlights from tiles in the highlited list.
        '''
        for tile in self.highlighted:
            tile.label.configure(highlightthickness=0)


    def get_upgrade_pawn(self, color):
        '''
        Create a popup that prompts the user to choose which piece the pawn should be upgraded to.
        '''
        popup = PawnPopup(self, color)
        self.wait_window(popup)


    def show_winner(self, color, cond):
        '''
        Creates a pop that states who won the game, prompt user to play again.
        '''
        if not self.popup_quit:
            self.popup_quit = WinPopup(self, color, cond)


    def update_pieces_lost(self, color, piece_name, new_value):
        '''
        Sets the new value of pieces lost in the correct panel.
        '''
        self.pieces_lost[color][piece_name].configure(text=str(new_value))


    def update_timer(self, color):
        '''
        Changes the text in the correct panel to match the timers value
        '''
        total_seconds = self.controller.time_limit - self.controller.timer.get_current_interval() - 3
        if total_seconds < 0: total_seconds = 0
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if color == BLACK:
            self.black_panel.timer_text.configure(text="Timer   %d:%02d" % (minutes, seconds))
            if total_seconds <= 10: self.black_panel.timer_text.configure(fg=WARNING_COLOR)
        else:
            self.white_panel.timer_text.configure(text="Timer   %d:%02d" % (minutes, seconds))
            if total_seconds <= 10: self.white_panel.timer_text.configure(fg=WARNING_COLOR)
        

    def pass_turn(self, color):
        '''
        Reset timer and turn indicator.
        '''
        minutes = (self.controller.time_limit - 3) // 60
        seconds = (self.controller.time_limit - 3) % 60

        #It is now black's turn
        if color == BLACK:
            self.white_panel.timer_text.configure(text="Timer   0:00", fg=self.color_settings[WHITE]['fg'])
            self.white_panel.configure(bg=self.color_settings[WHITE]['bg'])
            self.black_panel.timer_text.configure(text="Timer   %d:%02d" % (minutes, seconds), 
                fg=self.color_settings[BLACK]['fg'])
            self.black_panel.configure(bg=TURN_BORDER_COLOR)
        
        #It is now white's turn
        else:
            self.black_panel.timer_text.configure(text="Timer   0:00", fg=self.color_settings[BLACK]['fg'])
            self.black_panel.configure(bg=self.color_settings[BLACK]['bg'])
            self.white_panel.timer_text.configure(text="Timer   %d:%02d" % (minutes, seconds),
                fg=self.color_settings[WHITE]['fg'])
            self.white_panel.configure(bg=TURN_BORDER_COLOR)


class Menu(tk.Canvas):

    def __init__(self, master, width, height):
        self.padding = 10
        self.main_bg_image = ImageTk.PhotoImage(Image.open(ASSESTS_PATH + "main_background.png"))
        super().__init__(master=master, width=width, height=height, highlightthickness=0, bd=0)
        self.create_image(0, 0, anchor=tk.NW, image=self.main_bg_image)

        #Main Menu
        self.main_menu = tk.Frame(self, bg=BG_COLOR, highlightbackground=BOARD_COLOR_1, highlightthickness=3, bd=0)
        self.main_menu.pack(expand=True, fill=tk.BOTH)
        self.chess_title = tk.Label(self.main_menu, text="Chess", font=('Comic Sans MS', 70), bg=BG_COLOR, fg=BOARD_COLOR_1)
        self.chess_title.pack(padx=self.padding, pady=20)
        self.play_button = BorderButton(self.main_menu, text="Play", command=self.play)
        self.play_button.pack(padx=self.padding, pady=self.padding)        
        self.host_button = BorderButton(self.main_menu, text="Host", command=self.host)
        self.host_button.pack(padx=self.padding, pady=self.padding)
        self.join_button = BorderButton(self.main_menu, text="Join", command=self.join)
        self.join_button.pack(padx=self.padding, pady=self.padding)
        self.quit_button = BorderButton(self.main_menu, text="Quit", command=self.master.master.close)
        self.quit_button.pack(padx=self.padding, pady=self.padding)
        self.hide_main_menu()

        #Host Menu
        self.host_menu = tk.Frame(self, bg=BG_COLOR, highlightbackground=BOARD_COLOR_1, highlightthickness=3, bd=0)
        self.host_menu.pack(expand=True, fill=tk.BOTH, padx=400, pady=200)
        self.enter_port_label = tk.Label(self.host_menu, bg=BG_COLOR, text="Enter a Port Number\n(49152 to 65536)", 
                                    font=('Comic Sans MS', 15), fg=BOARD_COLOR_1)
        self.enter_port_label.pack(padx=self.padding, pady=25)
        v3 = tk.StringVar(self.host_menu, value="65000")
        self.enter_port_field = tk.Entry(self.host_menu, bg=BG_COLOR, background=BOARD_COLOR_2, foreground=BOARD_COLOR_1, 
                                font=('Comic Sans MS', 15), justify="center", highlightbackground=BOARD_COLOR_1, 
                                highlightthickness=3, bd=0, textvariable=v3)  #temp text
        self.enter_port_field.pack(padx=self.padding, pady=self.padding)
        self.create_button = BorderButton(self.host_menu, text="Create Lobby", command=self.create_lobby)
        self.create_button.pack(padx=self.padding, pady=(200, self.padding))
        self.host_back_button = BorderButton(self.host_menu, text="Back", command=self.host_back)
        self.host_back_button.pack(padx=self.padding, pady=self.padding)
        self.hide_host_menu()

        #Lobby Menu
        self.lobby_menu = tk.Frame(self, bg=BG_COLOR, highlightbackground=BOARD_COLOR_1, highlightthickness=3, bd=0)
        self.lobby_menu.pack(expand=True, fill=tk.BOTH, padx=400, pady=200)
        self.player1_label = tk.Label(self.lobby_menu, bg=BG_COLOR, text="Open", 
                                background=BOARD_COLOR_2, font=('Comic Sans MS', 15), foreground=BOARD_COLOR_1,
                                highlightbackground=BOARD_COLOR_1, highlightthickness=3, height=2, width=20)
        self.player1_label.pack(padx=self.padding, pady=(40, self.padding))
        self.vs_label = tk.Label(self.lobby_menu, bg=BG_COLOR, text="VS", background=BG_COLOR, 
                                font=('Comic Sans MS', 15), foreground=BOARD_COLOR_1)
        self.vs_label.pack(padx=self.padding, pady=self.padding)
        self.player2_label = tk.Label(self.lobby_menu, bg=BG_COLOR, text="Open", 
                                background=BOARD_COLOR_2, font=('Comic Sans MS', 15), foreground=BOARD_COLOR_1, 
                                highlightbackground=BOARD_COLOR_1, highlightthickness=3, height=2, width=20)
        self.player2_label.pack(padx=self.padding, pady=self.padding)
        self.start_button = BorderButton(self.lobby_menu, text="Start Game", command=self.start)
        self.start_button.configure(state="disabled")
        self.start_button.pack(padx=self.padding, pady=(125, self.padding))
        self.leave_button = BorderButton(self.lobby_menu, text="Leave Lobby", command=self.leave_lobby)
        self.leave_button.pack(padx=self.padding, pady=self.padding)
        self.hide_lobby_menu()

        #Join Menu
        self.join_menu = tk.Frame(self, bg=BG_COLOR, highlightbackground=BOARD_COLOR_1, highlightthickness=3, bd=0)
        self.join_menu.pack(expand=True, fill=tk.BOTH, padx=400, pady=200)
        self.ip_label = tk.Label(self.join_menu, text="IP Address", background=BG_COLOR, font=('Comic Sans MS', 15), foreground=BOARD_COLOR_1)
        self.ip_label.pack(padx=self.padding, pady=self.padding)
        v1 = tk.StringVar(self.join_menu, value="10.0.0.242")
        self.ip_field = tk.Entry(self.join_menu, bg=BG_COLOR, background=BOARD_COLOR_2, foreground=BOARD_COLOR_1, 
                                font=('Comic Sans MS', 15), justify="center", highlightbackground=BOARD_COLOR_1, 
                                highlightthickness=3, bd=0, textvariable=v1)  #temp text
        self.ip_field.pack(padx=self.padding, pady=self.padding)
        self.port_label = tk.Label(self.join_menu, text="Port", background=BG_COLOR, font=('Comic Sans MS', 15), foreground=BOARD_COLOR_1)
        self.port_label.pack(padx=self.padding, pady=self.padding)
        v2 = tk.StringVar(self.join_menu, value="65000")
        self.port_field = tk.Entry(self.join_menu, bg=BG_COLOR, background=BOARD_COLOR_2, foreground=BOARD_COLOR_1, 
                                font=('Comic Sans MS', 15), justify="center", highlightbackground=BOARD_COLOR_1, 
                                highlightthickness=3, bd=0, textvariable=v2)    #temp text
        self.port_field.pack(padx=self.padding, pady=self.padding)
        self.connect_button = BorderButton(self.join_menu, text="Connect", command=self.connect)
        self.connect_button.pack(padx=self.padding, pady=(175, self.padding))
        self.join_back_button = BorderButton(self.join_menu, text="Back", command=self.join_back)
        self.join_back_button.pack(padx=self.padding, pady=self.padding)
        self.hide_join_menu()

        self.show_main_menu()


    def show_main_menu(self):
        self.main_menu.pack(expand=True, fill=tk.BOTH, padx=400, pady=65)
        self.master.master.active_frame = 1

    def hide_main_menu(self):
        self.main_menu.pack_forget()

    def show_host_menu(self):
        self.host_menu.pack(expand=True, fill=tk.BOTH, padx=400, pady=65)
        self.master.master.active_frame = 3
    
    def hide_host_menu(self):
        self.host_menu.pack_forget()
    
    def show_lobby_menu(self):
        self.start_button.configure(state="disabled")
        self.lobby_menu.pack(expand=True, fill=tk.BOTH, padx=400, pady=65)
        self.master.master.active_frame = 5

    def hide_lobby_menu(self):
        self.lobby_menu.pack_forget()
    
    def show_join_menu(self):
        self.connect_button.configure(state="active")
        self.join_back_button.configure(state="active")
        self.join_menu.pack(expand=True, fill=tk.BOTH, padx=400, pady=65)
        self.master.master.active_frame = 4

    def hide_join_menu(self):
        self.join_menu.pack_forget()
    
    def play(self):
        self.master.master.controller.play_vs_ai()

    def host(self):
        self.hide_main_menu()
        self.show_host_menu()

    def host_back(self):
        self.hide_host_menu()
        self.show_main_menu()

    def join(self):
        self.hide_main_menu()
        self.show_join_menu()

    def join_back(self):
        self.hide_join_menu()
        self.show_main_menu()

    def create_lobby(self):
        self.master.master.controller.host_on_port(self.enter_port_field.get())

    def start(self):
        self.master.master.controller.new_game()

    def leave_lobby(self):
        self.master.master.controller.close_connections()
        self.hide_lobby_menu()
        self.show_main_menu()

    def connect(self):
        self.connect_button.configure(state="disabled")
        self.join_back_button.configure(state="disabled")
        self.master.master.controller.join_game(self.port_field.get(), self.ip_field.get())

    def update_connected(self, player_slot, player_name):
        if player_slot == 1: self.player1_label.configure(text=player_name)
        elif player_slot == 2: self.player2_label.configure(text=player_name)


class BorderButton(tk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(args[0], highlightbackground=BOARD_COLOR_1, highlightthickness=3, bd=0, height=60, width=200)
        self.button = tk.Button(self, kwargs, foreground=BOARD_COLOR_1, bg=BOARD_COLOR_2, font=('Comic Sans MS', 20),
                                relief="flat", activeforeground=BOARD_COLOR_1, activebackground=BOARD_COLOR_2)
        
    def pack(self, **kwargs):
        super().pack(kwargs)
        super().pack_propagate(0)
        self.button.pack(expand=True, fill=tk.BOTH)

    def configure(self, **kwargs):
        self.button.configure(kwargs)


class Panel(tk.Frame):

    def __init__(self, master, color):
        
        self.vis = master.master.master.color_settings[color]
        self.padding = 20
        self.piece_x_padding = 35
        super().__init__(master=master, bg=self.vis['bg'])

        self.inner_frame = tk.Frame(self, bg=self.vis["bg"])
        self.inner_frame.pack(expand=True, fill=tk.BOTH, padx=self.padding, pady=self.padding)
        
        self.title_frame = tk.Frame(self.inner_frame, bg=self.vis["bg"])
        self.title_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.title_text = tk.Label(self.inner_frame, text=self.vis["text"], bg=self.vis["bg"], 
            fg=self.vis["fg"], font=('Comic Sans MS', 30, "underline"))
        self.title_text.pack()
        
        self.timer_frame = tk.Frame(self.inner_frame, bg=self.vis["bg"])
        self.timer_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.timer_text = tk.Label(self.inner_frame, text=f"Timer   0:00", bg=self.vis["bg"], 
            fg=self.vis["fg"], font=('Comic Sans MS', 15))
        self.timer_text.pack()

        self.pieces_lost_frame = tk.Frame(self.inner_frame, bg=self.vis["bg"])
        self.pieces_lost_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.lost_text = tk.Label(self.inner_frame, text="Pieces Lost", bg=self.vis["bg"], 
            fg=self.vis["fg"], font=('Comic Sans MS', 15))
        self.lost_text.pack()

        self.pawns_frame = tk.Frame(self.inner_frame, bg=self.vis["bg"])
        self.pawns_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.pawns_label = tk.Label(self.pawns_frame, 
            image=self.master.master.master.images[color]['Pawn'], bg=self.vis["bg"])
        self.pawns_label.pack(side=tk.LEFT, padx=self.piece_x_padding)
        self.pawns_text = tk.Label(self.pawns_frame, text="0", bg=self.vis["bg"], 
            fg=self.vis["fg"], font=('Comic Sans MS', 15))
        self.pawns_text.pack(side=tk.LEFT)

        self.rooks_frame = tk.Frame(self.inner_frame, bg=self.vis["bg"])
        self.rooks_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.rooks_label = tk.Label(self.rooks_frame, 
            image=self.master.master.master.images[color]['Rook'], bg=self.vis["bg"])
        self.rooks_label.pack(side=tk.LEFT, padx=self.piece_x_padding)
        self.rooks_text = tk.Label(self.rooks_frame, text="0", bg=self.vis["bg"], 
            fg=self.vis["fg"], font=('Comic Sans MS', 15))
        self.rooks_text.pack(side=tk.LEFT)

        self.knights_frame = tk.Frame(self.inner_frame, bg=self.vis["bg"])
        self.knights_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.knights_label = tk.Label(self.knights_frame, 
            image=self.master.master.master.images[color]['Knight'], bg=self.vis["bg"])
        self.knights_label.pack(side=tk.LEFT, padx=self.piece_x_padding)
        self.knights_text = tk.Label(self.knights_frame, text="0", bg=self.vis["bg"],
            fg=self.vis["fg"], font=('Comic Sans MS', 15))
        self.knights_text.pack(side=tk.LEFT)

        self.bishops_frame = tk.Frame(self.inner_frame, bg=self.vis["bg"])
        self.bishops_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.bishops_label = tk.Label(self.bishops_frame, 
            image=self.master.master.master.images[color]['Bishop'], bg=self.vis["bg"])
        self.bishops_label.pack(side=tk.LEFT, padx=self.piece_x_padding)
        self.bishops_text = tk.Label(self.bishops_frame, text="0", bg=self.vis["bg"], 
            fg=self.vis["fg"], font=('Comic Sans MS', 15))
        self.bishops_text.pack(side=tk.LEFT)

        self.queens_frame = tk.Frame(self.inner_frame, bg=self.vis["bg"])
        self.queens_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.queens_label = tk.Label(self.queens_frame, 
            image=self.master.master.master.images[color]['Queen'], bg=self.vis["bg"])
        self.queens_label.pack(side=tk.LEFT, padx=self.piece_x_padding)
        self.queens_text = tk.Label(self.queens_frame, text="0", bg=self.vis["bg"], 
            fg=self.vis["fg"], font=('Comic Sans MS', 15))
        self.queens_text.pack(side=tk.LEFT)


class Board(tk.Frame):

    def __init__(self, master, length):
        
        self.length = length
        self.padding = 20
        self.tile_len = int((self.length - self.padding*2) / 8)
        self.selected_tile = None
        super().__init__(master=master, width=self.length, height=self.length, bg=BASE_BOARD_COLOR)
        self.tile_frame = tk.Frame(self, bg=BG_COLOR)
        self.tile_frame.pack(expand=True, fill=tk.BOTH, padx=self.padding, pady=self.padding)

        #Create rows, each holds 8 tiles
        for i in range(8):
            row_frame = tk.Frame(self.tile_frame)
            row_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
            offset = 0 if i % 2 == 0 else 1
            self.master.master.master.tiles.append(list())

            #Create tiles in row
            for j in range(8):
                color = BOARD_COLOR_1 if (j+offset) % 2 == 0 else BOARD_COLOR_2
                tile = Tile(row_frame, i, j, color)
                tile.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
                tile.pack_propagate(0)
                self.master.master.master.tiles[i].append(tile)


class Tile(tk.Frame):

    def __init__(self, master, row, column, color):

        self.row = row
        self.column = column
        super().__init__(master=master, bg=color)
        self.label = tk.Label(self, bg=color)
        self.label.pack(expand=True, fill=tk.BOTH)
        self.label.bind("<Button 1>", self.left_click)

    
    def left_click(self, event):
        '''
        Notify the controller that this tile has been clicked
        '''
        #tile . row_frame . tile_frame . board . ingame_frame . main_frame . app . controller
        self.master.master.master.master.master.master.controller.tile_clicked(self)  


class PawnPopup(tk.Toplevel):
    """
    Asks user which piece the pawn should be upgraded to
    """
    def __init__(self, master, color):

        #Initialize window properties
        self.vis = master.color_settings[color]
        self.width = 375
        self.height = 150
        self.padding = 10
        super().__init__()
        self.transient(master)   #Set the popup to be on top of the main window
        self.grab_set()          #Ignore clicks in the main window while the popup is open
        self.title("Upgrade Pawn")
        self.protocol("WM_DELETE_WINDOW", lambda: None)   #Disable clicking "x"
        self.configure(bg=BG_COLOR)
        self.resizable(width=False, height=False)
        self.geometry("{}x{}+{}+{}".format(self.width, self.height,
                                            int(master.winfo_screenwidth()/2 - self.width/2),
                                            int(master.winfo_screenheight()/2 - self.height/2)))

        #Fill window with content
        self.ingame_frame = tk.Frame(self, bg=BG_COLOR)
        self.ingame_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.message_frame = tk.Frame(self.ingame_frame, bg=self.vis['bg'])
        self.message_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.message_text = tk.Label(self.message_frame, text="Select an upgrade for your pawn",
                            font=('Comic Sans MS', 15), bg=self.vis['bg'], fg=self.vis['fg'])
        self.message_text.pack(pady=(10,0))
        
        self.buttons_frame = tk.Frame(self.ingame_frame, bg=self.vis['bg'])
        self.buttons_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.queen_btn = tk.Button(self.buttons_frame, image=master.images[color]['Queen'],
                            bg=self.vis['bg'], command=lambda: self.send_input("Queen"))
        self.queen_btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=self.padding, pady=self.padding)

        self.rook_btn = tk.Button(self.buttons_frame, image=master.images[color]['Rook'],
                            bg=self.vis['bg'], command=lambda: self.send_input("Rook"))
        self.rook_btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=self.padding, pady=self.padding)

        self.knight_btn = tk.Button(self.buttons_frame, image=master.images[color]['Knight'],
                            bg=self.vis['bg'], command=lambda: self.send_input("Knight"))
        self.knight_btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=self.padding, pady=self.padding)

        self.bishop_btn = tk.Button(self.buttons_frame, image=master.images[color]['Bishop'],
                            bg=self.vis['bg'], command=lambda: self.send_input("Bishop"))
        self.bishop_btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=self.padding, pady=self.padding)

    
    def send_input(self, new_type):
        '''
        Action to perform once button is clicked.
        '''
        self.master.controller.upgrade_pawn(new_type)
        self.destroy()


class WinPopup(tk.Toplevel):
    """
    Displays ther winner, prompts user to play again
    """

    def __init__(self, master, color, cond):

        #Initialize window properties
        self.vis = master.color_settings[color]
        self.width = 375
        self.height = 340
        self.padding = 5
        super().__init__()
        self.transient(master)   #Set the popup to be on top of the main window
        self.grab_set()          #Ignore clicks in the main window while the popup is open
        self.title("Game Complete")
        self.protocol("WM_DELETE_WINDOW", lambda: None)  #Disable clicking "x"
        self.configure(bg=BG_COLOR)
        self.resizable(width=False, height=False)
        self.geometry("{}x{}+{}+{}".format(self.width, self.height,
             int(master.winfo_x() + master.width/2 - self.width/2),
             int(master.winfo_y() + master.height/2 - self.height/2)))
        
        #Fill window with content
        self.ingame_frame = tk.Frame(self, bg=BG_COLOR)
        self.ingame_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        message = "Draw!" if cond == "Stalemate" else f"{self.vis['text']} Wins!"
        self.message_frame = tk.Frame(self.ingame_frame, bg=self.vis['bg'])
        self.message_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.message_text = tk.Label(self.message_frame, text=message,
            font=('Comic Sans MS', 30), bg=self.vis['bg'], fg=self.vis['fg'])
        self.message_text.pack(pady=(10,0))
        
        self.cond_text = tk.Label(self.message_frame, text=f"Condition: {cond}",
            font=('Comic Sans MS', 15), bg=self.vis['bg'], fg=self.vis['fg'])
        self.cond_text.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        
        self.buttons_frame = tk.Frame(self.ingame_frame, bg=self.vis['bg'])
        self.buttons_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.play_again_btn = tk.Button(self.buttons_frame, text="Play Again", font=('Comic Sans MS', 15),
            bg=self.vis['bg'], fg=self.vis['fg'], command=self.play_again)
        self.play_again_btn.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=(20, self.padding))
        
        self.ret_main_btn = tk.Button(self.buttons_frame, text="Return to Main", font=('Comic Sans MS', 15),
            bg=self.vis['bg'], fg=self.vis['fg'], command=self.return_main)
        self.ret_main_btn.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=self.padding)

        self.quit_btn = tk.Button(self.buttons_frame, text="Quit", font=('Comic Sans MS', 15),
            bg=self.vis['bg'], fg=self.vis['fg'], command=self.master.close)
        self.quit_btn.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=(self.padding, 15))


    def play_again(self):
        '''
        Action to perform when play again button is clicked.
        '''
        self.master.controller.play_again()
        self.master.popup_quit = None
        self.destroy()
        

    def return_main(self):
        '''
        Action to perform when return to main is clicked
        '''
        self.master.controller.return_to_main()
        self.master.popup_quit = None
        self.destroy()

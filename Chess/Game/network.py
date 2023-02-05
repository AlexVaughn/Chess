import socket
from time import sleep
from threading import Thread
from Game.constants import *


class OnlinePlayer:

    def __init__(self, *args):
        self.controller = args[0]
        self.color = args[1]
        self.data_limit = 1024
        self.closing_connection = False
        self.receiving_instruction = False

        if args[2] == NetworkHost.SERVER.value:
            self.host = Server(self, *args[3:])
        elif args[2] == NetworkHost.CLIENT.value:
            self.host = Client(self, *args[3:])
        else:
            raise ValueError("Expected enum NetworkHost as args[2]")


    def disconnect(self):
        '''
        Gracefully close the server and client connections, join threads, and del objects
        '''
        if self.host:
            self.closing_connection = True
            self.host.close_connection()
            self.closing_connection = False
            del self.host


    def send_as_bytes(self, *args):
        '''
        Turn instructions into byte format so they can be sent across the network.
        Then send instructions.
        '''
        string = ""
        for arg in args:
            if isinstance(arg, tuple):
                for i in arg:
                    string += str(i) + ","
            else:
                string += str(arg) + ","
        self.host.data_to_send = bytes(string[:-1], 'utf-8')
 

    def receive_ins(self, byte_string):
        '''
        Decode the receive byte string and tell controller to execute the instructions.
        '''
        self.receiving_instruction = True
        data = byte_string.decode('utf-8').split(",")
        for i in range(len(data)):
            try: data[i] = int(data[i])
            except: pass
        if data[0] != 0:
            self.controller.execute_instructions(data)
        self.receiving_instruction = False


class Server(Thread):

    def __init__(self, player, port):
        self.player = player
        self.port = port
        self.server_ip = socket.gethostbyname(socket.gethostname())
        self.client_ip = ""
        self.data_to_send = b""
        self.conn = None
        self.s = None
        self.socket_live = False
        super().__init__(target=self.open_connection)
        self.start()


    def open_connection(self):
        '''
        Allow server to accept connections
        '''
        self.socket_live = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
            self.s.bind((self.server_ip, self.port))
            self.s.listen()

            while True:
                try: self.conn, addr = self.s.accept()
                except: break
                self.client_ip = addr[0]
                self.player.controller.server_join_status(True)
                self.send_recv_data()

                if not self.player.closing_connection:
                    self.player.controller.server_join_status(False)

                if self.player.controller.view.active_frame == ActiveFrame.IN_GAME.value:
                    break
        
        if not self.player.closing_connection:
            self.player.controller.connection_ended()

        self.socket_live = False
            

    def send_recv_data(self):
        '''
        Send and receive data every time interval 
        '''
        with self.conn:
            while True:
                try:
                    if self.data_to_send:
                        self.conn.sendall(self.data_to_send)
                        self.data_to_send = b""
                    elif (self.player.controller.view.active_frame == ActiveFrame.IN_GAME.value
                    and self.player.controller.win_color is None):
                        self.player.controller.send_ins(NetworkIns.UPDATE_TIMER.value)
                        self.conn.sendall(self.data_to_send)
                        self.data_to_send = b""
                    else:
                        self.conn.sendall(b"0")
                    data = self.conn.recv(self.player.data_limit)
                    if not data: break
                    self.player.receive_ins(data)
                    sleep(1)
                except:
                    break
        self.client_ip = ""
        

    def close_connection(self):
        '''
        Gracefully close the server connection and thread
        '''
        if self.conn:
            self.conn.close()
        if self.s:
            self.s.close()
            self.socket_live = False
        if self.is_alive():
            self.join()


class Client(Thread):
    
    def __init__(self, player, port, server_ip):
        self.player = player
        self.port = port
        self.server_ip = server_ip
        self.client_ip = socket.gethostbyname(socket.gethostname())
        self.data_to_send = ""
        self.s = None
        self.socket_live = False
        super().__init__(target=self.open_connection)
        self.start()


    def open_connection(self):
        '''
        Connect client to server
        '''
        self.socket_live = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
            try:
                self.s.connect((self.server_ip, self.port))
                self.player.controller.client_join_status(True)
            except:
                self.player.controller.client_join_status(False)
                return
            self.send_recv_data()
        
        if not self.player.closing_connection:
            self.player.controller.connection_ended()
        
        self.socket_live = False


    def send_recv_data(self):
        '''
        Receive data, then instantly send data
        '''
        with self.s:
            while True:
                try:
                    data = self.s.recv(self.player.data_limit)
                    if not data: break
                    self.player.receive_ins(data)
                    if self.data_to_send:
                        self.s.sendall(self.data_to_send)
                        self.data_to_send = b""
                    else:
                        self.s.sendall(b"0")
                except:
                    break


    def close_connection(self):
        '''
        Gracefully close the client connection and thread
        '''
        if self.s:
            self.s.close()
            self.socket_live = False
        if self.is_alive():
            self.join()

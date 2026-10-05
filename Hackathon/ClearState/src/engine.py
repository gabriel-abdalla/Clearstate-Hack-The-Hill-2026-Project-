import pygame
import sys
import socket
import threading
import json
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK
from src.modules.push_button import Push_Button
from src.screens import MainMenu, Setup, Help

'''
#setup base host and port 
HOST = "127.0.0.1"
PORT = 5000

global latest_apps
latest_apps = [] #receiving all apps
'''

class Game:
    def __init__(self, initial_state="MAIN_MENU"):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.running = True
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))    
        
        self.state_dict = {
            "MAIN_MENU": MainMenu(),
            "SETUP": Setup(),
            "HELP": Help()
        }
        
        self.active_state_name = initial_state
        self.state = self.state_dict[self.active_state_name]
        self.all_sprites = [] #USE FOR SPRITE GROUPS
    '''
    def receive_apps():
    
            #server setup
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((HOST, PORT))
            server.listen(1)
    
            connection, address = server.accept() #function pauses unless a connection is made (if script isnt open)
    
            buffer = "" #collect data until a new line is found
            while True:
                data = connection.recv(4096) #reads MAX 4096 bytes, (really dont need more)
    
                if not data: #if connection dies break whole loop and stop receiving data
                    break
    
                buffer += data.decode("utf-8") #converts data into a string and adds it to the buffer
    
                while "\n" in buffer: #iff the buffer creates a new line, it means a full message has been received, so we can process it
                    message, buffer = buffer.split("\n", 1) #slit at end, reset buffer, store message
                    latest_apps = json.loads(message) #convert the message into a python object (list of dicts)
                    for app in latest_apps:
                        print(app) #full JSON string
                        print(app["name"]) #individual name (2D list section)
                        print(app["window"]) #window title (2D list section)

    threading.Thread(          
        target=receive_apps,
        daemon=True
    ).start()
    '''
    
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events(self.clock)

            if not self.running:
                break

            self.update()
            self.draw()
            if self.state.done:
                self.flip_state()
        pygame.quit()
        sys.exit()

    def handle_events(self, clock):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT: #x button closes the window
                self.running = False
        self.state.handle_events(events, clock)

    def update(self):
       # self.all_sprites.update() if sprites are decided to be used
        self.state.update()

    def draw(self):
        self.state.draw(self.screen)
        pygame.display.flip()
        
    def flip_state(self):
        next_state_name = self.state.next_state
        
        # Reset the old state's exit flags before leaving
        self.state.done = False
        self.state.next_state = None
        
        # Load the new active state (and optionally re-instantiate it to reset it)
        if next_state_name == "SETUP":
            self.state_dict["SETUP"] = Setup() # Clean slate reset
        if next_state_name == "MAIN_MENU":
            self.state_dict["MAIN_MENU"] = MainMenu() # Clean slate reset
        if next_state_name == "HELP":
            self.state_dict["HELP"] = Help() # Clean slate reset
            
        self.active_state_name = next_state_name
        self.state = self.state_dict[self.active_state_name]

    
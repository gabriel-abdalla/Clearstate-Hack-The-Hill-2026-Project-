import pygame
import sys
import subprocess
from pathlib import Path
from src.screens.base_state import BaseState
from src.modules.push_button import Push_Button
from src.modules.label import Label
from src.modules.text_input import TextInput
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BROWN, BLACK, ORANGE, PRESAGE_STATE_FILE, APP_MONITOR_SCRIPT, CLEARSTATE_DIR

class MainMenu(BaseState):
    def __init__(self):
        super().__init__()
        self.background = pygame.image.load(CLEARSTATE_DIR / "assets" / "White_Background.jpg").convert()
        self.btn_start_game = Push_Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 250, 300, 150, "Setup", 60, "setup")
        self.btn_help = Push_Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50, 300, 150, "Help", 60, "help")
        self.btn_exit = Push_Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 150, 300, 150, "Exit", 60, "exit")
        self.lbl_title = Label(0, 0, SCREEN_WIDTH, 80, "ClearState", 50)
        self.btn_start_bgscript = Push_Button(25, 600, 300, 150, "Start Script", 60, "start_bgs")
        self.btn_end_bgscript = Push_Button(700, 600, 300, 150, "End Script", 60, "end_bgs")
        self.background_process = None
        
    def handle_events(self, events, clock):
        for event in events:
            if self.btn_start_game.click(event):
                self.next_state = "SETUP"
                self.done = True
            elif self.btn_help.click(event):
                self.next_state = "HELP"
                self.done = True
            elif self.btn_exit.click(event):
                self.write_andclear_textfile(PRESAGE_STATE_FILE, "False")  # Write "False" to the text file
            elif self.btn_start_bgscript.click(event):
                if self.background_process is None or self.background_process.poll() is not None:
                    self.background_process = subprocess.Popen(
                        [sys.executable, str(APP_MONITOR_SCRIPT)],
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif self.btn_end_bgscript.click(event):
                self.close_external_script()
                 
    def draw(self, screen):
        screen.fill((30, 30, 40)) 
        screen.blit(self.background, (0, 0))
        self.lbl_title.draw(screen)
        self.btn_start_game.draw(screen)
        self.btn_help.draw(screen)
        self.btn_exit.draw(screen)
        self.btn_start_bgscript.draw(screen)
        self.btn_end_bgscript.draw(screen)
        self.lbl_title.draw(screen)
    
    @staticmethod
    def read_textfile(file_path):
        entries = []
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                # .strip() removes the trailing newline character (\n)
                entry = line.strip()
                if entry:
                    entries.append(entry)
        return entries

    @staticmethod 
    def write_andclear_textfile(file_path, entry):
        with open(file_path, "w", encoding="utf-8") as file:
            pass  # Clear the file by opening it in write mode without writing anything
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(entry) #write the new entry to the file
    
    def close_external_script(self):
        if self.background_process is None:
            print("Script was not started by this menu.")
            return

        if self.background_process.poll() is None:
            self.background_process.terminate()
            try:
                self.background_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.background_process.kill()
                self.background_process.wait()

        self.background_process = None
        
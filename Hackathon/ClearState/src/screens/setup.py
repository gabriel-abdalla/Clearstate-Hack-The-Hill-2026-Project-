import pygame
from pathlib import Path
from src.screens.base_state import BaseState
from src.modules.listview import ListView
from src.settings import WHITE, BLACK, GREEN, BROWN, RED, SCREEN_WIDTH, SCREEN_HEIGHT, LOCKED_APPS_FILE, CLEARSTATE_DIR
from src.modules.label import Label
from src.modules.push_button import Push_Button
from src.modules.text_input import TextInput


def create_programs(count):
    programs = []
    for number in range(1, count + 1):
        programs.append(f"Program {number}")
    return programs

class Setup(BaseState):
    def __init__(self):
        super().__init__()
        self.font = pygame.font.SysFont(None, 36)
        self.items = self.read_textfile(LOCKED_APPS_FILE)  # Read the list of blocked programs from the text file
        self.background = pygame.image.load(CLEARSTATE_DIR / "assets" / "White_Background_3.jpg").convert()
        self.lst_blockedprograms = ListView(self.items, SCREEN_WIDTH * 0.25, 100, 30)
        self.lst_blockedprograms.set_max_visible_items(15)
        self.lst_blockedprograms.set_width_override(SCREEN_WIDTH // 2)  # Set the width of the ListView to half the screen width
        self.lbl_title = Label(0, 0, SCREEN_WIDTH, 80, "ClearState", 50)
        self.btn_add_program = Push_Button(25, 100, 150, 50, "Add Program", 24, "add_program")
        self.txt_add_program = TextInput(25, 200, 150, 100, 24)
        self.btn_remove_program = Push_Button(25, 350, 150, 50, "Remove Program", 24, "remove_program")
        self.txt_remove_program = TextInput(25, 450, 150, 100, 24)
        
        self.btn_return = Push_Button(850, 550, 150, 150, "Return", 24, "return")
        
        self.txt_add_program.set_prompt("Program...")
        self.txt_add_program.set_max_chars(50)
        self.txt_add_program.set_text_color(BLACK)
        self.txt_add_program.set_border_color(GREEN)
        self.txt_add_program.set_background_color(WHITE)
        self.txt_add_program.set_cursor_color(BROWN)
        self.txt_add_program.set_multiline(True)  # Enable multiline input for the add program TextInput
        self.txt_remove_program.set_prompt("Program...")
        self.txt_remove_program.set_max_chars(50)
        self.txt_remove_program.set_text_color(BLACK)
        self.txt_remove_program.set_border_color(RED)
        self.txt_remove_program.set_background_color(WHITE)
        self.txt_remove_program.set_cursor_color(BROWN)
        self.txt_remove_program.set_multiline(True)  # Enable multiline input for the remove program TextInput 

    def handle_events(self, events, clock):
        self.lst_blockedprograms.handle_events(events)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Return to menu on Escape
                self.next_state = "MAIN_MENU"
                self.done = True
            elif self.btn_return.click(event):
                self.next_state = "MAIN_MENU"
                self.done = True
            if self.btn_add_program.click(event):
                program_to_add = self.txt_add_program.get_text().strip().lower()
                if program_to_add:
                    self.items.append(program_to_add)
                    self.write_andclear_textfile(LOCKED_APPS_FILE, "\n".join(self.items))  # Update the text file
                    self.lst_blockedprograms.clear_items()  # Clear the ListView items
                    self.txt_add_program.set_text("")  # Clear the TextInput after adding the program
                    self.lst_blockedprograms.add_items(self.items)  # Update the ListView with the new list
            elif self.btn_remove_program.click(event):
                program_to_remove = self.txt_remove_program.get_text().strip().lower()
                if program_to_remove in self.items:
                    self.items.remove(program_to_remove)
                    self.write_andclear_textfile(LOCKED_APPS_FILE, "\n".join(self.items))  # Update the text file
                    self.lst_blockedprograms.clear_items()  # Clear the ListView items
                    self.txt_remove_program.set_text("")  # Clear the TextInput after removing the program
                    self.lst_blockedprograms.add_items(self.items)  # Update the ListView with the new list
        self.txt_add_program.handle_events(events)
        self.txt_add_program.update(clock.get_time() / 1000.0)
        self.txt_remove_program.handle_events(events)
        self.txt_remove_program.update(clock.get_time() / 1000.0)

    def draw(self, screen):
        screen.fill((10, 50, 10))
        screen.blit(self.background, (0, 0))
        self.lst_blockedprograms.draw(screen)
        self.lbl_title.draw(screen)
        self.btn_return.draw(screen)
        self.btn_add_program.draw(screen)
        self.btn_remove_program.draw(screen)
        self.txt_add_program.draw(screen)  # Draw the TextInput on the screen
        self.txt_remove_program.draw(screen)  # Draw the TextInput on the screen
        
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
#push button example
#TO DOOOO
#1. could add an effect where everything pauses until you release the button (non-instant activation)

import pygame
from src.settings import WHITE, BLACK, DARK_GRAY, DARK_BLUE, BLUE, RED, GREEN, LIGHT_GRAY, LIGHT_BLUE, LIGHT_GREEN, LIGHT_RED, ORANGE, YELLOW, DARK_ORANGE, DARK_YELLOW, DARK_GREEN, DARK_RED, PINK, PURPLE

class Push_Button (pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, text, fontsize, purpose):
        super().__init__()
        self.base = pygame.rect.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, fontsize)  # Use default font and the specified size
        self.text = self.font.render(text, True, (255, 255, 255))  # Render the text in white
        self.current_color = BLACK  # Default button color
        self.bg_color = BLACK # default button color
        self.text_color = WHITE # default text color
        self.hover_color = GREEN # default color when hovering
        self.click_color = RED # default color when clicked
        self.purpose = purpose  # Store the button's purpose

        
        self.text_rect = self.text.get_rect(center=self.base.center) #text in button center
        
    def draw(self, screen):
        self.hover(pygame.event.Event(pygame.NOEVENT))  # Check for hover state
        pygame.draw.rect(screen, self.current_color, self.base)  # Draw the button rectangle
        screen.blit(self.text, self.text_rect)  # Draw the text on the button
        
    def click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
            if self.base.collidepoint(event.pos):
                self.current_color = self.click_color  # Change color on click
                return True  # Button was clicked
        return False  # Button was not clicked
    
    def hover(self, event):
            if self.base.collidepoint(pygame.mouse.get_pos()):
                if self.purpose == "exit" or self.purpose == "end_bgs":
                    self.current_color = RED  # Change color on hover for exit button
                else:
                    self.current_color = self.hover_color  # Change color on hover
            else:
                self.current_color = self.bg_color  # Reset color when not hovering
            
    def set_text(self, new_text):
        self.text = self.font.render(new_text, True, self.text_color)  # Update the text
        self.text_rect = self.text.get_rect(center=self.base.center)  # Re-center the text
    
    def change_bg_color(self, new_color):
        self.current_color = new_color  # Change the background color of the button
        
    def change_text_color(self, new_color):
        self.text_color = new_color  # Change the text color of the button
        self.text = self.font.render(self.text.get_text(), True, self.text_color)  # Update the text with the new color
        self.text_rect = self.text.get_rect(center=self.base.center)  # Re-center the text

    def change_hover_color(self, new_color):
        self.hover_color = new_color  # Change the hover color of the button
        
    def change_click_color(self, new_color):
        self.click_color = new_color  # Change the click color of the button
        
    def change_font_size(self, new_size):
        self.font = pygame.font.Font(None, new_size)  # Change the font size
        self.text = self.font.render(self.text.get_text(), True, self.text_color)  # Update the text with the new font size
        self.text_rect = self.text.get_rect(center=self.base.center)  # Re-center the text
import pygame
from src.settings import WHITE, BLACK, DARK_GRAY, DARK_BLUE, BLUE, RED, GREEN, LIGHT_GRAY, LIGHT_BLUE, LIGHT_GREEN, LIGHT_RED, ORANGE, YELLOW, DARK_ORANGE, DARK_YELLOW, DARK_GREEN, DARK_RED, PINK, PURPLE

class Label(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, text, fontsize):
        super().__init__()
        self.base = pygame.rect.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, fontsize)  # Use default font and the specified size
        self.text = self.font.render(text, True, (255, 255, 255))  # Render the text in white
        self.current_color = BLACK  # Default button color
        self.bg_color = BLACK # default button color
        self.text_color = WHITE # default text color
        
        self.text_rect = self.text.get_rect(center=self.base.center) #text in button center
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.current_color, self.base)  # Draw the button rectangle
        screen.blit(self.text, self.text_rect)  # Draw the text on the button
            
    def set_text(self, new_text):
        self.text = self.font.render(new_text, True, self.text_color)  # Update the text
        self.text_rect = self.text.get_rect(center=self.base.center)  # Re-center the text
    
    def change_bg_color(self, new_color):
        self.current_color = new_color  # Change the background color of the button
        
    def change_text_color(self, new_color):
        self.text_color = new_color  # Change the text color of the button
        self.text = self.font.render(self.text.get_text(), True, self.text_color)  # Update the text with the new color
        self.text_rect = self.text.get_rect(center=self.base.center)  # Re-center the text
        
    def change_font_size(self, new_size):
        self.font = pygame.font.Font(None, new_size)  # Change the font size
        self.text = self.font.render(self.text.get_text(), True, self.text_color)  # Update the text with the new font size
        self.text_rect = self.text.get_rect(center=self.base.center)  # Re-center the text
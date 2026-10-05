import pygame
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, BLACK, DARK_GRAY, DARK_BLUE, BLUE, RED, GREEN, LIGHT_GRAY, LIGHT_BLUE, LIGHT_GREEN, LIGHT_RED, ORANGE, YELLOW, DARK_ORANGE, DARK_YELLOW, DARK_GREEN, DARK_RED, PINK, PURPLE

class Grid(pygame.sprite.Sprite):
    def __init__(self, size, color):
        super().__init__()
        self.lines = []
        self.size = size  # Size of the grid cells
        self.color = color  # Color of the grid lines
        self.thickness = 1  # Thickness of the grid lines
        self.font = pygame.font.Font(None, 20)  # Use default font and the specified size
    
    def draw(self, screen):
        # Draw vertical lines
        for x in range(0, SCREEN_WIDTH, self.size): #0 to the screens width incrmented by pixel step size
            pygame.draw.line(screen, self.color, (x, 0), (x, SCREEN_HEIGHT), self.thickness)
            # Draw the x-coordinate label
            label = self.font.render(str(x), True, WHITE)
            screen.blit(label, (x + 2, 2))  # Offset the label slightly from the line

        # Draw horizontal lines
        for y in range(0, SCREEN_HEIGHT, self.size): #0 to the screens height incrmented by pixel step size
            pygame.draw.line(screen, self.color, (0, y), (SCREEN_WIDTH, y), self.thickness)
            # Draw the y-coordinate label
            label = self.font.render(str(y), True, WHITE)
            screen.blit(label, (2, y + 2))  # Offset the label slightly from the line
    
    def change_line_thickness(self, new_thickness):
        self.thickness = new_thickness  # Change the thickness of the grid lines
        
    def change_line_color(self, new_color):
        self.color = new_color  # Change the color of the grid lines
        
    def change_font_size(self, new_size):
        self.font = pygame.font.Font(None, new_size)  # Change the font size for the coordinate labels

    def change_grid_size(self, new_size):
        self.size = new_size  # Change the size of the grid cells
import pygame
from pathlib import Path
from src.modules.label import Label
from src.screens.base_state import BaseState
from src.settings import BLACK, SCREEN_WIDTH, SCREEN_HEIGHT, CLEARSTATE_DIR

class Help(BaseState):
    def __init__(self):
        super().__init__()
        self.background = pygame.image.load(CLEARSTATE_DIR / "assets" / "White_Background_3.jpg").convert()
        self.font = pygame.font.SysFont(None, 36)
        self.subtitlefont = pygame.font.SysFont(None, 28)
        self.bodyfont = pygame.font.SysFont(None, 15)
        self.title1 = self.font.render("Instuctions to setup Clearstate:", True, BLACK)
        self.title1_rect = self.title1.get_rect(center=(SCREEN_WIDTH // 2 - 75, 75))
        self.subtitle1 = self.subtitlefont.render("How to add a program:", True, BLACK)
        self.subtitle1_rect = self.subtitle1.get_rect(center=(SCREEN_WIDTH // 2 - 150, 125))
        self.subtitle2 = self.subtitlefont.render("How to remove a program:", True, BLACK)
        self.subtitle2_rect = self.title1.get_rect(center=(SCREEN_WIDTH // 2 - 75, 300))
        self.title2 = self.font.render("How to pass Clearstate test:", True, BLACK)
        self.title2_rect = self.title1.get_rect(center=(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT - 300))

        self.body1 = self.bodyfont.render("1. Click Setup", True, BLACK)
        self.body1_rect = self.body1.get_rect(center=(SCREEN_WIDTH // 2 - 100, 165))
        self.body2 = self.bodyfont.render("2. Type program name to be blocked in Add Program field", True, BLACK)
        self.body2_rect = self.body2.get_rect(center=(SCREEN_WIDTH // 2 - 100, 185))
        self.body3 = self.bodyfont.render("3. Click on the Add Program button", True, BLACK)
        self.body3_rect = self.body3.get_rect(center=(SCREEN_WIDTH // 2 - 100, 205))
        self.body4 = self.bodyfont.render("4. Return to the main menu to save", True, BLACK)
        self.body4_rect = self.body4.get_rect(center=(SCREEN_WIDTH // 2 - 100, 225))

        self.body5 = self.bodyfont.render("1. Click Setup", True, BLACK)
        self.body5_rect = self.body5.get_rect(center=(SCREEN_WIDTH // 2 - 100, 340))
        self.body6 = self.bodyfont.render("2. Type program name to be removed in Remove Program field", True, BLACK)
        self.body6_rect = self.body6.get_rect(center=(SCREEN_WIDTH // 2 - 100, 360))
        self.body7 = self.bodyfont.render("3. Click on the Remove Program button", True, BLACK)
        self.body7_rect = self.body7.get_rect(center=(SCREEN_WIDTH // 2 - 100, 380))
        self.body8 = self.bodyfont.render("4. Return to the main menu to save", True, BLACK)
        self.body8_rect = self.body8.get_rect(center=(SCREEN_WIDTH // 2 - 100, 400))

        self.body9 = self.bodyfont.render("1. When the window opens follow window instructions", True, BLACK)
        self.body9_rect = self.body9.get_rect(center=(SCREEN_WIDTH // 2 - 100, 508))
        self.body10 = self.bodyfont.render("2. Assure good lighting", True, BLACK)
        self.body10_rect = self.body10.get_rect(center=(SCREEN_WIDTH // 2 - 100, 528))
        self.body11 = self.bodyfont.render("3. Stand still during scan and smile :)", True, BLACK)
        self.body11_rect = self.body11.get_rect(center=(SCREEN_WIDTH // 2 - 100, 548))
    
    
    def handle_events(self, events, clock):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Return to menu on Escape
                self.next_state = "MAIN_MENU"
                self.done = True

    def draw(self, screen):
        screen.fill((30, 30, 40))
        screen.blit(self.background, (0, 0))
        message = self.font.render("HELP - Press ESC to return to menu", True, BLACK)
        message_rect = message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(message, message_rect)
        screen.blit(self.title1, self.title1_rect)
        screen.blit(self.title2, self.title2_rect)
        screen.blit(self.subtitle1, self.subtitle1_rect)
        screen.blit(self.subtitle2, self.subtitle2_rect)
        screen.blit(self.body1, self.body1_rect)
        screen.blit(self.body2, self.body2_rect)
        screen.blit(self.body3, self.body3_rect)
        screen.blit(self.body4, self.body4_rect)
        screen.blit(self.body5, self.body5_rect)
        screen.blit(self.body6, self.body6_rect)
        screen.blit(self.body7, self.body7_rect)
        screen.blit(self.body8, self.body8_rect)
        screen.blit(self.body9, self.body9_rect)
        screen.blit(self.body10, self.body10_rect)
        screen.blit(self.body11, self.body11_rect)
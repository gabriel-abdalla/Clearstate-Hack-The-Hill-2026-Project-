#pull from this to create extra screens
import pygame

class BaseState:
    def __init__(self):
        self.next_state = None  # Tracks which state to switch to next
        self.done = False       # Set to True when this GUI wants to close

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Handle mouse clicks, text input, and button presses for this GUI."""
        pass

    def update(self) -> None:
        """Update animations, buttons, or UI logic."""
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """Render the layout elements to the window."""
        pass
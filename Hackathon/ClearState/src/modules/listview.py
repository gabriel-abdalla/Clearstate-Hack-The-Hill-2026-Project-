import pygame
from src.settings import WHITE, BLACK, DARK_GRAY, DARK_BLUE, BLUE, RED, GREEN, LIGHT_GRAY, LIGHT_BLUE, LIGHT_GREEN, LIGHT_RED, ORANGE, YELLOW, DARK_ORANGE, DARK_YELLOW, DARK_GREEN, DARK_RED, PINK, PURPLE

class ListView(pygame.sprite.Sprite):
    def __init__(self, items, x, y, fontsize):
        super().__init__()
        self.items = [str(item) for item in items]  # List of items to display
        self.x = x
        self.y = y
        self.font_size = fontsize
        self.font = pygame.font.Font(None, fontsize)  # Use default font and the specified size
        self.text_color = WHITE  # Default text color
        self.background_color = BLACK  # Default background color
        self.selection_color = DARK_GRAY  # Color for the selected item
        self.selected_index = None # Index of the currently selected item
        self.item_spacing = 1.2
        self.item_padding = 5  # Padding around each item
        self.scroll_offset = 0  # Offset for scrolling through items
        self.max_visible_items = 10 # base 10
        self.show_scrollbar = True  # Whether to show a scrollbar or not
        self.scrollbar_width = 10  # Width of the scrollbar
        self.scrollbar_color = DARK_GRAY  # Color of the scrollbar
        self.width_override = None  # Optional width override for the label
        
    def set_width_override(self, width):
        self.width_override = width  # Set the width override for the label
        
    def set_text_color(self, color):
        self.text_color = color  # Change the text color of the label
        
    def set_background_color(self, color):
        self.background_color = color  # Change the background color of the label
        
    def set_selection_color(self, color):
        self.selection_color = color  # Change the selection color of the label
        
    def set_item_spacing(self, spacing):
        self.item_spacing = spacing  # Change the spacing between items
        
    def set_item_padding(self, padding):
        self.item_padding = padding  # Change the padding around each item
        
    def set_max_visible_items(self, max_items):
        self.max_visible_items = max_items  # Set the maximum number of visible items
        
    def set_scrollbar_settings(self, show_scrollbar, width, color):
        self.show_scrollbar = show_scrollbar  # Show or hide the scrollbar
        self.scrollbar_width = width  # Set the width of the scrollbar
        self.scrollbar_color = color  # Set the color of the scrollbar
    
    def add_items(self, items):
        for item in items: #add 
            self.items.append(str(item))  # Add new items to the list and convert them to strings
        
    def clear_items(self):
        self.items.clear()  # Clear all items from the list
        self.selected_index = None # Reset the selected index
        self.scroll_offset = 0  # Reset the scroll offset
    
    def remove_item(self, index):
        if 0 <= index < len(self.items):
            self.items.pop(index) # Remove the item at the specified index
            self.selected_index = None # Reset the selected index
            if self.scroll_offset > 0 and self.scroll_offset >= len(self.items):
                self.scroll_offset = max(0, len(self.items) - 1)  # Adjust the scroll offset if necessary
                
    def get_selected_item(self):
        if self.selected_index is None:
            return None
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None
    
    def select_item(self, index):
        if index is None or 0 <= index < len(self.items):
            self.selected_index = index 

    def _row_height(self):
        return max(1, int(round(self.font.get_height() * self.item_spacing + self.item_padding * 2)))

    def _geometry(self):
        width, height = self.calculate_dimensions()
        total_width = width
        if self.show_scrollbar and self.max_visible_items is not None and len(self.items) > self.max_visible_items:
            total_width += self.scrollbar_width
        list_rect = pygame.Rect(self.x - self.item_padding, self.y - self.item_padding, total_width, height)
        content_rect = pygame.Rect(self.x - self.item_padding, self.y - self.item_padding, width, height)
        scrollbar_rect = pygame.Rect(self.x + width, self.y - self.item_padding, self.scrollbar_width, height)
        return width, height, list_rect, content_rect, scrollbar_rect
            
    def calculate_dimensions(self):
        # Calculate the width and height of the label based on the items and font size
        max_width = 0
        for item in self.items:
            text_surface = self.font.render(item, True, self.text_color)
            max_width = max(max_width, text_surface.get_width())

        visible_count = len(self.items)
        if self.max_visible_items is not None:
            visible_count = min(visible_count, self.max_visible_items)
        row_height = self._row_height()
        total_height = visible_count * row_height
        
        if self.width_override is not None:
            max_width = self.width_override  # Use the width override if set
            
        return max_width, total_height
    
    def handle_scroll(self, events=()):
        if self.max_visible_items is None or len(self.items) <= self.max_visible_items:
            return  # No need to scroll if all items fit within the visible area
        _, _, list_rect, _, _ = self._geometry()
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type != pygame.MOUSEWHEEL:
                continue
            event_pos = getattr(event, "pos", None) or mouse_pos
            if list_rect.collidepoint(event_pos):
                max_offset = max(0, len(self.items) - self.max_visible_items)
                self.scroll_offset = min(max(self.scroll_offset - event.y, 0), max_offset)
    
    def handle_scrollbar_interaction(self, events=()):
        if not self.show_scrollbar or self.max_visible_items is None:
            return  # No scrollbar interaction if it's not shown or max_visible_items is not set
        if len(self.items) <= self.max_visible_items:
            return  # No need to interact with the scrollbar if all items fit within the visible area
        _, height, _, _, scrollbar_rect = self._geometry()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and scrollbar_rect.collidepoint(event.pos):
                relative_y = event.pos[1] - self.y
                max_offset = max(0, len(self.items) - self.max_visible_items)
                self.scroll_offset = min(max(int(relative_y / height * len(self.items)), 0), max_offset)
                
    def update(self, events=()):
        self.handle_scroll(events)
        self.handle_scrollbar_interaction(events)
        _, _, _, content_rect, _ = self._geometry()
        item_height = self._row_height()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if content_rect.collidepoint(event.pos):
                    relative_y = event.pos[1] - content_rect.top + self.scroll_offset * item_height
                    clicked_index = int(relative_y / item_height)
                    self.select_item(clicked_index)

    def handle_events(self, events):
        self.update(events)
                    
    def draw(self, screen, events=()):
        width, height, list_rect, _, scrollbar_rect = self._geometry()
        item_height = self._row_height()
        self.base = list_rect
        pygame.draw.rect(screen, self.background_color, self.base)
        #visible range of items
        visible_count = len(self.items) if self.max_visible_items is None else min(len(self.items), self.max_visible_items)
        end_idx = self.scroll_offset + visible_count
        visible_items = self.items[self.scroll_offset:end_idx]
        for idx, item in enumerate(visible_items):
            actual_idx = self.scroll_offset + idx
            row_rect = pygame.Rect(
                self.x - self.item_padding,
                self.base.top + idx * item_height,
                width,
                item_height,
            )
            if actual_idx == self.selected_index and self.selected_index is not None:
                pygame.draw.rect(screen, self.selection_color, row_rect)
            text = self.font.render(item, True, self.text_color)
            screen.blit(text, text.get_rect(center=row_rect.center))
            
        if self.show_scrollbar and self.max_visible_items is not None and len(self.items) > self.max_visible_items:
            if len(self.items) > self.max_visible_items:
                handle_ratio = self.max_visible_items / len(self.items)
                handle_height = max(1, int(height * handle_ratio))
                max_scrollable = len(self.items) - self.max_visible_items
                if max_scrollable > 0:
                    handle_position = scrollbar_rect.top + (height - handle_height) * (self.scroll_offset / max_scrollable)
                else:
                    handle_position = scrollbar_rect.top
                pygame.draw.rect(screen, self.scrollbar_color, (scrollbar_rect.left, handle_position, scrollbar_rect.width, handle_height))
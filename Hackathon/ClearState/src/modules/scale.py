import pygame

class Scale:
    def __init__(self, virtual_width, virtual_height):
        self.virtual_size = (virtual_width, virtual_height)
        self.update((virtual_width, virtual_height))

    def update(self, window_size):
        window_width, window_height = window_size
        virtual_width, virtual_height = self.virtual_size
        self.scale_factor = min(window_width / virtual_width, window_height / virtual_height)
        self.scaled_size = (
            int(virtual_width * self.scale_factor),
            int(virtual_height * self.scale_factor),
        )
        self.offset = (
            (window_width - self.scaled_size[0]) // 2,
            (window_height - self.scaled_size[1]) // 2,
        )

    def to_virtual_pos(self, window_pos):
        return tuple(
            int((coordinate - offset) / self.scale_factor)
            for coordinate, offset in zip(window_pos, self.offset)
        )

    def transform_event(self, event):
        if hasattr(event, "pos"):
            transformed = event.__dict__.copy()
            transformed["pos"] = self.to_virtual_pos(event.pos)
            return pygame.event.Event(event.type, transformed)
        return event
import pygame


class TextInput(pygame.sprite.Sprite):
    """
    Pygame version of the Rust/Macroquad TextInput from Module Examples.pdf.

    Main features:
      - Single-line and multiline text
      - Mouse click to activate and position cursor
      - Mouse drag selection
      - Shift + arrow selection
      - Ctrl/Cmd + A selection
      - Backspace/Delete
      - Left/Right cursor movement
      - Up/Down movement in multiline mode
      - Key repeat for cursor movement/deletion
      - Maximum character limit
      - Allowed-character whitelist
      - Prompt text
      - Enabled/disabled state
      - Custom font and colours
      - Blinking cursor
      - Separate handle_events(), update(), and draw() methods
      - Chainable setters, matching the style of the Rust version

    Typical use:

        txt_input = TextInput(100, 100, 300, 40, 25)
        txt_input.set_prompt("Enter your name...")

        while running:
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            dt = clock.tick(60) / 1000.0
            txt_input.handle_events(events)
            txt_input.update(dt)
            txt_input.draw(screen)

            pygame.display.flip()
    """

    def __init__(self, x, y, width, height, fontsize):
        super().__init__()

        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)

        self.text = ""
        self.active = False

        # Cursor is stored as a Python string/character index.
        # This is different from Rust, where the implementation stores
        # a UTF-8 byte index.
        self.cursor_index = 0

        self.cursor_timer = 0.0
        self.cursor_visible = True

        self.font_size = int(fontsize)
        self.font = pygame.font.Font(None, self.font_size)

        # Appearance defaults
        self.text_color = pygame.Color("black")
        self.border_color = pygame.Color("darkgray")
        self.background_color = pygame.Color("lightgray")
        self.cursor_color = pygame.Color("black")

        self.prompt = None
        self.prompt_color = pygame.Color("gray")

        # Key repeat defaults from the Rust version
        self.key_repeat_delay = 0.4
        self.key_repeat_rate = 0.05
        self.key_repeat_timer = 0.0
        self.last_key = None

        # Enabled/disabled state
        self.enabled = True
        self.disabled_color = pygame.Color(179, 179, 179, 128)

        # Text restrictions
        self.multiline = False
        self.max_chars = None
        self.allowed_chars = None

        # Selection
        self.selection_anchor = None
        self.is_dragging_selection = False

        # Used by multiline up/down navigation.
        self.preferred_col = None

        # Keep Pygame text input enabled. Actual text is read from
        # TEXTINPUT events rather than guessing characters from keycodes.
        pygame.key.start_text_input()

    # ------------------------------------------------------------------
    # Utility / text constraints
    # ------------------------------------------------------------------

    def _is_char_allowed(self, char):
        if self.allowed_chars is None:
            return True
        return char in self.allowed_chars

    def _apply_text_constraints(self, text):
        constrained = []

        for char in text:
            if char == "\n":
                if self.multiline:
                    constrained.append(char)
            elif self._is_char_allowed(char):
                constrained.append(char)

            if (
                self.max_chars is not None
                and len(constrained) >= self.max_chars
            ):
                break

        return "".join(constrained)

    def _can_insert_char(self, char):
        if char == "\n" and not self.multiline:
            return False

        if char != "\n" and not self._is_char_allowed(char):
            return False

        if (
            self.max_chars is not None
            and len(self.text) >= self.max_chars
        ):
            return False

        return True

    # ------------------------------------------------------------------
    # Wrapping / cursor mapping
    # ------------------------------------------------------------------

    def _get_wrapped_lines_and_mapping(self):
        """
        Returns:
            wrapped_lines:
                List of strings representing displayed lines.

            mapping:
                mapping[text_index] = (line, column)

        Unlike the Rust version, Python string indices are character
        indices, so Unicode characters do not need UTF-8 byte-boundary
        handling.
        """

        if not self.multiline:
            mapping = [(0, i) for i in range(len(self.text) + 1)]
            return [self.text], mapping

        lines = []
        mapping = [(0, 0)] * (len(self.text) + 1)

        padding = 5
        max_width = max(1, int(self.width - 2 * padding))

        line_index = 0
        column_index = 0
        current_line = ""
        current_width = 0

        def char_width(char):
            return self.font.size(char)[0]

        for text_index, char in enumerate(self.text):
            char_width_value = char_width(char)

            if (
                char != "\n"
                and current_line
                and current_width + char_width_value > max_width
            ):
                lines.append(current_line)
                current_line = ""
                current_width = 0
                line_index += 1
                column_index = 0

            if char == "\n":
                lines.append(current_line)
                current_line = ""
                current_width = 0
                line_index += 1
                column_index = 0

                mapping[text_index] = (line_index, column_index)
                continue

            current_line += char
            mapping[text_index] = (line_index, column_index)

            current_width += char_width_value
            column_index += 1

        if current_line or not lines:
            lines.append(current_line)

        mapping[len(self.text)] = (
            max(0, line_index if current_line == "" else line_index),
            len(lines[-1]) if lines else 0,
        )

        # The final mapping above can be wrong after an explicit newline.
        # Rebuild the end position using the same display representation.
        if self.text:
            last_line = len(lines) - 1
            mapping[len(self.text)] = (last_line, len(lines[last_line]))

        return lines, mapping

    def _horizontal_offset_for_col(self, line, col):
        col = max(0, min(col, len(line)))
        if col == 0:
            return 0

        return self.font.size(line[:col])[0]

    def _line_col_for_index(self, mapping, wrapped_lines, index):
        index = max(0, min(index, len(self.text)))

        if index < len(mapping):
            return mapping[index]

        if not wrapped_lines:
            return 0, 0

        return len(wrapped_lines) - 1, len(wrapped_lines[-1])

    def _index_from_local_point(self, local_x, local_y):
        if not self.text:
            return 0

        wrapped_lines, mapping = self._get_wrapped_lines_and_mapping()

        if not wrapped_lines:
            return len(self.text)

        line_height = self.font_size + 2
        clicked_line = int(local_y // line_height)
        clicked_line = max(
            0,
            min(clicked_line, len(wrapped_lines) - 1)
        )

        line = wrapped_lines[clicked_line]

        col = 0
        x_offset = 0

        for i, char in enumerate(line):
            char_width = self.font.size(char)[0]

            if x_offset + char_width / 2 > local_x:
                break

            x_offset += char_width
            col = i + 1

        # Find the last text index mapped to this line/column.
        last_match = None

        for text_index, (line_index, mapped_col) in enumerate(mapping):
            if line_index == clicked_line and mapped_col == col:
                last_match = text_index

        return (
            last_match
            if last_match is not None
            else len(self.text)
        )

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _get_selection_range(self):
        if self.selection_anchor is None:
            return None

        start = min(self.selection_anchor, self.cursor_index)
        end = max(self.selection_anchor, self.cursor_index)

        if start == end:
            return None

        return start, end

    def _clear_selection(self):
        self.selection_anchor = None

    def _delete_selection(self):
        selection = self._get_selection_range()

        if selection is None:
            return False

        start, end = selection

        self.text = self.text[:start] + self.text[end:]
        self.cursor_index = start
        self._clear_selection()

        return True

    # ------------------------------------------------------------------
    # Constructor-compatible / configuration methods
    # ------------------------------------------------------------------

    def set_multiline(self, multiline):
        self.multiline = bool(multiline)

        if not self.multiline:
            self.text = self.text.replace("\n", "")

        self.cursor_index = min(self.cursor_index, len(self.text))
        self._clear_selection()
        return self

    def is_multiline(self):
        return self.multiline

    def get_x(self):
        return self.x

    def set_x(self, x):
        self.x = float(x)
        return self

    def get_y(self):
        return self.y

    def set_y(self, y):
        self.y = float(y)
        return self

    def get_width(self):
        return self.width

    def set_width(self, width):
        self.width = float(width)
        return self

    def get_height(self):
        return self.height

    def set_height(self, height):
        self.height = float(height)
        return self

    def get_position(self):
        return self.x, self.y

    def set_position(self, x, y):
        self.x = float(x)
        self.y = float(y)
        return self

    def get_dimensions(self):
        return self.width, self.height

    def set_dimensions(self, width, height):
        self.width = float(width)
        self.height = float(height)
        return self

    def with_colors(
        self,
        text_color,
        border_color,
        background_color,
        cursor_color
    ):
        self.text_color = text_color
        self.border_color = border_color
        self.background_color = background_color
        self.cursor_color = cursor_color
        return self

    def with_font(self, font):
        self.font = font
        self.font_size = font.get_height()
        return self

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = self._apply_text_constraints(str(text))
        self.cursor_index = min(self.cursor_index, len(self.text))
        self._clear_selection()
        return self

    def is_active(self):
        return self.active

    def set_active(self, active):
        self.active = bool(active)

        if not self.active:
            self._clear_selection()
            self.is_dragging_selection = False

        self.cursor_visible = True
        self.cursor_timer = 0.0

        return self

    def get_cursor_index(self):
        return self.cursor_index

    def set_cursor_index(self, index):
        if 0 <= index <= len(self.text):
            self.cursor_index = index
            self._clear_selection()

        return self

    def get_font_size(self):
        return self.font_size

    def set_font_size(self, size):
        self.font_size = int(size)
        self.font = pygame.font.Font(None, self.font_size)
        return self

    def get_text_color(self):
        return self.text_color

    def set_text_color(self, color):
        self.text_color = color
        return self

    def get_border_color(self):
        return self.border_color

    def set_border_color(self, color):
        self.border_color = color
        return self

    def get_background_color(self):
        return self.background_color

    def set_background_color(self, color):
        self.background_color = color
        return self

    def get_cursor_color(self):
        return self.cursor_color

    def set_cursor_color(self, color):
        self.cursor_color = color
        return self

    def get_font(self):
        return self.font

    def set_prompt(self, prompt):
        self.prompt = str(prompt)
        return self

    def get_prompt(self):
        return self.prompt

    def set_prompt_color(self, color):
        self.prompt_color = color
        return self

    def get_prompt_color(self):
        return self.prompt_color

    def get_key_repeat_delay(self):
        return self.key_repeat_delay

    def set_key_repeat_delay(self, delay):
        self.key_repeat_delay = float(delay)
        return self

    def get_key_repeat_rate(self):
        return self.key_repeat_rate

    def set_key_repeat_rate(self, rate):
        self.key_repeat_rate = float(rate)
        return self

    def with_key_repeat_settings(self, delay, rate):
        self.key_repeat_delay = float(delay)
        self.key_repeat_rate = float(rate)
        return self

    def is_enabled(self):
        return self.enabled

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)

        if not self.enabled:
            self.active = False
            self._clear_selection()
            self.is_dragging_selection = False
            self.cursor_visible = False

        return self

    def get_disabled_color(self):
        return self.disabled_color

    def set_disabled_color(self, color):
        self.disabled_color = color
        return self

    def set_max_chars(self, maximum):
        self.max_chars = int(maximum)
        self.text = self._apply_text_constraints(self.text)
        self.cursor_index = min(self.cursor_index, len(self.text))
        return self

    def clear_max_chars(self):
        self.max_chars = None
        return self

    def set_allowed_chars(self, allowed_chars):
        self.allowed_chars = str(allowed_chars)
        self.text = self._apply_text_constraints(self.text)
        self.cursor_index = min(self.cursor_index, len(self.text))
        self._clear_selection()
        return self

    def clear_allowed_chars(self):
        self.allowed_chars = None
        return self

    def get_allowed_chars(self):
        return self.allowed_chars

    # ------------------------------------------------------------------
    # Mouse / keyboard handling
    # ------------------------------------------------------------------

    def _inside(self, position):
        rect = pygame.Rect(
            int(self.x),
            int(self.y),
            int(self.width),
            int(self.height)
        )
        return rect.collidepoint(position)

    def _reset_cursor_blink(self):
        self.cursor_visible = True
        self.cursor_timer = 0.0

    def _move_left(self, shift=False):
        if shift:
            if self.selection_anchor is None:
                self.selection_anchor = self.cursor_index
        else:
            selection = self._get_selection_range()

            if selection:
                self.cursor_index = selection[0]
                self._clear_selection()
                self.preferred_col = None
                return

            self._clear_selection()

        if self.cursor_index > 0:
            self.cursor_index -= 1

        self.preferred_col = None

    def _move_right(self, shift=False):
        if shift:
            if self.selection_anchor is None:
                self.selection_anchor = self.cursor_index
        else:
            selection = self._get_selection_range()

            if selection:
                self.cursor_index = selection[1]
                self._clear_selection()
                self.preferred_col = None
                return

            self._clear_selection()

        if self.cursor_index < len(self.text):
            self.cursor_index += 1

        self.preferred_col = None

    def _move_vertical(self, direction, shift=False):
        if not self.multiline:
            return

        wrapped_lines, mapping = self._get_wrapped_lines_and_mapping()

        if not wrapped_lines:
            return

        current_line, current_col = self._line_col_for_index(
            mapping,
            wrapped_lines,
            self.cursor_index
        )

        if shift:
            if self.selection_anchor is None:
                self.selection_anchor = self.cursor_index
        else:
            self._clear_selection()

        if self.preferred_col is None:
            self.preferred_col = current_col

        target_line = current_line + direction

        if target_line < 0:
            target_line = 0

        if target_line >= len(wrapped_lines):
            target_line = len(wrapped_lines) - 1

        target_col = min(
            self.preferred_col,
            len(wrapped_lines[target_line])
        )

        # Find the text index for target line/column.
        best_index = self.cursor_index

        for index, (line, col) in enumerate(mapping):
            if line == target_line and col == target_col:
                best_index = index

        self.cursor_index = best_index

    def _insert_text(self, incoming):
        for char in incoming:
            if char == "\r":
                continue

            if char == "\n":
                if not self.multiline:
                    continue

            if not self._can_insert_char(char):
                continue

            # Typing replaces the current selection.
            self._delete_selection()

            self.text = (
                self.text[:self.cursor_index]
                + char
                + self.text[self.cursor_index:]
            )

            self.cursor_index += 1
            self.preferred_col = None

        self._reset_cursor_blink()

    def _delete_forward(self):
        if self._delete_selection():
            return

        if self.cursor_index < len(self.text):
            self.text = (
                self.text[:self.cursor_index]
                + self.text[self.cursor_index + 1:]
            )

        self._reset_cursor_blink()

    def _delete_backward(self):
        if self._delete_selection():
            self._reset_cursor_blink()
            return

        if self.cursor_index > 0:
            self.text = (
                self.text[:self.cursor_index - 1]
                + self.text[self.cursor_index:]
            )
            self.cursor_index -= 1

        self._reset_cursor_blink()

    def _handle_key(self, key, shift=False):
        if key == pygame.K_BACKSPACE:
            self._delete_backward()
            self.last_key = key
            self.key_repeat_timer = 0.0

        elif key == pygame.K_DELETE:
            self._delete_forward()
            self.last_key = key
            self.key_repeat_timer = 0.0

        elif key == pygame.K_LEFT:
            self._move_left(shift)
            self.last_key = key
            self.key_repeat_timer = 0.0

        elif key == pygame.K_RIGHT:
            self._move_right(shift)
            self.last_key = key
            self.key_repeat_timer = 0.0

        elif key == pygame.K_UP:
            self._move_vertical(-1, shift)
            self.last_key = key
            self.key_repeat_timer = 0.0

        elif key == pygame.K_DOWN:
            self._move_vertical(1, shift)
            self.last_key = key
            self.key_repeat_timer = 0.0

        self._reset_cursor_blink()

    def _repeat_key(self, dt):
        if self.last_key is None:
            return

        if not pygame.key.get_pressed()[self.last_key]:
            self.last_key = None
            self.key_repeat_timer = 0.0
            return

        self.key_repeat_timer += dt

        if self.key_repeat_timer < self.key_repeat_delay:
            return

        # Perform one repeat action at the configured rate.
        self.key_repeat_timer -= self.key_repeat_rate

        shift = (
            pygame.key.get_mods()
            & pygame.KMOD_SHIFT
        ) != 0

        if self.last_key == pygame.K_LEFT:
            self._move_left(shift)

        elif self.last_key == pygame.K_RIGHT:
            self._move_right(shift)

        elif self.last_key == pygame.K_UP:
            self._move_vertical(-1, shift)

        elif self.last_key == pygame.K_DOWN:
            self._move_vertical(1, shift)

        elif self.last_key == pygame.K_BACKSPACE:
            self._delete_backward()

        elif self.last_key == pygame.K_DELETE:
            self._delete_forward()

        self._reset_cursor_blink()

    def _handle_mouse_down(self, event):
        if event.button != 1:
            return

        if self._inside(event.pos):
            self.active = True

            local_x = event.pos[0] - self.x - 5
            local_y = event.pos[1] - self.y - 5

            self.cursor_index = self._index_from_local_point(
                local_x,
                local_y
            )

            self.selection_anchor = self.cursor_index
            self.is_dragging_selection = True

            self._reset_cursor_blink()
        else:
            self.active = False
            self._clear_selection()
            self.is_dragging_selection = False

    def _handle_mouse_motion(self, event):
        if not self.active or not self.is_dragging_selection:
            return

        if not pygame.mouse.get_pressed()[0]:
            self.is_dragging_selection = False
            return

        local_x = event.pos[0] - self.x - 5
        local_y = event.pos[1] - self.y - 5

        self.cursor_index = self._index_from_local_point(
            local_x,
            local_y
        )

        self._reset_cursor_blink()

    # ------------------------------------------------------------------
    # Event handling / update / draw
    # ------------------------------------------------------------------

    def handle_events(self, events):
        """Process Pygame events only. Does not update timers or draw."""
        if not self.enabled:
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_dragging_selection = False

            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event)

            elif event.type == pygame.TEXTINPUT:
                if self.active:
                    self._insert_text(event.text)

            elif event.type == pygame.KEYDOWN:
                if not self.active:
                    continue

                mods = pygame.key.get_mods()
                shift = bool(mods & pygame.KMOD_SHIFT)
                shortcut_mod = bool(
                    mods & (pygame.KMOD_CTRL | pygame.KMOD_GUI)
                )

                if shortcut_mod and event.key == pygame.K_a:
                    self.selection_anchor = 0
                    self.cursor_index = len(self.text)
                    self._reset_cursor_blink()
                    self.last_key = None
                    self.key_repeat_timer = 0.0
                    continue

                if shortcut_mod:
                    self.last_key = None
                    self.key_repeat_timer = 0.0
                    continue

                if event.key in (
                    pygame.K_BACKSPACE,
                    pygame.K_DELETE,
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                    pygame.K_UP,
                    pygame.K_DOWN,
                ):
                    self._handle_key(event.key, shift)

                elif event.key == pygame.K_RETURN and self.multiline:
                    self._insert_text("\n")

    def update(self, dt):
        """Update time-based state only. dt is elapsed seconds."""
        if not self.enabled:
            self.active = False
            self.cursor_visible = False
            self._clear_selection()
            self.is_dragging_selection = False
            return

        dt = max(0.0, float(dt))
        self._repeat_key(dt)
        self.cursor_timer += dt

        while self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer -= 0.5

    def update_only(self, dt):
        self.update(dt)

    def draw_only(self, screen):
        self._draw_internal(screen)

    def draw(self, screen):
        """Draw only. Events and updating are handled separately."""
        self._draw_internal(screen)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _draw_selection(self, screen, text_x, text_y):
        selection = self._get_selection_range()

        if not self.enabled or not self.active or selection is None:
            return

        start, end = selection

        wrapped_lines, mapping = self._get_wrapped_lines_and_mapping()

        if not wrapped_lines:
            return

        start_line, start_col = self._line_col_for_index(
            mapping,
            wrapped_lines,
            start
        )

        end_line, end_col = self._line_col_for_index(
            mapping,
            wrapped_lines,
            end
        )

        selection_color = pygame.Color(51, 115, 242, 90)

        line_height = self.font_size + 2

        for line_index in range(
            start_line,
            min(end_line + 1, len(wrapped_lines))
        ):
            line = wrapped_lines[line_index]
            line_length = len(line)

            from_col = (
                start_col
                if line_index == start_line
                else 0
            )

            to_col = (
                end_col
                if line_index == end_line
                else line_length
            )

            from_col = min(from_col, line_length)
            to_col = min(to_col, line_length)

            if to_col <= from_col:
                continue

            start_x = (
                text_x
                + self._horizontal_offset_for_col(line, from_col)
            )

            end_x = (
                text_x
                + self._horizontal_offset_for_col(line, to_col)
            )

            y = (
                text_y
                + line_index * line_height
                - int(self.font_size * 0.8)
            )

            pygame.draw.rect(
                screen,
                selection_color,
                pygame.Rect(
                    int(start_x),
                    int(y),
                    max(1, int(end_x - start_x)),
                    self.font_size + 6
                )
            )

    def _draw_cursor(self, screen, text_x, text_y):
        if not self.enabled or not self.active or not self.cursor_visible:
            return

        wrapped_lines, mapping = self._get_wrapped_lines_and_mapping()

        if self.multiline:
            cursor_line, cursor_col = self._line_col_for_index(
                mapping,
                wrapped_lines,
                self.cursor_index
            )

            if cursor_line < len(wrapped_lines):
                line = wrapped_lines[cursor_line]
            else:
                line = ""

            cursor_offset = self._horizontal_offset_for_col(
                line,
                cursor_col
            )

            line_height = self.font_size + 2

            y1 = (
                text_y
                + cursor_line * line_height
                - int(self.font_size * 0.7)
            )

            y2 = text_y + cursor_line * line_height + 2

        else:
            line = self.text
            cursor_offset = self._horizontal_offset_for_col(
                line,
                self.cursor_index
            )

            y1 = text_y - int(self.font_size * 0.7)
            y2 = text_y + 2

        cursor_x = text_x + cursor_offset + 2

        pygame.draw.line(
            screen,
            self.cursor_color,
            (int(cursor_x), int(y1)),
            (int(cursor_x), int(y2)),
            1
        )

    def _draw_internal(self, screen):
        padding = 5

        text_x = self.x + padding
        text_y = self.y + self.font_size + padding

        # Background
        background = (
            self.background_color
            if self.enabled
            else self.disabled_color
        )

        pygame.draw.rect(
            screen,
            background,
            pygame.Rect(
                int(self.x),
                int(self.y),
                int(self.width),
                int(self.height)
            )
        )

        text_color = (
            self.text_color
            if self.enabled
            else pygame.Color("gray")
        )

        prompt_color = (
            self.prompt_color
            if self.enabled
            else pygame.Color("gray")
        )

        # Selection must be drawn before text.
        self._draw_selection(
            screen,
            text_x,
            text_y
        )

        # Text / prompt
        if not self.text:
            if self.prompt is not None:
                surface = self.font.render(
                    self.prompt,
                    True,
                    prompt_color
                )
                screen.blit(
                    surface,
                    (int(text_x), int(text_y - self.font_size))
                )
        else:
            wrapped_lines, _ = (
                self._get_wrapped_lines_and_mapping()
            )

            line_height = self.font_size + 2

            for i, line in enumerate(wrapped_lines):
                surface = self.font.render(
                    line,
                    True,
                    text_color
                )

                screen.blit(
                    surface,
                    (
                        int(text_x),
                        int(text_y - self.font_size + i * line_height)
                    )
                )

        # Cursor
        self._draw_cursor(
            screen,
            text_x,
            text_y
        )

        # Border
        border = (
            self.border_color
            if self.enabled
            else pygame.Color("gray")
        )

        pygame.draw.rect(
            screen,
            border,
            pygame.Rect(
                int(self.x),
                int(self.y),
                int(self.width),
                int(self.height)
            ),
            width=2
        )

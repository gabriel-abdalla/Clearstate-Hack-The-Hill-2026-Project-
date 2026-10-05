import json
import os
import queue
import signal
import subprocess
import threading
import time
from pathlib import Path

import pygame


BG = (238, 242, 235)
PAPER = (252, 253, 249)
INK = (27, 43, 38)
MUTED = (99, 115, 106)
LINE = (215, 222, 213)
GREEN = (42, 119, 91)
GREEN_PALE = (224, 240, 229)
CORAL = (191, 83, 66)
CORAL_PALE = (249, 231, 224)
AMBER = (171, 116, 40)
AMBER_PALE = (249, 239, 215)
WHITE = (255, 255, 255)
HAPPY_CONFIDENCE_THRESHOLD = 60
HAPPY_READINGS_REQUIRED = 3

INITIAL_SIZE = (1160, 780)
MIN_SIZE = (900, 650)
EXPRESSION_NAMES = {
    "angry": "Angry",
    "contempt": "Contempt",
    "disgust": "Disgust",
    "fear": "Fear",
    "happy": "Happy",
    "neutral": "Neutral",
    "sad": "Sad",
    "surprise": "Surprise",
    "unspecified": "Unspecified",
}


def _font(size, bold=False, mono=False):
    families = ("consolas", "bahnschrift", "segoeui") if mono else ("bahnschrift", "segoeui")
    for family in families:
        path = pygame.font.match_font(family, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont(None, size, bold=bold)


def _text(surface, value, position, font, color=INK, max_width=None):
    value = str(value)
    if max_width is not None:
        while value and font.size(value)[0] > max_width:
            value = value[:-2].rstrip() + "..."
    image = font.render(value, True, color)
    surface.blit(image, position)
    return image.get_rect(topleft=position)


def _wrap(text, font, width):
    words = str(text).split()
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if line and font.size(candidate)[0] > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def _panel(surface, rect, color=PAPER):
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, LINE, rect, width=1, border_radius=8)


def _pill(surface, rect, label, fill, color, font):
    pygame.draw.rect(surface, fill, rect, border_radius=8)
    image = font.render(label, True, color)
    surface.blit(image, image.get_rect(center=rect.center))


def _history_chart(surface, rect, history, color):
    pygame.draw.line(surface, LINE, (rect.left, rect.bottom), (rect.right, rect.bottom), 1)
    if len(history) < 2:
        _text(surface, "Waiting for trend", (rect.left, rect.top + 10), _font(13), MUTED)
        return
    values = [value for value in history if value is not None]
    if len(values) < 2:
        return
    low, high = min(values), max(values)
    spread = max(high - low, 1.0)
    points = []
    for index, value in enumerate(values):
        x = rect.left + index * rect.width / (len(values) - 1)
        y = rect.bottom - 4 - (value - low) * (rect.height - 10) / spread
        points.append((round(x), round(y)))
    pygame.draw.lines(surface, color, False, points, 2)
    pygame.draw.circle(surface, color, points[-1], 4)

def _draw_metric(surface, rect, title, item, unit, history, accent, warmup_seconds,
                 sample_age_seconds=None, precision=0):
    _panel(surface, rect)
    pad = 19
    _text(surface, title.upper(), (rect.x + pad, rect.y + 15), _font(13, bold=True), MUTED)
    if not item or item.get("value") is None:
        value_text = "--"
    else:
        value_text = f"{item['value']:.{precision}f}"
    number = _text(surface, value_text, (rect.x + pad, rect.y + 45), _font(48, bold=True, mono=True), INK)
    _text(surface, unit, (number.right + 9, rect.y + 72), _font(15, bold=True), MUTED)

    if item and item.get("confidence") is not None:
        stable = item.get("stable")
        stability = "STABLE" if stable else "BUILDING" if stable is False else ""
        text = f"Confidence {item['confidence']:.0f}%"
        if stability:
            text += f"  /  {stability}"
        tint = GREEN if stable else AMBER if stable is False else MUTED
        _text(surface, text, (rect.x + pad, rect.y + 110), _font(13, bold=True), tint)
    else:
        _text(surface, "Waiting for a confident reading", (rect.x + pad, rect.y + 112), _font(13), MUTED)
    if sample_age_seconds is not None:
        stale = sample_age_seconds > 15
        age_label = f"Last sample {sample_age_seconds}s ago" + (" | STALE" if stale else "")
        _text(surface, age_label, (rect.x + pad, rect.y + 130), _font(11, bold=stale), AMBER if stale else MUTED)
    _text(surface, f"Allow {warmup_seconds}s for the analysis window",
          (rect.x + pad, rect.y + 153), _font(11), MUTED)

    chart = pygame.Rect(rect.right - 194, rect.y + 54, 170, 86)
    _history_chart(surface, chart, history, accent)


def _draw_face(surface, rect, face):
    pad = 18
    _text(surface, "FACE SIGNAL", (rect.x + pad, rect.y + 14), _font(13, bold=True), MUTED)
    face = face or {}
    blinking = face.get("blinking")
    talking = face.get("talking")
    blink_label = "BLINK  YES" if blinking and blinking.get("detected") else "BLINK  NO" if blinking else "BLINK  --"
    talk_label = "TALK  YES" if talking and talking.get("detected") else "TALK  NO" if talking else "TALK  --"
    _pill(surface, pygame.Rect(rect.x + pad, rect.y + 44, 112, 28), blink_label,
          GREEN_PALE if blinking and blinking.get("detected") else BG,
          GREEN if blinking and blinking.get("detected") else MUTED, _font(11, bold=True))
    _pill(surface, pygame.Rect(rect.x + pad + 120, rect.y + 44, 104, 28), talk_label,
          CORAL_PALE if talking and talking.get("detected") else BG,
          CORAL if talking and talking.get("detected") else MUTED, _font(11, bold=True))

    expression = face.get("expression") or {}
    scores = expression.get("scores") or []
    top_scores = sorted(scores, key=lambda score: score.get("confidence", 0), reverse=True)[:3]
    _text(surface, "EXPRESSION MODEL SCORES", (rect.x + pad, rect.y + 91), _font(10, bold=True), MUTED)
    for index, score in enumerate(top_scores):
        row_y = rect.y + 114 + index * 32
        score_value = max(0, min(100, score.get("confidence", 0)))
        label = EXPRESSION_NAMES.get(score.get("type"), "Unknown")
        _text(surface, label, (rect.x + pad, row_y), _font(11, bold=True), INK, 88)
        track = pygame.Rect(rect.x + pad + 94, row_y + 5, 76, 7)
        pygame.draw.rect(surface, LINE, track, border_radius=3)
        fill_width = round(track.width * score_value / 100)
        if fill_width:
            pygame.draw.rect(surface, GREEN, (track.x, track.y, fill_width, track.height), border_radius=3)
        _text(surface, f"{score_value:.0f}%", (track.right + 7, row_y - 3), _font(11), MUTED)
    if not top_scores:
        _text(surface, "No expression scores yet", (rect.x + pad, rect.y + 118), _font(11), MUTED)
    _text(surface, "Model probabilities, not a mood reading",
          (rect.x + pad, rect.bottom - 22), _font(10), MUTED, 220)

    landmarks = face.get("landmarks") or {}
    points = landmarks.get("points") or []
    plot = pygame.Rect(rect.x + pad + 230, rect.y + 84, max(100, rect.width - 264), rect.height - 105)
    pygame.draw.rect(surface, BG, plot, border_radius=6)
    _text(surface, f"LANDMARKS  {len(points)}", (plot.x + 10, plot.y + 8), _font(11, bold=True), MUTED)
    if points:
        xs = [point["x"] for point in points]
        ys = [point["y"] for point in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(max_x - min_x, 1e-6)
        span_y = max(max_y - min_y, 1e-6)
        inset = 16
        drawable_w = max(1, plot.width - inset * 2)
        drawable_h = max(1, plot.height - inset * 2 - 18)
        for point in points:
            px = plot.x + inset + (point["x"] - min_x) / span_x * drawable_w
            py = plot.y + inset + 15 + (point["y"] - min_y) / span_y * drawable_h
            pygame.draw.circle(surface, GREEN, (round(px), round(py)), 2)
    else:
        _text(surface, "Face points appear when tracking is ready",
              (plot.x + 12, plot.centery), _font(12), MUTED, plot.width - 24)


def _draw_guidance(surface, rect, state, elapsed, output_jsonl):
    _panel(surface, rect)
    pad = 18
    _text(surface, "SESSION", (rect.x + pad, rect.y + 14), _font(13, bold=True), MUTED)
    _text(surface, time.strftime("%M:%S", time.gmtime(elapsed)),
          (rect.x + pad, rect.y + 43), _font(31, bold=True, mono=True), INK)
    _text(surface, "ELAPSED", (rect.x + pad + 112, rect.y + 56), _font(11, bold=True), MUTED)

    _text(surface, "INPUT GUIDANCE", (rect.x + pad, rect.y + 100), _font(11, bold=True), MUTED)
    hint_font = _font(16, bold=True)
    lines = _wrap(state.get("hint") or "Center your face and remain still.", hint_font, rect.width - pad * 2)
    visible_lines = lines[:2] if rect.height < 245 else lines[:3]
    for index, line in enumerate(visible_lines):
        _text(surface, line, (rect.x + pad, rect.y + 120 + index * 22), hint_font, INK)

    metrics = state.get("metrics") or {}
    hrv = metrics.get("hrv") or {}
    amplitude = metrics.get("breathing_amplitude") or {}
    apnea = metrics.get("apnea")
    detail = "HRV RMSSD  --"
    if hrv.get("rmssd") is not None:
        detail = f"HRV RMSSD  {hrv['rmssd']:.0f} ms"
    if amplitude.get("value") is not None:
        detail += f"    BREATH AMPLITUDE  {amplitude['value']:.2f}"
    if apnea:
        detail += f"    APNEA  {'YES' if apnea.get('detected') else 'NO'}"
    _text(surface, detail, (rect.x + pad, rect.bottom - 32), _font(11, bold=True), MUTED, rect.width - pad * 2)
    if output_jsonl:
        _text(surface, f"Writing decoded records to {output_jsonl.name}",
              (rect.x + pad, rect.bottom - 16), _font(10), MUTED, rect.width - pad * 2)


class Dashboard:
    def __init__(self, node, output_jsonl):
        self.node = node
        self.output_jsonl = output_jsonl
        self.events = queue.Queue()
        self.process = None
        self.reader = None
        self.log_file = None
        self.error = ""
        self.status = "Ready"
        self.hint = "Center your face and remain still."
        self.metrics = {}
        self.pulse_history = []
        self.pulse_reading = None
        self.pulse_updated_at = None
        self.started_at = None
        self.last_metrics_at = None
        self.key_value = os.environ.get("SMARTSPECTRA_API_KEY", "")
        self.key_focused = False
        self.happy_readings = 0
        self.passed = False
        self.running = True
        self.clock = pygame.time.Clock()
        self.size = INITIAL_SIZE
        self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)
        pygame.display.set_caption("SmartSpectra | Live Vitals")
        self.small = _font(12)
        self.body = _font(15)
        self.title = _font(30, bold=True)
        self.label = _font(13, bold=True)
        self.key_rect = pygame.Rect(0, 0, 0, 0)
        self.action_rect = pygame.Rect(0, 0, 0, 0)
        if self.key_value:
            self._start_session()

    def _paste_key(self):
        try:
            clipboard = pygame.scrap.get(pygame.SCRAP_TEXT)
        except pygame.error:
            self.error = "Clipboard unavailable; type the API key instead."
            return
        if not clipboard:
            return
        if isinstance(clipboard, bytes):
            pasted = clipboard.decode("utf-8", errors="ignore")
        else:
            pasted = str(clipboard)
        pasted = pasted.rstrip("\0\r\n").strip()
        if pasted:
            self.key_value = pasted[:512]
            self.error = ""

    def _start_session(self):
        if self.process and self.process.poll() is None:
            return
        key = self.key_value.strip() or os.environ.get("SMARTSPECTRA_API_KEY", "").strip()
        if not key:
            self.error = "Enter your API key in the field below to connect."
            return
        env = os.environ.copy()
        env["SMARTSPECTRA_API_KEY"] = key
        try:
            if self.output_jsonl:
                self.log_file = self.output_jsonl.open("a", encoding="utf-8")
            self.process = subprocess.Popen(
                [self.node, str(Path(__file__).resolve().parent / "presage_bridge.mjs"), "--live"],
                cwd=Path(__file__).resolve().parent,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except OSError as error:
            self.error = f"Could not start the SDK: {error}"
            if self.log_file:
                self.log_file.close()
                self.log_file = None
            return

        self.error = ""
        self.status = "Connecting"
        self.hint = "Starting camera and checking authorization."
        self.metrics = {}
        self.pulse_history.clear()
        self.pulse_reading = None
        self.pulse_updated_at = None
        self.started_at = time.monotonic()
        self.last_metrics_at = None
        self.key_value = ""
        self.key_focused = False
        self.reader = threading.Thread(target=self._read_events, args=(self.process,), daemon=True)
        self.reader.start()

    def _read_events(self, process):
        try:
            for line in process.stdout:
                try:
                    self.events.put(json.loads(line))
                except json.JSONDecodeError:
                    continue
            self.events.put({"type": "process_exit", "code": process.wait()})
        except OSError as error:
            self.events.put({"type": "error", "message": str(error)})

    def _stop_session(self, status="Stopping"):
        if not self.process or self.process.poll() is not None:
            return
        if status:
            self.status = status
        try:
            if os.name == "nt":
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.process.send_signal(signal.SIGINT)
        except OSError as error:
            self.error = f"Could not stop cleanly: {error}"

    def _accept_event(self, event):
        kind = event.get("type")
        if kind == "started":
            self.status = "Starting camera"
        elif kind == "status":
            status = event.get("status", "").removeprefix("k")
            self.status = status.capitalize() or "Running"
            if status.lower() == "running" and self.started_at is None:
                self.started_at = time.monotonic()
        elif kind == "validation":
            self.hint = event.get("hint") or "Adjust your position and lighting."
        elif kind == "metrics":
            self.metrics = event
            expression = (event.get("face") or {}).get("expression") or {}
            happy_score = next(
                (score for score in expression.get("scores", [])
                 if score.get("type") == "happy"),
                None,
            )
            if (
                happy_score
                and happy_score.get("confidence", 0) >= HAPPY_CONFIDENCE_THRESHOLD
                and expression.get("stable") is not False
            ):
                self.happy_readings += 1
            else:
                self.happy_readings = 0
            if self.happy_readings >= HAPPY_READINGS_REQUIRED:
                self.passed = True
                self.status = "Access granted"
                self.hint = "Happy expression detected. Access granted."
                self.running = False
                self._stop_session(status=None)
            pulse = event.get("pulse_rate")
            if pulse and pulse.get("value") is not None:
                self.pulse_reading = pulse
                self.pulse_updated_at = time.monotonic()
                self.pulse_history.append(pulse["value"])
                del self.pulse_history[:-48]
            if self.log_file:
                self.log_file.write(json.dumps(event, separators=(",", ":")) + "\n")
                self.log_file.flush()
        elif kind == "error":
            self.error = event.get("message", "SmartSpectra encountered an error.")
            self.status = "Error"
        elif kind == "process_exit":
            code = event.get("code", 0)
            self.status = "Stopped" if code == 0 else "Error"
            if code and not self.error:
                self.error = f"SmartSpectra exited with code {code}. Check the API key and subscription."
            self.process = None
            self.started_at = None
            if self.log_file:
                self.log_file.close()
                self.log_file = None

    def _drain_events(self):
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            self._accept_event(event)

    def _layout(self):
        width, height = self.size
        margin = 28
        gap = 16
        content_w = width - margin * 2
        top = 116
        footer_h = 95
        metric_h = 184
        pulse_rect = pygame.Rect(margin, top, content_w, metric_h)
        lower_y = top + metric_h + gap
        lower_h = max(170, height - lower_y - footer_h - gap - 15)
        face_w = int((content_w - gap) * 0.56)
        face = pygame.Rect(margin, lower_y, face_w, lower_h)
        guidance = pygame.Rect(margin + face_w + gap, lower_y, content_w - face_w - gap, lower_h)
        footer_y = height - footer_h
        action_w = 164
        self.key_rect = pygame.Rect(margin, footer_y + 27, content_w - action_w - gap, 50)
        self.action_rect = pygame.Rect(self.key_rect.right + gap, footer_y + 27, action_w, 50)
        return margin, pulse_rect, face, guidance, footer_y

    def _draw_header(self, margin, width):
        _text(self.screen, "PRESAGE  /  SMARTSPECTRA", (margin, 22), self.label, GREEN)
        _text(self.screen, "Vitals monitor", (margin, 43), self.title, INK)
        _text(self.screen, "LIVE ESTIMATES  |  NOT A MEDICAL DIAGNOSIS",
              (margin + 244, 57), self.small, MUTED)

        active = self.status.lower() in ("running", "starting camera")
        pending = self.status.lower() in ("connecting", "stopping")
        status_fill = GREEN_PALE if active else AMBER_PALE if pending else BG
        status_color = GREEN if active else AMBER if pending else MUTED
        pill = pygame.Rect(width - margin - 166, 38, 166, 34)
        _pill(self.screen, pill, self.status.upper(), status_fill, status_color, self.label)
        pygame.draw.line(self.screen, LINE, (margin, 98), (width - margin, 98), 1)

    def _draw_keybar(self, margin, footer_y):
        width = self.size[0]
        pygame.draw.rect(self.screen, (231, 236, 228), (0, footer_y, width, self.size[1] - footer_y))
        _text(self.screen, "API KEY  |  HIDDEN", (margin, footer_y + 7), self.label, MUTED)
        focused = self.key_focused
        pygame.draw.rect(self.screen, PAPER, self.key_rect, border_radius=8)
        pygame.draw.rect(self.screen, GREEN if focused else LINE, self.key_rect,
                         width=2 if focused else 1, border_radius=8)
        if not self.key_value:
            _text(self.screen, "Click here, then Ctrl+V to paste your key",
                  (self.key_rect.x + 13, self.key_rect.y + 16), self.body, MUTED, self.key_rect.width - 26)
        else:
            _text(self.screen, "*" * min(len(self.key_value), 60),
                  (self.key_rect.x + 13, self.key_rect.y + 14), _font(20), INK, self.key_rect.width - 26)

        active = self.process is not None and self.process.poll() is None
        button_label = "STOP MEASUREMENT" if active else "START MEASUREMENT"
        button_color = CORAL if active else GREEN
        pygame.draw.rect(self.screen, button_color, self.action_rect, border_radius=8)
        image = _font(12, bold=True).render(button_label, True, WHITE)
        self.screen.blit(image, image.get_rect(center=self.action_rect.center))
        if self.error:
            _text(self.screen, self.error, (margin, footer_y + 80), _font(12, bold=True), CORAL, width - margin * 2)
        elif os.environ.get("SMARTSPECTRA_API_KEY") and not self.key_value:
            _text(self.screen, "Using SMARTSPECTRA_API_KEY from the environment",
                  (margin, footer_y + 80), _font(11), MUTED)

    def draw(self):
        self.screen.fill(BG)
        margin, pulse_rect, face_rect, guidance_rect, footer_y = self._layout()
        self._draw_header(margin, self.size[0])
        sample_age = None
        if self.pulse_updated_at is not None:
            sample_age = int(time.monotonic() - self.pulse_updated_at)
        _draw_metric(self.screen, pulse_rect, "Pulse rate", self.pulse_reading,
                     "bpm", self.pulse_history, CORAL, 12, sample_age, 0)
        _draw_face(self.screen, face_rect, self.metrics.get("face"))
        elapsed = time.monotonic() - self.started_at if self.started_at else 0
        state = {"hint": self.hint, "metrics": self.metrics}
        _draw_guidance(self.screen, guidance_rect, state, elapsed, self.output_jsonl)
        self._draw_keybar(margin, footer_y)
        pygame.display.flip()

    def run(self):
        try:
            pygame.scrap.init()
        except pygame.error:
            pass
        pygame.key.start_text_input()
        try:
            while self.running:
                self._drain_events()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.size = (max(MIN_SIZE[0], event.w), max(MIN_SIZE[1], event.h))
                        self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.key_focused = self.key_rect.collidepoint(event.pos)
                        if self.action_rect.collidepoint(event.pos):
                            if self.process and self.process.poll() is None:
                                self._stop_session()
                            else:
                                self._start_session()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.process and self.process.poll() is None:
                                self._stop_session()
                            else:
                                self.running = False
                        elif self.key_focused and event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                            self._paste_key()
                        elif self.key_focused and event.key == pygame.K_BACKSPACE:
                            self.key_value = self.key_value[:-1]
                        elif self.key_focused and event.key == pygame.K_RETURN:
                            self._start_session()
                    elif event.type == pygame.TEXTINPUT and self.key_focused:
                        self.key_value = (self.key_value + event.text)[:512]
                self.draw()
                self.clock.tick(30)
        finally:
            if self.process and self.process.poll() is None:
                self._stop_session()
                try:
                    self.process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    self.process.terminate()
                    self.process.wait()
            if self.log_file:
                self.log_file.close()
            pygame.quit()
        return 0 if self.passed else 1


def run_gui(node, output_jsonl):
    try:
        pygame.init()
        dashboard = Dashboard(node, output_jsonl)
        return dashboard.run()
    except pygame.error as error:
        print(f"Could not open the Pygame dashboard: {error}")
        pygame.quit()
        return 1
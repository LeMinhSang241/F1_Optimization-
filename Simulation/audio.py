from pathlib import Path

import pygame


ASSET_DIR = Path(__file__).resolve().parent / "assets"


class RaceAudio:
    """Tiếng máy, safety car và khán giả. Thiếu file thì mô phỏng vẫn chạy im lặng."""

    def __init__(self):
        """Mở máy và khán giả ngay khi vào cuộc đua."""
        self.enabled = False
        self.safety_on = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self.engine = pygame.mixer.Sound(str(ASSET_DIR / "engine.mp3"))
            self.safety = pygame.mixer.Sound(str(ASSET_DIR / "safety_car.mp3"))
            self.crowd = pygame.mixer.Sound(str(ASSET_DIR / "crowd.mp3"))
        except pygame.error:
            return

        self.engine_channel = pygame.mixer.Channel(0)
        self.safety_channel = pygame.mixer.Channel(1)
        self.crowd_channel = pygame.mixer.Channel(2)
        self.engine_channel.play(self.engine, loops=-1)
        self.engine_channel.set_volume(0.42)
        self.crowd_channel.play(self.crowd, loops=-1)
        self.crowd_channel.set_volume(0.16)
        self.safety_loops = -1 if self.safety.get_length() < 12 else 0
        self.enabled = True

    def update(self, paused, race_control, cars):
        """Giảm máy khi có cờ, bật tiếng safety car, và nâng khán giả lúc có xe về đích."""
        if not self.enabled:
            return
        if paused:
            pygame.mixer.pause()
            return
        pygame.mixer.unpause()

        if race_control.mode == "safety_car":
            if not self.safety_on:
                self.safety_channel.play(self.safety, loops=self.safety_loops)
                self.safety_on = True
            self.engine_channel.set_volume(0.16)
        else:
            if self.safety_on:
                self.safety_channel.fadeout(400)
                self.safety_on = False
            if race_control.mode == "virtual_safety_car":
                self.engine_channel.set_volume(0.28)
            else:
                self.engine_channel.set_volume(0.42)

        if any(car.finished for car in cars):
            self.crowd_channel.set_volume(0.5)
        else:
            self.crowd_channel.set_volume(0.16)

    def stop(self):
        """Tắt hết tiếng khi đóng cửa sổ."""
        if self.enabled:
            pygame.mixer.stop()

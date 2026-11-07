import math

import pygame

from car_sprite import build_car_surface, looks_for_starting_order


def color_from_hex(color_text):
    """Đổi mã màu dạng #RRGGBB sang ba số màu cho pygame."""
    color_text = color_text.replace("#", "")
    red = int(color_text[0:2], 16)
    green = int(color_text[2:4], 16)
    blue = int(color_text[4:6], 16)
    return red, green, blue


class Renderer:
    """Vẽ đường đua, xe 2D và bảng thông tin bên phải."""

    def __init__(self, screen):
        """Chuẩn bị font rõ, ba sprite xe và bộ nhớ ảnh đã xoay."""
        self.screen = screen
        self.title_font = pygame.font.SysFont("segoeui", 20, bold=True)
        self.name_font = pygame.font.SysFont("segoeui", 16, bold=True)
        self.small_font = pygame.font.SysFont("segoeui", 15)
        self.badge_font = pygame.font.SysFont("segoeui", 14, bold=True)
        self.car_sprites = []
        for starting_order in range(3):
            body_color, nose_color, wing_color, number_text = looks_for_starting_order(starting_order)
            self.car_sprites.append(build_car_surface(body_color, nose_color, wing_color, number_text))
        self.rotated_sprites = {}

    def draw_text(self, text, position, color=(236, 236, 236), font=None):
        """Vẽ một dòng chữ lên màn hình."""
        if font is None:
            font = self.small_font
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def sprite_facing(self, starting_order, direction_x, direction_y):
        """Lấy sprite đã xoay để mũi xe trùng hướng chạy."""
        heading = math.degrees(math.atan2(-direction_y, direction_x)) - 90
        turned = int(round(heading))
        key = (starting_order, turned)
        if key not in self.rotated_sprites:
            self.rotated_sprites[key] = pygame.transform.rotozoom(self.car_sprites[starting_order], turned, 1)
        return self.rotated_sprites[key]

    def car_screen_pose(self, track, car):
        """Tọa độ vẽ của một xe, trên đường hoặc đang đi trong làn pit."""
        if car.status == "pit lane" and car.locked_duration:
            pit_fraction = car.seconds_into_segment / car.locked_duration
            return track.pit_car_pose(pit_fraction, car.starting_order)
        if car.status == "pit lane":
            return track.pit_car_pose(0.0, car.starting_order)
        lane_shift = (car.starting_order - 1) * 14
        return track.car_pose(car.progress, lane_shift)

    def draw_dirty_air(self, position_x, position_y, direction_x, direction_y):
        """Vệt khói ngắn phía sau xe đang bị khí bẩn."""
        scale = math.hypot(direction_x, direction_y) or 1
        back_x = -direction_x / scale
        back_y = -direction_y / scale
        for step, radius, color in (
            (24, 7, (230, 230, 220)),
            (38, 5, (190, 190, 180)),
            (52, 4, (150, 150, 140)),
        ):
            pygame.draw.circle(
                self.screen,
                color,
                (round(position_x + back_x * step), round(position_y + back_y * step)),
                radius,
            )

    def draw_place_badge(self, position_x, position_y, car):
        """Số hạng nổi phía trên xe."""
        badge_x = round(position_x) + (car.place - 2) * 18
        badge_y = round(position_y) - 46
        pygame.draw.circle(self.screen, car.color, (badge_x, badge_y), 11)
        pygame.draw.circle(self.screen, (255, 255, 255), (badge_x, badge_y), 11, 2)
        brightness = car.color[0] * 0.3 + car.color[1] * 0.59 + car.color[2] * 0.11
        number_color = (24, 24, 24) if brightness > 170 else (255, 255, 255)
        label = self.badge_font.render(str(car.place), True, number_color)
        self.screen.blit(label, label.get_rect(center=(badge_x, badge_y)))

    def draw_cars(self, track, cars):
        """Vẽ vệt khí bẩn, xe, rồi số hạng nếu các xe đang đi sát."""
        poses = [self.car_screen_pose(track, car) for car in cars]
        close_flags = []
        for index, (position_x, position_y, _direction_x, _direction_y) in enumerate(poses):
            is_close = False
            for other_index, (other_x, other_y, _other_dx, _other_dy) in enumerate(poses):
                if other_index == index:
                    continue
                if math.hypot(position_x - other_x, position_y - other_y) < 80:
                    is_close = True
            close_flags.append(is_close)

        ordered = sorted(range(len(cars)), key=lambda index: cars[index].place, reverse=True)
        for index in ordered:
            car = cars[index]
            position_x, position_y, direction_x, direction_y = poses[index]
            if car.traffic_note == "dirty air":
                self.draw_dirty_air(position_x, position_y, direction_x, direction_y)
            sprite = self.sprite_facing(car.starting_order, direction_x, direction_y)
            rectangle = sprite.get_rect(center=(round(position_x), round(position_y)))
            self.screen.blit(sprite, rectangle)
        for index, car in enumerate(cars):
            if close_flags[index]:
                position_x, position_y, _direction_x, _direction_y = poses[index]
                self.draw_place_badge(position_x, position_y, car)

    def draw_bar(self, left, top, width, height, fraction, fill_color):
        """Thanh tỉ lệ bo góc, dùng cho tuổi lốp và xăng."""
        fraction = max(0.0, min(1.0, fraction))
        pygame.draw.rect(self.screen, (46, 50, 58), (left, top, width, height), border_radius=3)
        filled = int(width * fraction)
        if 0 < filled < 6:
            filled = 6
        if filled > 0:
            pygame.draw.rect(self.screen, fill_color, (left, top, filled, height), border_radius=3)

    def draw_panel(self, cars, race_status):
        """Cột phải: trạng thái chặng và một thẻ cho mỗi xe."""
        pygame.draw.rect(self.screen, (14, 16, 22), (900, 0, 300, 800))
        pygame.draw.rect(self.screen, (198, 32, 42), (900, 0, 300, 5))
        self.screen.set_clip(pygame.Rect(908, 0, 284, 800))

        self.draw_text(race_status["circuit_name"], (912, 14), (255, 255, 255), self.title_font)
        self.draw_text(
            f"{race_status['track_temperature']:.0f} C    {race_status['coefficient_source']}    {race_status['time_scale']:.0f}x",
            (912, 40),
            (230, 234, 240),
        )
        self.draw_flag(race_status, 66)
        self.draw_text(race_status["planned_text"], (912, 98), (230, 234, 240))
        state_line = "Paused" if race_status["paused"] else "Running"
        compared = race_status["reference_name"].split("(")[0].strip()
        self.draw_text(f"{state_line}    vs {compared}", (912, 120), (230, 234, 240))
        if race_status["message"]:
            self.draw_text(race_status["message"], (912, 142), (255, 214, 120))
        self.draw_text("Space   Up Down   C   T   F   S   V", (912, 164), (210, 216, 224))

        for index, car in enumerate(cars):
            self.draw_car_card(car, 190 + index * 198)

        self.screen.set_clip(None)

    def draw_flag(self, race_status, top):
        """Dòng cờ có nền xanh, vàng hoặc cam."""
        mode = race_status["mode"]
        if mode == "safety_car":
            fill = (150, 118, 16)
        elif mode == "virtual_safety_car":
            fill = (156, 78, 22)
        else:
            fill = (22, 92, 48)
        pygame.draw.rect(self.screen, fill, (912, top, 276, 24), border_radius=4)
        self.draw_text(race_status["flag_text"], (920, top + 4))

    def draw_car_card(self, car, top):
        """Một thẻ: tên, chiến lược, hạng, thanh lốp, thanh xăng."""
        pygame.draw.rect(self.screen, (26, 29, 36), (912, top, 276, 188), border_radius=6)
        pygame.draw.rect(self.screen, car.color, (912, top, 5, 188), border_radius=2)
        self.draw_text(car.name, (926, top + 6), car.color, self.name_font)
        self.draw_text(car.strategy_line, (926, top + 28), (236, 240, 244))
        self.draw_text(
            f"P{car.place}    Gap {car.gap_to_leader_seconds:.1f} s    {car.elapsed:.0f} s",
            (926, top + 50),
            (255, 255, 255),
        )

        tyre_fraction = car.current_tyre_age / max(1, car.current_tyre_limit)
        if tyre_fraction >= 1:
            tyre_color = (196, 64, 54)
        elif tyre_fraction >= 0.75:
            tyre_color = (214, 168, 48)
        else:
            tyre_color = color_from_hex(car.compound_color)
        self.draw_text(
            f"{car.current_compound}  {car.current_tyre_age}/{car.current_tyre_limit}",
            (926, top + 72),
            (255, 255, 255),
        )
        self.draw_bar(926, top + 94, 248, 9, tyre_fraction, tyre_color)

        fuel_fraction = car.fuel_remaining_kg() / max(1.0, car.fuel_load_kg)
        self.draw_text(f"Fuel  {car.fuel_remaining_kg():.0f} kg", (926, top + 108), (255, 255, 255))
        self.draw_bar(926, top + 130, 248, 9, fuel_fraction, (72, 176, 220))

        pit_text = "Pit done" if car.laps_until_pit() is None else f"Pit in {car.laps_until_pit()}"
        self.draw_text(f"{car.traffic_note}    {pit_text}", (926, top + 146), (236, 240, 244))
        self.draw_text(f"Base  {car.base_race_time:.3f} s", (926, top + 166), (170, 230, 176))

    def draw(self, track, cars, race_status):
        """Vẽ nền cỏ, đường, xe và bảng."""
        self.screen.fill((32, 104, 52))
        for band in range(0, 800, 36):
            if (band // 36) % 2 == 0:
                pygame.draw.rect(self.screen, (26, 86, 44), (0, band, 900, 36))
        track.draw(self.screen)
        self.draw_cars(track, cars)
        self.draw_panel(cars, race_status)

import math

import pygame


# Monza: hai đoạn thẳng dài. Đoạn đầu là đường chính, dài nhất, dùng làm vùng DRS.
MONZA_POINTS = [
    (200, 250),
    (800, 250),
    (840, 390),
    (740, 540),
    (460, 640),
    (190, 600),
    (80, 440),
    (80, 250),
]

# Silverstone: nhiều góc hơn, đường chính ngắn. Vùng DRS rơi vào đoạn thẳng dài phía dưới.
SILVERSTONE_POINTS = [
    (170, 210),
    (400, 210),
    (620, 130),
    (800, 220),
    (790, 400),
    (640, 480),
    (720, 650),
    (430, 700),
    (200, 630),
    (100, 480),
    (70, 320),
    (70, 210),
]


class Track:
    """Đường đua khép kín. Monza và Silverstone có hình khác nhau."""

    def __init__(self, circuit_key="monza"):
        """Chọn hình đường, rồi dựng làn pit dọc vạch xuất phát."""
        self.circuit_key = circuit_key
        if circuit_key == "silverstone":
            self.points = list(SILVERSTONE_POINTS)
        else:
            self.points = list(MONZA_POINTS)
        self.road_width = 54
        self.segment_lengths = []
        for index in range(len(self.points)):
            start = self.points[index]
            end = self.points[(index + 1) % len(self.points)]
            self.segment_lengths.append(math.dist(start, end))
        self.total_length = sum(self.segment_lengths)
        self.center_x = sum(point[0] for point in self.points) / len(self.points)
        self.center_y = sum(point[1] for point in self.points) / len(self.points)
        self.drs_index = max(range(len(self.segment_lengths)), key=lambda index: self.segment_lengths[index])
        self.label_font = pygame.font.SysFont("segoeui", 16, bold=True)
        self.build_pit_lane()

    def draw(self, screen):
        """Vẽ làn pit, mặt đường, vùng DRS, vạch xuất phát và ba ô pit."""
        self.draw_pit_lane(screen)
        for point in self.points:
            pygame.draw.circle(screen, (214, 214, 214), point, (self.road_width + 12) // 2)
        pygame.draw.lines(screen, (214, 214, 214), True, self.points, self.road_width + 12)
        for point in self.points:
            pygame.draw.circle(screen, (48, 50, 56), point, self.road_width // 2)
        pygame.draw.lines(screen, (48, 50, 56), True, self.points, self.road_width)
        self.draw_drs_zone(screen)
        self.draw_start_line(screen)
        self.draw_pit_boxes(screen)

    def draw_pit_lane(self, screen):
        """Làn pit hẹp hơn đường đua, nối từ trước vạch ra sau vạch."""
        if len(self.pit_path) < 2:
            return
        pygame.draw.lines(screen, (210, 210, 210), False, self.pit_path, 26)
        pygame.draw.lines(screen, (36, 38, 44), False, self.pit_path, 18)

    def draw_drs_zone(self, screen):
        """Tô đoạn thẳng dài nhất bằng một vạch xanh và chữ DRS."""
        start = self.points[self.drs_index]
        end = self.points[(self.drs_index + 1) % len(self.points)]
        pygame.draw.line(screen, (36, 168, 78), start, end, 6)
        label_x = start[0] + (end[0] - start[0]) * 0.18
        label_y = start[1] + (end[1] - start[1]) * 0.18
        label = self.label_font.render("DRS", True, (236, 255, 236))
        plate = label.get_rect(center=(label_x, label_y))
        pygame.draw.rect(screen, (16, 70, 32), plate.inflate(8, 4), border_radius=3)
        screen.blit(label, plate)

    def draw_start_line(self, screen):
        """Vạch trắng ngang đường tại điểm xuất phát."""
        start_x, start_y, direction_x, direction_y = self.locate(0.0)
        side_x, side_y = self.side_direction(direction_x, direction_y)
        half_width = self.road_width / 2
        left = (start_x + side_x * half_width, start_y + side_y * half_width)
        right = (start_x - side_x * half_width, start_y - side_y * half_width)
        pygame.draw.line(screen, (245, 245, 245), left, right, 4)

    def draw_pit_boxes(self, screen):
        """Ba ô đỗ nằm trên làn pit."""
        for box_x, box_y in self.pit_boxes:
            pygame.draw.rect(screen, (22, 24, 30), (box_x - 16, box_y - 14, 32, 28), border_radius=2)
            pygame.draw.rect(screen, (190, 190, 190), (box_x - 16, box_y - 14, 32, 28), 1, border_radius=2)

    def build_pit_lane(self):
        """Dựng làn pit song song vạch xuất phát: vào từ trước vạch, ba ô, rồi nhập lại sau vạch."""
        start = self.points[0]
        following = self.points[1]
        direction_x = following[0] - start[0]
        direction_y = following[1] - start[1]
        scale = math.hypot(direction_x, direction_y) or 1
        forward_x = direction_x / scale
        forward_y = direction_y / scale
        inside_x, inside_y = self.inside_direction(direction_x, direction_y, start[0], start[1])
        lane_offset = self.road_width / 2 + 30

        def shift(distance_along):
            return (
                start[0] + forward_x * distance_along + inside_x * lane_offset,
                start[1] + forward_y * distance_along + inside_y * lane_offset,
            )

        entry_on_track = (start[0] - forward_x * 110, start[1] - forward_y * 110)
        entry_lane = shift(-90)
        self.pit_boxes = [shift(-36), shift(8), shift(52)]
        exit_lane = shift(130)
        exit_on_track = (start[0] + forward_x * 160, start[1] + forward_y * 160)
        self.pit_path = [
            entry_on_track,
            entry_lane,
            self.pit_boxes[0],
            self.pit_boxes[1],
            self.pit_boxes[2],
            exit_lane,
            exit_on_track,
        ]

    def locate(self, progress):
        """Đổi tiến độ một vòng thành tọa độ và hướng của đoạn thẳng đang đứng."""
        distance = (progress % 1.0) * self.total_length
        for index, length in enumerate(self.segment_lengths):
            if length == 0:
                continue
            if distance < length or index == len(self.segment_lengths) - 1:
                start = self.points[index]
                end = self.points[(index + 1) % len(self.points)]
                portion = 0 if length == 0 else min(1.0, distance / length)
                position_x = start[0] + (end[0] - start[0]) * portion
                position_y = start[1] + (end[1] - start[1]) * portion
                return position_x, position_y, end[0] - start[0], end[1] - start[1]
            distance -= length
        return self.points[0][0], self.points[0][1], 1, 0

    def car_pose(self, progress, lane_shift):
        """Vị trí làn và hướng mũi xe. Hướng lấy ngắn phía trước và sau để qua góc không bị nhảy."""
        position_x, position_y, _direction_x, _direction_y = self.locate(progress)
        look = 28.0 / self.total_length
        ahead_x, ahead_y, _ahead_dx, _ahead_dy = self.locate(progress + look)
        behind_x, behind_y, _behind_dx, _behind_dy = self.locate(progress - look)
        direction_x = ahead_x - behind_x
        direction_y = ahead_y - behind_y
        side_x, side_y = self.side_direction(direction_x, direction_y)
        return (
            position_x + side_x * lane_shift,
            position_y + side_y * lane_shift,
            direction_x,
            direction_y,
        )

    def side_direction(self, direction_x, direction_y):
        """Vectơ vuông góc với hướng chạy, dài bằng 1."""
        scale = math.hypot(direction_x, direction_y) or 1
        return -direction_y / scale, direction_x / scale

    def inside_direction(self, direction_x, direction_y, position_x, position_y):
        """Phía trong đường đua, hướng về tâm vòng."""
        side_x, side_y = self.side_direction(direction_x, direction_y)
        toward_center_x = self.center_x - position_x
        toward_center_y = self.center_y - position_y
        if side_x * toward_center_x + side_y * toward_center_y < 0:
            return -side_x, -side_y
        return side_x, side_y

    def pit_car_pose(self, pit_fraction, slot):
        """Xe vào làn, dừng ở ô của mình, rồi ra lại đường đua."""
        pit_fraction = max(0.0, min(1.0, pit_fraction))
        entry_on_track = self.pit_path[0]
        entry_lane = self.pit_path[1]
        box = self.pit_boxes[slot]
        exit_lane = self.pit_path[5]
        exit_on_track = self.pit_path[6]
        if pit_fraction < 0.28:
            position = self.mix_points(entry_on_track, entry_lane, pit_fraction / 0.28)
            return position[0], position[1], entry_lane[0] - entry_on_track[0], entry_lane[1] - entry_on_track[1]
        if pit_fraction < 0.45:
            position = self.mix_points(entry_lane, box, (pit_fraction - 0.28) / 0.17)
            return position[0], position[1], box[0] - entry_lane[0], box[1] - entry_lane[1]
        if pit_fraction < 0.72:
            return box[0], box[1], exit_lane[0] - box[0], exit_lane[1] - box[1]
        if pit_fraction < 0.86:
            position = self.mix_points(box, exit_lane, (pit_fraction - 0.72) / 0.14)
            return position[0], position[1], exit_lane[0] - box[0], exit_lane[1] - box[1]
        position = self.mix_points(exit_lane, exit_on_track, (pit_fraction - 0.86) / 0.14)
        return position[0], position[1], exit_on_track[0] - exit_lane[0], exit_on_track[1] - exit_lane[1]

    def mix_points(self, start, end, portion):
        """Điểm nằm giữa hai mốc. Portion bằng 0 là mốc đầu, bằng 1 là mốc cuối."""
        portion = max(0.0, min(1.0, portion))
        return (
            start[0] + (end[0] - start[0]) * portion,
            start[1] + (end[1] - start[1]) * portion,
        )

    def get_position(self, progress):
        """Đổi tiến độ một vòng, từ 0 đến 1, thành tọa độ trên đường."""
        position_x, position_y, _direction_x, _direction_y = self.locate(progress)
        return position_x, position_y

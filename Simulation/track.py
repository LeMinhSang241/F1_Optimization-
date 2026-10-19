import pygame
import math

class Track:
    def __init__(self):
        self.points = [
            (300, 180),
            (650, 180),
            (850, 320),
            (800, 550),
            (550, 650),
            (250, 600),
            (120, 400),
            (140, 180),
            ]
        self.road_width = 60
        self.segment_lengths = []

        #Tinh start, end, do dai doan
        for i in range(len(self.points)):
            start = self.points[i]
            end = self.points[(i + 1) % len(self.points)]

            length = math.dist(start, end)
            self.segment_lengths.append(length)
        
        self.total_length = sum(self.segment_lengths)

    def draw(self, screen):
        #Vien
        pygame.draw.lines(screen, (220, 220, 220), True, self.points, self.road_width + 10)
        #Mat duong
        pygame.draw.lines(screen, (65, 65, 70), True, self.points, self.road_width
    )

    #Tinh vi tri xe
    def get_position(self, progress):
        distance = (progress % 1.0) * self.total_length

        for i, length in enumerate(self.segment_lengths):
            if length == 0:
                continue
            if distance < length:
                start = self.points[i]
                end = self.points[(i + 1) % len(self.points)]
                p = distance / length
                x = start[0] + (end[0] - start[0]) * p
                y = start[1] + (end[1] - start[1]) * p
                return x, y
            distance -= length
        return self.points[0]
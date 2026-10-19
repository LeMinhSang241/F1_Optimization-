import pygame


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 26)

    def draw_text(self, text, position, color=(240, 240, 240)):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def draw(self, track, cars):
        # Nền và đường đua
        self.screen.fill((35, 85, 50))
        track.draw(self.screen)

        # Nền bảng thông tin bên phải
        pygame.draw.rect(
            self.screen,
            (25, 28, 35),
            (900, 0, 300, 800)
        )

        self.draw_text("RACE INFORMATION", (920, 60))

        for i, car in enumerate(cars):
            # Vẽ xe
            x, y = track.get_position(car.progress)

            pygame.draw.circle(
                self.screen,
                car.color,
                (round(x), round(y)),
                9
            )

            # Vẽ thông tin của xe
            row_y = 120 + i * 150

            self.draw_text(car.name, (920, row_y), car.color)

            self.draw_text(
                f"Laps: {car.laps_completed}/{car.total_laps}",
                (920, row_y + 30)
            )

            self.draw_text(
                f"Time: {car.elapsed:.1f} s",
                (920, row_y + 60)
            )

            status = car.status
            self.draw_text(status, (920, row_y + 90))

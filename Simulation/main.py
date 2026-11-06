import sys
from pathlib import Path

# Đảm bảo đường dẫn import trong thư mục Simulation
SIM_DIR = Path(__file__).resolve().parent
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import pygame
from track import Track
from race import RaceCar
from renderer import Renderer


def main():
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("F1 Pit-Stop Strategy 2D Simulation - DS106")
    clock = pygame.time.Clock()

    renderer = Renderer(screen)
    track = Track()

    # Tốc độ tua nhanh mô phỏng mặc định (60x: 1 phút ảo = 1 giây thực)
    SIM_TIME_SCALE = 60.0

    # Khởi tạo 3 chiến lược đối kháng trực tiếp
    cars = [
        RaceCar(
            name="GA Optimal (2-Stop)",
            color=(235, 45, 45),       # Đỏ Ferrari / Soft Accent
            strategy=[("Medium", 20), ("Soft", 14), ("Medium", 19)],
            time_scale=SIM_TIME_SCALE
        ),
        RaceCar(
            name="Verstappen (1-Stop)",
            color=(45, 135, 245),      # Xanh Red Bull
            strategy=[("Medium", 26), ("Hard", 27)],
            time_scale=SIM_TIME_SCALE
        ),
        RaceCar(
            name="Greedy (1-Stop)",
            color=(245, 195, 35),      # Vàng Medium
            strategy=[("Medium", 28), ("Hard", 25)],
            time_scale=SIM_TIME_SCALE
        ),
    ]

    running = True
    paused = False

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    for car in cars:
                        car.time_scale = min(200.0, car.time_scale + 20.0)
                elif event.key == pygame.K_DOWN:
                    for car in cars:
                        car.time_scale = max(10.0, car.time_scale - 20.0)

        if not paused:
            for car in cars:
                car.update(dt)

        # Vẽ đường đua, các xe và bảng thông số thời gian thực
        renderer.draw(track, cars)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

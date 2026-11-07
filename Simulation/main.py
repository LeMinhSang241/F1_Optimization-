import sys
from pathlib import Path

# Thư mục mô phỏng và thư mục gốc, để import được track và bảng cấu hình.
SIM_DIR = Path(__file__).resolve().parent
ROOT_DIR = SIM_DIR.parent
for folder in (str(SIM_DIR), str(ROOT_DIR)):
    if folder not in sys.path:
        sys.path.insert(0, folder)

import pygame
from audio import RaceAudio
from race import advance_cars, assign_race_order, demo_field, leader_race_lap, temperature_for_circuit
from renderer import Renderer
from track import Track


def main():
    """Mở cửa sổ và chạy ba xe. Phím đổi chặng, nhiệt độ, hệ số lốp và cờ."""
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("F1 Pit-Stop Strategy 2D Simulation - DS106")
    clock = pygame.time.Clock()
    renderer = Renderer(screen)
    race_audio = RaceAudio()

    circuit_key = "monza"
    track = Track(circuit_key)
    coefficient_source = "nominal"
    temperature_index = 1
    time_scale = 60.0
    paused = False
    cars, race_control, numbers = demo_field(
        circuit_key,
        temperature_for_circuit(circuit_key, temperature_index),
        coefficient_source,
        time_scale,
    )

    running = True
    while running:
        frame_seconds = min(clock.tick(60) / 1000.0, 1.0 / 30.0)
        rebuild_race = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    time_scale = min(200.0, time_scale + 20.0)
                    for car in cars:
                        car.time_scale = time_scale
                elif event.key == pygame.K_DOWN:
                    time_scale = max(10.0, time_scale - 20.0)
                    for car in cars:
                        car.time_scale = time_scale
                elif event.key == pygame.K_c:
                    circuit_key = "silverstone" if circuit_key == "monza" else "monza"
                    rebuild_race = True
                elif event.key == pygame.K_t:
                    temperature_index = (temperature_index + 1) % 3
                    rebuild_race = True
                elif event.key == pygame.K_f:
                    coefficient_source = "fitted" if coefficient_source == "nominal" else "nominal"
                    rebuild_race = True
                elif event.key == pygame.K_s:
                    race_control.request_flag("safety_car", leader_race_lap(cars))
                elif event.key == pygame.K_v:
                    race_control.request_flag("virtual_safety_car", leader_race_lap(cars))

        if rebuild_race:
            track = Track(circuit_key)
            cars, race_control, numbers = demo_field(
                circuit_key,
                temperature_for_circuit(circuit_key, temperature_index),
                coefficient_source,
                time_scale,
            )

        if not paused:
            advance_cars(cars, race_control, frame_seconds)
        assign_race_order(cars)

        reference_car = next(car for car in cars if car.is_reference)
        race_status = {
            "circuit_name": numbers["circuit_name"],
            "track_temperature": numbers["track_temperature"],
            "coefficient_source": coefficient_source,
            "flag_text": race_control.flag_text(),
            "planned_text": race_control.planned_text(),
            "message": race_control.message,
            "time_scale": time_scale,
            "paused": paused,
            "reference_name": reference_car.name,
            "mode": race_control.mode,
        }
        race_audio.update(paused, race_control, cars)
        renderer.draw(track, cars, race_status)
        pygame.display.flip()

    race_audio.stop()
    pygame.quit()


if __name__ == "__main__":
    main()

import pygame
from track import Track
from race import RaceCar
from renderer import Renderer

def main():
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("F1")
    clock = pygame.time.Clock()

    #VARIABLE
    renderer = Renderer(screen)
    cars = [
    RaceCar("Xe A", (230, 50, 50), lap_duration=10.0),
    RaceCar("Xe B", (50, 150, 240), lap_duration=12.0),
    RaceCar("Xe C", (240, 200, 50), lap_duration=14.0),
    ]
    track = Track()
    running = True

    while running:

        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        for car in cars: 
            car.update(dt)

        #Ve duong va xe
        renderer.draw(track, cars)
        
        pygame.display.flip()


    pygame.quit()


if __name__ == "__main__":
    main()

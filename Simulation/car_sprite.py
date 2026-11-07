import pygame


def build_car_surface(body_color, nose_color, wing_color, number_text):
    """Vẽ xe nhìn từ trên, mũi hướng lên, theo tỷ lệ ảnh mẫu. Không chép logo."""
    width = 120
    height = 250
    canvas = pygame.Surface((width, height), pygame.SRCALPHA)
    center = width // 2

    draw_wing(canvas, 8, 14, 14, wing_color, body_color)
    draw_wheel(canvas, 4, 34, nose_color)
    draw_wheel(canvas, width - 30, 34, nose_color)
    draw_nose(canvas, center, nose_color, body_color)
    draw_body(canvas, center, body_color, wing_color)
    draw_wheel(canvas, 2, 156, nose_color)
    draw_wheel(canvas, width - 28, 156, nose_color)
    draw_wing(canvas, 4, 214, 22, wing_color, body_color)
    draw_cockpit(canvas, center)
    draw_number(canvas, center, number_text)

    return pygame.transform.smoothscale(canvas, (30, 64))


def draw_wing(canvas, left, top, wing_height, wing_color, body_color):
    """Cánh trước hoặc cánh sau, có tấm chắn hai đầu."""
    width = canvas.get_width()
    pygame.draw.rect(canvas, wing_color, (left, top, width - left * 2, wing_height), border_radius=2)
    pygame.draw.rect(canvas, body_color, (left + 16, top + 4, width - (left + 16) * 2, max(4, wing_height - 8)))
    pygame.draw.rect(canvas, wing_color, (left - 2, top - 2, 6, wing_height + 4))
    pygame.draw.rect(canvas, wing_color, (width - left - 4, top - 2, 6, wing_height + 4))


def draw_wheel(canvas, left, top, rim_color):
    """Lốp đen và vành, đặt ngoài thân xe như ảnh nhìn từ trên."""
    pygame.draw.ellipse(canvas, (16, 16, 18), (left, top, 26, 42))
    pygame.draw.ellipse(canvas, (62, 64, 70), (left + 5, top + 8, 16, 26))
    pygame.draw.ellipse(canvas, rim_color, (left + 9, top + 14, 8, 14))


def draw_nose(canvas, center, nose_color, body_color):
    """Mũi xe thu nhỏ từ buồng lái ra cánh trước."""
    nose = [
        (center - 6, 22),
        (center + 6, 22),
        (center + 12, 78),
        (center - 12, 78),
    ]
    pygame.draw.polygon(canvas, nose_color, nose)
    pygame.draw.polygon(canvas, body_color, [
        (center - 3, 28),
        (center + 3, 28),
        (center + 5, 70),
        (center - 5, 70),
    ])


def draw_body(canvas, center, body_color, wing_color):
    """Thân xe và hai hốc gió hai bên buồng lái."""
    body = [
        (center - 16, 72),
        (center + 16, 72),
        (center + 24, 118),
        (center + 18, 168),
        (center - 18, 168),
        (center - 24, 118),
    ]
    pygame.draw.polygon(canvas, body_color, body)
    pygame.draw.polygon(canvas, wing_color, [
        (center - 24, 108),
        (center - 14, 96),
        (center - 14, 150),
        (center - 22, 162),
    ])
    pygame.draw.polygon(canvas, wing_color, [
        (center + 24, 108),
        (center + 14, 96),
        (center + 14, 150),
        (center + 22, 162),
    ])


def draw_cockpit(canvas, center):
    """Buồng lái tối và mũ bảo hiểm sáng ở giữa xe."""
    pygame.draw.ellipse(canvas, (10, 12, 16), (center - 11, 96, 22, 36))
    pygame.draw.ellipse(canvas, (226, 214, 196), (center - 6, 106, 12, 16))


def draw_number(canvas, center, number_text):
    """Số xe trên mũi."""
    font = pygame.font.Font(None, 28)
    label = font.render(number_text, True, (245, 245, 245))
    shadow = font.render(number_text, True, (12, 12, 12))
    place = label.get_rect(center=(center, 58))
    canvas.blit(shadow, (place.x + 1, place.y + 1))
    canvas.blit(label, place)


def looks_for_starting_order(starting_order):
    """Ba bộ màu: đỏ, xanh navy với mũi vàng như ảnh mẫu, và vàng."""
    looks = [
        ((186, 28, 36), (186, 28, 36), (24, 24, 28), "16"),
        ((16, 32, 78), (214, 176, 28), (150, 24, 32), "33"),
        ((214, 168, 28), (214, 168, 28), (28, 28, 32), "4"),
    ]
    return looks[starting_order]

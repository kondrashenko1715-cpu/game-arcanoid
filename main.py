import array
import math
import random
import pygame

pygame.init()
pygame.mixer.init(44100, -16, 1, 512)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()


def make_sound(freq, duration=0.08, volume=0.3):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array("h")
    for i in range(n_samples):
        fade = 1.0 - (i / n_samples)
        val = int(
            32767
            * volume
            * fade
            * math.sin(2 * math.pi * freq * i / sample_rate)
        )
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf)


snd_wall = make_sound(300, 0.05, 0.2)
snd_paddle = make_sound(500, 0.07, 0.3)
snd_brick = make_sound(750, 0.08, 0.3)
snd_bonus = make_sound(880, 0.12, 0.35)
snd_level_up = make_sound(1050, 0.2, 0.35)
snd_fall = make_sound(220, 0.2, 0.35)
snd_over = make_sound(140, 0.4, 0.4)
snd_upgrade = make_sound(1200, 0.15, 0.4)

DARK = (25, 25, 35)
PANEL_BG = (35, 38, 52)
WHITE = (255, 255, 255)
BLUE = (50, 160, 255)
YELLOW = (255, 220, 50)
GREEN = (60, 220, 110)
GRAY = (110, 115, 130)

FLOOR1_COLS = [
    (255, 65, 65),
    (255, 155, 45),
    (255, 230, 85),
]
ALL_COLS = [
    (255, 65, 65),
    (255, 155, 45),
    (255, 230, 85),
    (75, 220, 120),
    (50, 180, 255),
    (185, 95, 255),
    (255, 105, 180),
]

font = pygame.font.SysFont(None, 52)
small_font = pygame.font.SysFont(None, 38)
big_font = pygame.font.SysFont(None, 72)

upgrades = {
    "width": {
        "name": "Ширина платформы",
        "lvl": 0,
        "max": 5,
        "cost": 100,
        "req": None,
    },
    "power": {
        "name": "Сила удара (урон)",
        "lvl": 0,
        "max": 5,
        "cost": 150,
        "req": "width",
    },
    "luck": {
        "name": "Шанс бонусов",
        "lvl": 0,
        "max": 5,
        "cost": 200,
        "req": "width",
    },
    "greed": {
        "name": "Множитель очков",
        "lvl": 0,
        "max": 5,
        "cost": 300,
        "req": "power",
    },
}

paddle_h = 32
paddle_y = int(HEIGHT * 0.84)
wide_timer = 0
score = 0
current_floor = 1
floors_data = {}
falling_mode = False
in_tree = False


def get_base_paddle_w():
    return int((WIDTH // 3.4) * (1 + upgrades.get("width").get("lvl") * 0.14))


paddle_w = get_base_paddle_w()
paddle_x = WIDTH // 2 - paddle_w // 2


def spawn_ball(x, y, dy=-11.0):
    return {
        "x": float(x),
        "y": float(y),
        "dx": float(random.choice((-10, -8, 8, 10))),
        "dy": float(dy),
        "r": 20,
    }


def generate_floor(floor_num):
    bricks = []
    rows = 3
    cols = 6
    gap = 12
    brick_w = (WIDTH - gap * (cols + 1)) // cols
    brick_h = 46
    top_offset = 175

    for row in range(rows):
        row_color = (
            FLOOR1_COLS[row]
            if floor_num == 1
            else random.choice(ALL_COLS)
        )
        for col in range(cols):
            bx = gap + col * (brick_w + gap)
            by = top_offset + row * (brick_h + gap)
            col_color = (
                row_color
                if floor_num == 1
                else random.choice(ALL_COLS)
            )
            bricks.append(
                {
                    "rect": pygame.Rect(bx, by, brick_w, brick_h),
                    "hp": floor_num,
                    "color": col_color,
                }
            )
    return bricks


def start_new_run():
    global current_floor, floors_data, falling_mode, wide_timer, paddle_w, paddle_x
    current_floor = 1
    floors_data = {1: generate_floor(1)}
    falling_mode = False
    wide_timer = 0
    paddle_w = get_base_paddle_w()
    paddle_x = WIDTH // 2 - paddle_w // 2
    return [spawn_ball(WIDTH // 2, paddle_y - 30)], []


balls, bonuses = start_new_run()
restart_btn = pygame.Rect(WIDTH // 2 - 190, HEIGHT - 150, 380, 75)
running = True
while running:
    screen.fill(DARK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if in_tree:
                if restart_btn.collidepoint(mx, my):
                    in_tree = False
                    balls, bonuses = start_new_run()
                else:
                    y_pos = 240
                    for key, upg in upgrades.items():
                        card_rect = pygame.Rect(50, y_pos, WIDTH - 100, 145)
                        req = upg.get("req")
                        unlocked = req is None or upgrades.get(req).get("lvl") >= 1
                        if (
                            card_rect.collidepoint(mx, my)
                            and unlocked
                            and upg.get("lvl") < upg.get("max")
                            and score >= upg.get("cost")
                        ):
                            score -= upg.get("cost")
                            upg["lvl"] += 1
                            upg["cost"] = int(upg.get("cost") * 1.7)
                            snd_upgrade.play()
                        y_pos += 170
            elif not falling_mode:
                paddle_x = mx - paddle_w // 2
        elif (
            event.type == pygame.MOUSEMOTION
            and any(pygame.mouse.get_pressed())
            and not in_tree
            and not falling_mode
        ):
            paddle_x = event.pos[0] - paddle_w // 2

    if not in_tree:
        base_w = get_base_paddle_w()
        if wide_timer > 0:
            wide_timer -= 1
            paddle_w = int(base_w * 1.4)
        else:
            paddle_w = base_w

        paddle_x = max(0, min(WIDTH - paddle_w, paddle_x))
        paddle_rect = pygame.Rect(paddle_x, paddle_y, paddle_w, paddle_h)
        bricks = floors_data.get(current_floor)

        if not falling_mode:
            for b in bonuses[:]:
                br = b.get("rect")
                br.y += 7
                if br.top > HEIGHT:
                    bonuses.remove(b)
                elif br.colliderect(paddle_rect):
                    snd_bonus.play()
                    score += 25 * (1 + upgrades.get("greed").get("lvl"))
                    if b.get("type") == "W":
                        wide_timer = 600
                    elif b.get("type") == "M" and balls:
                        ref = next(iter(balls))
                        new_b = spawn_ball(ref.get("x"), ref.get("y"), ref.get("dy"))
                        new_b["dx"] = -ref.get("dx")
                        balls.append(new_b)
                    bonuses.remove(b)

        for ball in balls[:]:
            ball["x"] += ball.get("dx")
            ball["y"] += ball.get("dy")
            r = ball.get("r")

            if ball.get("x") - r <= 0:
                ball["x"] = r
                ball["dx"] = -ball.get("dx")
                snd_wall.play()
            elif ball.get("x") + r >= WIDTH:
                ball["x"] = WIDTH - r
                ball["dx"] = -ball.get("dx")
                snd_wall.play()

            if ball.get("y") + r < 0:
                if not falling_mode:
                    snd_level_up.play()
                    current_floor += 1
                    if current_floor not in floors_data:
                        floors_data[current_floor] = generate_floor(current_floor)
                    bonuses.clear()
                    balls = [spawn_ball(ball.get("x"), paddle_y - 35, -11.5)]
                    break
                else:
                    ball["y"] = r
                    ball["dy"] = abs(ball.get("dy"))
                    snd_wall.play()

            if ball.get("y") - r > HEIGHT:
                if len(balls) > 1:
                    balls.remove(ball)
                    continue
                elif current_floor > 1:
                    snd_fall.play()
                    falling_mode = True
                    bonuses.clear()
                    current_floor -= 1
                    ball["y"] = r + 10
ball["dy"] = abs(ball.get("dy"))
                    break
                else:
                    snd_over.play()
                    in_tree = True
                    break

            ball_rect = pygame.Rect(
                ball.get("x") - r, ball.get("y") - r, r * 2, r * 2
            )

            if (
                not falling_mode
                and ball_rect.colliderect(paddle_rect)
                and ball.get("dy") > 0
            ):
                snd_paddle.play()
                ball["dy"] = -abs(ball.get("dy"))
                hit_pos = (ball.get("x") - paddle_rect.centerx) / (paddle_w / 2)
                ball["dx"] = hit_pos * 14
                if abs(ball.get("dx")) < 2:
                    ball["dx"] = random.choice((-4, 4))

            damage = 1 + upgrades.get("power").get("lvl")
            bonus_chance = 0.25 + upgrades.get("luck").get("lvl") * 0.1
            score_mult = 1 + upgrades.get("greed").get("lvl")

            for brick in bricks[:]:
                rect = brick.get("rect")
                if ball_rect.colliderect(rect):
                    brick["hp"] -= damage
                    snd_brick.play()
                    if brick.get("hp") <= 0:
                        bricks.remove(brick)
                        score += 10 * current_floor * score_mult
                        if not falling_mode and random.random() < bonus_chance:
                            b_type = random.choice(("W", "M"))
                            b_rect = pygame.Rect(
                                rect.centerx - 30, rect.centery - 18, 60, 36
                            )
                            bonuses.append({"rect": b_rect, "type": b_type})

                    if (
                        abs(ball_rect.bottom - rect.top) < 22
                        or abs(ball_rect.top - rect.bottom) < 22
                    ):
                        ball["dy"] = -ball.get("dy")
                    else:
                        ball["dx"] = -ball.get("dx")
                    break

    for brick in floors_data.get(current_floor):
        hp = brick.get("hp")
        rect = brick.get("rect")
        pygame.draw.rect(screen, brick.get("color"), rect, border_radius=8)
        if hp > 1:
            hp_txt = small_font.render(str(hp), True, DARK)
            screen.blit(
                hp_txt,
                (
                    rect.centerx - hp_txt.get_width() // 2,
                    rect.centery - hp_txt.get_height() // 2,
                ),
            )

    if not falling_mode:
        for b in bonuses:
            rect = b.get("rect")
            tp = b.get("type")
            col = GREEN if tp == "W" else (0, 220, 255)
            pygame.draw.rect(screen, col, rect, border_radius=12)
            txt = small_font.render(tp, True, DARK)
            screen.blit(
                txt,
                (
                    rect.centerx - txt.get_width() // 2,
                    rect.centery - txt.get_height() // 2,
                ),
            )

        pygame.draw.rect(
            screen,
            BLUE,
            (paddle_x, paddle_y, paddle_w, paddle_h),
            border_radius=12,
        )

    for ball in balls:
        pygame.draw.circle(
            screen,
            YELLOW,
            (int(ball.get("x")), int(ball.get("y"))),
            ball.get("r"),
        )

    score_surf = font.render(f"Очки: {score}", True, WHITE)
    floor_surf = small_font.render(f"Этаж: {current_floor}", True, YELLOW)
    screen.blit(score_surf, (35, 80))
    screen.blit(floor_surf, (35, 130))

    if falling_mode and not in_tree:
        fall_txt = font.render("ПАДЕНИЕ!", True, (255, 80, 80))
        screen.blit(fall_txt, (WIDTH - fall_txt.get_width() - 35, 95))

    if in_tree:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(238)
        overlay.fill(DARK)
        screen.blit(overlay, (0, 0))

        title = big_font.render("ПРОИГРЫШ — ПРОКАЧКА", True, YELLOW)
pts = font.render(f"Ваши очки: {score}", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 75))
        screen.blit(pts, (WIDTH // 2 - pts.get_width() // 2, 155))

        y_pos = 240
        for key, upg in upgrades.items():
            card_rect = pygame.Rect(50, y_pos, WIDTH - 100, 145)
            req = upg.get("req")
            unlocked = req is None or upgrades.get(req).get("lvl") >= 1

            border_col = GREEN if unlocked else GRAY
            pygame.draw.rect(screen, PANEL_BG, card_rect, border_radius=14)
            pygame.draw.rect(screen, border_col, card_rect, 3, border_radius=14)

            name_txt = font.render(
                f"{upg.get('name')} [{upg.get('lvl')}/{upg.get('max')}]",
                True,
                WHITE if unlocked else GRAY,
            )
            screen.blit(name_txt, (75, y_pos + 22))

            if not unlocked:
                req_name = upgrades.get(req).get("name")
                status_txt = small_font.render(
                    f"Нужно открыть: {req_name}", True, (255, 100, 100)
                )
            elif upg.get("lvl") >= upg.get("max"):
                status_txt = small_font.render("МАКСИМУМ", True, YELLOW)
            else:
                can_buy = score >= upg.get("cost")
                status_txt = small_font.render(
                    f"Улучшить за {upg.get('cost')} очков",
                    True,
                    GREEN if can_buy else GRAY,
                )

            screen.blit(status_txt, (75, y_pos + 82))
            y_pos += 170

        pygame.draw.rect(screen, GREEN, restart_btn, border_radius=14)
        c_txt = font.render("ИГРАТЬ СНОВА", True, DARK)
        screen.blit(
            c_txt,
            (
                restart_btn.centerx - c_txt.get_width() // 2,
                restart_btn.centery - c_txt.get_height() // 2,
            ),
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

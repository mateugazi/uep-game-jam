import pygame
import random
import sys
import os
import json

# --- Stałe ---
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800

START_BG = pygame.image.load(os.path.join('assets', 'background', 'altum.png'))
GAME_BG = pygame.image.load(os.path.join('assets', 'background', 'platform_background.png'))
TARAS_BG = pygame.image.load(os.path.join('assets', 'background', 'taras.png'))
TARAS_BG = pygame.transform.scale(TARAS_BG, (SCREEN_WIDTH, SCREEN_HEIGHT))

PLAYER_WIDTH = 60
PLAYER_HEIGHT = 60
PLATFORM_WIDTH = 80
PLATFORM_HEIGHT = 31
PLATFORM_IMG = pygame.image.load(os.path.join('assets', 'background', 'platform123.png'))
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLATFORM_COLOR = (50, 200, 50)
OBSTACLE_COLOR = (200, 40, 40)
BUTTON_COLOR = (100, 220, 120)
BUTTON_HOVER = (60, 170, 80)
FPS = 60

PLATFORM_MIN_DIST = 80
PLATFORM_MAX_DIST = 140

OBSTACLE_WIDTH = 80
OBSTACLE_HEIGHT = 121
OBSTACLE_CHANCE_PER_FRAME = 0.003

# --- Plik z rekordem ---
HIGHSCORE_FILE = "highscore.json"

# --- Definicja postaci (dostępne wybory) ---
CHARACTERS = [
    {
        "name": "Klasyczny",
        "spirit": os.path.join('assets', 'hero', 'hero_spirit.png'),
        "jump": os.path.join('assets', 'hero', 'hero_jump.png'),
        "power_jump_strength": -20,
        "power_jump_cd": 5.0
    },
    {
        "name": "Lewusek 2.0",
        "spirit": os.path.join('assets', 'hero', 'hero_spirit2.png'),
        "jump": os.path.join('assets', 'hero', 'hero_jump2.png'),
        "power_jump_strength": -26,  # wyżej skacze!
        "power_jump_cd": 7.0  # dłuższy cooldown!
    }
]

pygame.init()
pygame.mixer.init()
pygame.mixer.music.load(os.path.join('assets', 'sound', 'muzyka.wav'))
pygame.mixer.music.set_volume(0.2)  # Głośność (0.0 - 1.0)
pygame.mixer.music.play(-1)  # -1 = zapętlona muzyka
JUMP_SOUND = pygame.mixer.Sound(os.path.join('assets', 'sound', 'jump.wav'))
POWERJUMP_SOUND = pygame.mixer.Sound(os.path.join('assets', 'sound', 'jump2.wav'))
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("MISJA UEP")
clock = pygame.time.Clock()
WIND_IMG = pygame.image.load(os.path.join('assets', 'background', 'winda.png'))


def get_font(name_list, size, bold=False):
    for name in name_list:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except:
            continue
    return pygame.font.SysFont('arial', size, bold=bold)


NICE_FONTS = [
    'Arial Narrow', 'Montserrat', 'Comic Sans MS', 'Verdana', 'Arial'
]

font = get_font(NICE_FONTS, 28)
big_font = get_font(NICE_FONTS, 48, bold=True)
alert_font = get_font(NICE_FONTS, 18, bold=True)
score_font = get_font(NICE_FONTS, 32, bold=True)
cd_font = get_font(NICE_FONTS, 24, bold=True)
desc_font = get_font(NICE_FONTS, 23)


def load_image(path, size):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, size)


def draw_button(text, rect, mouse_pos):
    color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=10)
    label = font.render(text, True, BLACK)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)


def draw_alert(text):
    center_x = SCREEN_WIDTH // 2
    y = 80
    msg = alert_font.render(text, True, (220, 0, 0))
    screen.blit(msg, (center_x - msg.get_width() // 2, y))


# --- Funkcje obsługujące rekord ---
def load_highscore():
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            data = json.load(f)
        return data.get('highscore', 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def save_highscore(score):
    try:
        highscore = load_highscore()
        if score > highscore:
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump({'highscore': score}, f)
            return True
        return False
    except:
        return False


# --- Start screen z wyborem postaci i sliderem ---
def show_start_screen():
    bg_img = pygame.transform.scale(START_BG, (SCREEN_WIDTH, SCREEN_HEIGHT))
    title = big_font.render("MISJA UEP", True, (30, 40, 200))
    welcome_lines = [
        "Doskocz jak najwyżej.",
        "Unikaj spadających wind.",
        "Sterowanie: strzałki — poruszanie się.",
        "SPACJA — Power Jump (co 5 sek.)",
    ]
    button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 590, 200, 54)

    # --- Slider ---
    slider_x = SCREEN_WIDTH // 2 - 120
    slider_y = 730
    slider_w = 240
    slider_h = 8
    knob_r = 14
    dragging = False

    # --- Wybór postaci ---
    selected_char = 0
    char_rects = []
    char_preview_y = 410
    char_preview_spacing = 180

    overlay_height = len(welcome_lines) * 36 + 32
    overlay = pygame.Surface((SCREEN_WIDTH - 70, overlay_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))

    highscore = load_highscore()
    char_images = []
    for c in CHARACTERS:
        s = load_image(c["spirit"], (PLAYER_WIDTH, PLAYER_HEIGHT))
        char_images.append(s)

    def get_knob_pos(vol):
        return int(slider_x + vol * slider_w)

    waiting = True
    while waiting:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                vol = pygame.mixer.music.get_volume()
                knob_x = get_knob_pos(vol)
                knob_rect = pygame.Rect(knob_x - knob_r, slider_y - knob_r, knob_r * 2, knob_r * 2)
                slider_rect = pygame.Rect(slider_x, slider_y - slider_h // 2, slider_w, slider_h * 2)
                if knob_rect.collidepoint(mouse_pos) or slider_rect.collidepoint(mouse_pos):
                    dragging = True
                for idx, rect in enumerate(char_rects):
                    if rect.collidepoint(mouse_pos):
                        selected_char = idx
                if button_rect.collidepoint(mouse_pos):
                    waiting = False
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                mouse_x = max(slider_x, min(slider_x + slider_w, mouse_pos[0]))
                new_vol = (mouse_x - slider_x) / slider_w
                pygame.mixer.music.set_volume(new_vol)

        screen.blit(bg_img, (0, 0))
        # Tytuł
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 35))

        # Instrukcje
        screen.blit(overlay, (35, 120))
        y = 140
        for line in welcome_lines:
            rendered = desc_font.render(line, True, (240, 240, 240))
            screen.blit(rendered, (SCREEN_WIDTH // 2 - rendered.get_width() // 2, y))
            y += 34

        # Najlepszy wynik
        if highscore > 0:
            highscore_text = desc_font.render(f"Najlepszy wynik: {highscore}", True, (255, 215, 0))
            screen.blit(highscore_text, (SCREEN_WIDTH // 2 - highscore_text.get_width() // 2, 260))

        # --- Wybór postaci ---
        char_rects = []
        cx = SCREEN_WIDTH // 2 - ((len(CHARACTERS) - 1) * char_preview_spacing) // 2
        for idx, c in enumerate(CHARACTERS):
            r = pygame.Rect(cx + idx * char_preview_spacing - 45, char_preview_y - 15, 90, 110)
            char_rects.append(r)
            # Overlay pod każdą postacią
            char_overlay = pygame.Surface((90, 110), pygame.SRCALPHA)
            char_overlay.fill((15, 15, 18, 170))
            screen.blit(char_overlay, (r.x, r.y))
            pygame.draw.rect(screen, (120, 120, 120) if idx != selected_char else (30, 180, 50), r, border_radius=20, width=6 if idx == selected_char else 2)
            # Obrazek postaci
            img = char_images[idx]
            screen.blit(img, (r.x + (r.width - PLAYER_WIDTH) // 2, r.y + 12))
            # Nazwa postaci
            name = desc_font.render(CHARACTERS[idx]["name"], True, (255, 255, 255))
            screen.blit(name, (r.x + (r.width - name.get_width()) // 2, r.y + 66))
            # Parametry
            param = desc_font.render(
                f'Skok: {"++" if c["power_jump_strength"] < -22 else "+"}, CD: {c["power_jump_cd"]}s', True,
                (255, 220, 255))
            screen.blit(param, (r.x + (r.width - param.get_width()) // 2, r.y + 88))

        # Przycisk START
        draw_button("START", button_rect, mouse_pos)

        # --- Slider --- (duży ciemny overlay pod całością)
        slider_overlay = pygame.Surface((slider_w + 88, 90), pygame.SRCALPHA)
        slider_overlay.fill((0, 0, 0, 195))
        screen.blit(slider_overlay, (slider_x - 44, slider_y - 50))
        vol_big_font = get_font(NICE_FONTS, 32, bold=True)
        vol = pygame.mixer.music.get_volume()
        vol_text = vol_big_font.render(f"Głośność muzyki: {int(vol * 100)}%", True, (255, 255, 255))
        shadow = vol_big_font.render(f"Głośność muzyki: {int(vol * 100)}%", True, (30, 30, 30))
        shadow_x = SCREEN_WIDTH // 2 - vol_text.get_width() // 2 + 2
        shadow_y = slider_y - 38 + 2
        screen.blit(shadow, (shadow_x, shadow_y))
        screen.blit(vol_text, (SCREEN_WIDTH // 2 - vol_text.get_width() // 2, slider_y - 38))
        quiet_icon = font.render("🔈", True, (180, 220, 255))
        loud_icon = font.render("🔊", True, (180, 220, 255))
        screen.blit(quiet_icon, (slider_x - 35, slider_y - 10))
        screen.blit(loud_icon, (slider_x + slider_w + 8, slider_y - 10))
        pygame.draw.rect(screen, (230, 230, 255), (slider_x, slider_y - slider_h // 2, slider_w, slider_h + 2), border_radius=6)
        pygame.draw.rect(screen, (60, 200, 255), (slider_x, slider_y - slider_h // 2, int(vol * slider_w), slider_h + 2), border_radius=6)
        pygame.draw.rect(screen, (30, 30, 60), (slider_x, slider_y - slider_h // 2, slider_w, slider_h + 2), 2, border_radius=6)
        knob_x = int(slider_x + vol * slider_w)
        pygame.draw.circle(screen, (40, 160, 255), (knob_x, slider_y + 1), knob_r + 2)
        pygame.draw.circle(screen, (255, 255, 255), (knob_x, slider_y + 1), knob_r - 4)
        pygame.draw.circle(screen, (80, 80, 110), (knob_x, slider_y + 1), knob_r + 2, 3)

        pygame.display.flip()
        clock.tick(60)

    return selected_char


# --- Pause menu ---
def draw_pause_menu():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    pause_text = big_font.render("PAUZA", True, WHITE)
    screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))

    resume_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 30, 200, 50)
    quit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40, 200, 50)

    mouse_pos = pygame.mouse.get_pos()
    draw_button("Kontynuuj", resume_rect, mouse_pos)
    draw_button("Wyjdź", quit_rect, mouse_pos)

    return resume_rect, quit_rect


# --- Gra główna, uwzględnia wybraną postać! ---
def game_loop(selected_char):
    # Załaduj sprite'y i parametry dla wybranej postaci
    char = CHARACTERS[selected_char]
    spirit_img = load_image(char["spirit"], (PLAYER_WIDTH, PLAYER_HEIGHT))
    jump_img = load_image(char["jump"], (PLAYER_WIDTH, PLAYER_HEIGHT))
    power_jump_strength = char["power_jump_strength"]
    power_jump_cd = char["power_jump_cd"]

    class Player(pygame.sprite.Sprite):
        def __init__(self):
            super().__init__()
            self.images = {
                "spirit": spirit_img,
                "jump": jump_img
            }
            self.image = self.images["spirit"]
            self.rect = self.image.get_rect()
            self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
            self.vel_y = 0
            self.last_power_jump = -power_jump_cd

        def update(self):
            self.vel_y += 0.4
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.rect.x -= 7
            if keys[pygame.K_RIGHT]:
                self.rect.x += 7

            if self.rect.right > SCREEN_WIDTH:
                self.rect.left = 0
            elif self.rect.left < 0:
                self.rect.right = SCREEN_WIDTH

            self.rect.y += int(self.vel_y)

            if self.vel_y < 0:
                self.image = self.images["jump"]
            else:
                self.image = self.images["spirit"]

    class Platform(pygame.sprite.Sprite):
        def __init__(self, x, y):
            super().__init__()
            self.image = PLATFORM_IMG
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y

    class Obstacle(pygame.sprite.Sprite):
        def __init__(self, x):
            super().__init__()
            self.image = WIND_IMG
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = -OBSTACLE_HEIGHT
            self.speed = random.randint(3, 5)

        def update(self):
            self.rect.y += self.speed

    def add_next_platform(platforms):
        highest = min(platform.rect.y for platform in platforms)
        new_y = highest - random.randint(PLATFORM_MIN_DIST, PLATFORM_MAX_DIST)
        new_x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
        new_platform = Platform(new_x, new_y)
        platforms.add(new_platform)
        return new_platform

    def move_screen(player, platforms, obstacles, score):
        if player.rect.top <= SCREEN_HEIGHT // 4:
            offset = abs(player.vel_y)
            player.rect.y += int(offset)
            for plat in platforms:
                plat.rect.y += int(offset)
                if plat.rect.top >= SCREEN_HEIGHT:
                    plat.kill()
                    score += 1
            for obs in obstacles:
                obs.rect.y += int(offset)
        return score

    player = Player()
    platforms = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()

    base = Platform(SCREEN_WIDTH // 2 - PLATFORM_WIDTH // 2, SCREEN_HEIGHT - 60)
    platforms.add(base)
    last_y = SCREEN_HEIGHT - 60

    for i in range(7):
        x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
        last_y -= random.randint(PLATFORM_MIN_DIST, PLATFORM_MAX_DIST)
        platform = Platform(x, last_y)
        platforms.add(platform)

    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    all_sprites.add(platforms)
    all_sprites.add(obstacles)

    running = True
    paused = False
    score = 0
    show_cooldown_msg = False
    cooldown_msg_timer = 0

    # --- TŁO ---
    using_taras_bg = False
    crossfade = False
    crossfade_timer = 0
    crossfade_duration = 1.0  # sekundy
    crossfade_progress = 0

    while running:
        dt = clock.tick(FPS) / 1000
        current_time = pygame.time.get_ticks() / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                elif event.key == pygame.K_SPACE and not paused:
                    time_since_last = current_time - player.last_power_jump
                    if time_since_last >= power_jump_cd:
                        player.vel_y = power_jump_strength
                        player.last_power_jump = current_time
                        POWERJUMP_SOUND.play()
                    else:
                        show_cooldown_msg = True
                        cooldown_msg_timer = current_time
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and paused:
                mouse_pos = pygame.mouse.get_pos()
                resume_rect, quit_rect = draw_pause_menu()
                if resume_rect.collidepoint(mouse_pos):
                    paused = False
                elif quit_rect.collidepoint(mouse_pos):
                    return score

        if not paused:
            if player.vel_y > 0:
                hits = pygame.sprite.spritecollide(player, platforms, False)
                for hit in hits:
                    if player.rect.bottom <= hit.rect.bottom + 14:
                        player.rect.bottom = hit.rect.top
                        player.vel_y = -10
                        JUMP_SOUND.play()

            while len(platforms) < 8:
                new_platform = add_next_platform(platforms)
                all_sprites.add(new_platform)

            if random.random() < OBSTACLE_CHANCE_PER_FRAME:
                if player.rect.top < SCREEN_HEIGHT // 4:
                    safe_margin = 30
                    safe_left = max(0, player.rect.left - safe_margin)
                    safe_right = min(SCREEN_WIDTH, player.rect.right + safe_margin)
                    possible_ranges = []
                    if safe_left > 0:
                        left_range = (0, safe_left - OBSTACLE_WIDTH)
                        if left_range[1] > left_range[0]:
                            possible_ranges.append(left_range)
                    if safe_right < SCREEN_WIDTH:
                        right_range = (safe_right, SCREEN_WIDTH - OBSTACLE_WIDTH)
                        if right_range[1] > right_range[0]:
                            possible_ranges.append(right_range)
                    if possible_ranges:
                        spawn_range = random.choice(possible_ranges)
                        obs_x = random.randint(*spawn_range)
                        obstacle = Obstacle(obs_x)
                        obstacles.add(obstacle)
                        all_sprites.add(obstacle)
                else:
                    obs_x = random.randint(0, SCREEN_WIDTH - OBSTACLE_WIDTH)
                    obstacle = Obstacle(obs_x)
                    obstacles.add(obstacle)
                    all_sprites.add(obstacle)

            obstacles.update()
            for obs in list(obstacles):
                if obs.rect.top > SCREEN_HEIGHT:
                    obs.kill()

            if pygame.sprite.spritecollide(player, obstacles, False):
                running = False

            score = move_screen(player, platforms, obstacles, score)

            # --- Sprawdzanie zmiany tła na taras po przekroczeniu 50 ---
            if (not using_taras_bg) and (not crossfade) and (score >= 50):
                crossfade = True
                crossfade_timer = 0

            if player.rect.top > SCREEN_HEIGHT:
                running = False

            player.update()

            # --- tło z płynnym przejściem po 50 punktach ---
            if crossfade:
                crossfade_timer += dt
                crossfade_progress = min(crossfade_timer / crossfade_duration, 1.0)
                base_bg = GAME_BG.copy()
                taras_bg = TARAS_BG.copy()
                taras_bg.set_alpha(int(crossfade_progress * 255))
                screen.blit(base_bg, (0, 0))
                screen.blit(taras_bg, (0, 0))
                if crossfade_progress >= 1.0:
                    crossfade = False
                    using_taras_bg = True
            elif using_taras_bg:
                screen.blit(TARAS_BG, (0, 0))
            else:
                screen.blit(GAME_BG, (0, 0))

            all_sprites.draw(screen)
            score_text = score_font.render(f"Wynik: {score}", True, (40, 80, 220))
            screen.blit(score_text, (14, 14))

            cd_left = power_jump_cd - (current_time - player.last_power_jump)
            if cd_left < 0: cd_left = 0
            cd_txt = cd_font.render(f"Power Jump CD: {cd_left:.1f}s", True, (130, 130, 240))
            screen.blit(cd_txt, (SCREEN_WIDTH - cd_txt.get_width() - 18, 18))

            if show_cooldown_msg:
                draw_alert("POWER JUMP NA COOLDOWNIE!")
                if current_time - cooldown_msg_timer > 1.0:
                    show_cooldown_msg = False

        if paused:
            draw_pause_menu()

        pygame.display.flip()

    return score


def show_game_over(score):
    bg_img = pygame.transform.scale(START_BG, (SCREEN_WIDTH, SCREEN_HEIGHT))
    button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 80, 220, 50)
    waiting = True

    overlay_width = 360
    overlay_height = 240
    overlay_x = SCREEN_WIDTH // 2 - overlay_width // 2
    overlay_y = SCREEN_HEIGHT // 2 - 120

    overlay = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))

    new_highscore = save_highscore(score)
    highscore = load_highscore()

    while waiting:
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(bg_img, (0, 0))

        screen.blit(overlay, (overlay_x, overlay_y))

        over_text = big_font.render("KONIEC GRY", True, (200, 0, 0))
        shadow = big_font.render("KONIEC GRY", True, (0, 0, 0))
        text_x = SCREEN_WIDTH // 2 - over_text.get_width() // 2
        text_y = SCREEN_HEIGHT // 2 - 110
        screen.blit(shadow, (text_x + 3, text_y + 3))
        screen.blit(over_text, (text_x, text_y))

        score_text = font.render(f"Twój wynik: {score}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 40))

        highscore_text = font.render(f"Najlepszy wynik: {highscore}", True, (255, 215, 0))
        screen.blit(highscore_text, (SCREEN_WIDTH // 2 - highscore_text.get_width() // 2, SCREEN_HEIGHT // 2))

        if new_highscore:
            new_record_text = font.render("NOWY REKORD!", True, (255, 215, 0))
            screen.blit(new_record_text,
                        (SCREEN_WIDTH // 2 - new_record_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))

        draw_button("Zagraj ponownie", button_rect, mouse_pos)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(mouse_pos):
                    waiting = False


def main():
    while True:
        selected_char = show_start_screen()
        score = game_loop(selected_char)
        show_game_over(score)


if __name__ == '__main__':
    main()

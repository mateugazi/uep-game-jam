import pygame
import random
import sys
import os

# --- Stałe ---
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 60
PLATFORM_WIDTH = 80
PLATFORM_HEIGHT = 18
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLATFORM_COLOR = (50, 200, 50)
OBSTACLE_COLOR = (200, 40, 40)
BUTTON_COLOR = (100, 220, 120)
BUTTON_HOVER = (60, 170, 80)
FPS = 60

PLATFORM_MIN_DIST = 80
PLATFORM_MAX_DIST = 140

OBSTACLE_WIDTH = 48
OBSTACLE_HEIGHT = 48
OBSTACLE_CHANCE_PER_FRAME = 0.009  # Mniej przeszkód!

POWER_JUMP_CD = 5.0  # sekundy
POWER_JUMP_STRENGTH = -20  # dwa razy większy skok

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Endless Jumper")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 28)
big_font = pygame.font.SysFont('Arial', 42)
alert_font = pygame.font.SysFont('Arial', 17, bold=True)

def load_image(path, size):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, size)

SPIRIT_IMG = load_image(os.path.join('assets', 'hero', 'hero_spirit.png'), (PLAYER_WIDTH, PLAYER_HEIGHT))
JUMP_IMG = load_image(os.path.join('assets', 'hero', 'hero_jump.png'), (PLAYER_WIDTH, PLAYER_HEIGHT))

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images = {
            "spirit": SPIRIT_IMG,
            "jump": JUMP_IMG
        }
        self.image = self.images["spirit"]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
        self.vel_y = 0
        self.last_power_jump = -POWER_JUMP_CD

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
        self.image = pygame.Surface((PLATFORM_WIDTH, PLATFORM_HEIGHT))
        self.image.fill(PLATFORM_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        self.image = pygame.Surface((OBSTACLE_WIDTH, OBSTACLE_HEIGHT))
        self.image.fill(OBSTACLE_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = -OBSTACLE_HEIGHT
        self.speed = random.randint(3, 5)  # WOLNIEJSZE!

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

def draw_button(text, rect, mouse_pos):
    color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=10)
    label = font.render(text, True, BLACK)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

def draw_alert(text):
    alert = alert_font.render(text, True, (255, 0, 0))
    rect = alert.get_rect(center=(SCREEN_WIDTH // 2, 40))  # Niżej!
    # biała ramka pod spodem
    outline = alert_font.render(text, True, (255,255,255))
    outline_rect = outline.get_rect(center=(SCREEN_WIDTH // 2 + 2, 42))
    screen.blit(outline, outline_rect)
    screen.blit(alert, rect)

def game_loop():
    player = Player()
    platforms = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()

    base = Platform(SCREEN_WIDTH//2 - PLATFORM_WIDTH//2, SCREEN_HEIGHT - 60)
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
    score = 0
    show_cooldown_msg = False
    cooldown_msg_timer = 0

    while running:
        dt = clock.tick(FPS) / 1000
        current_time = pygame.time.get_ticks() / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    time_since_last = current_time - player.last_power_jump
                    if time_since_last >= POWER_JUMP_CD:
                        player.vel_y = POWER_JUMP_STRENGTH
                        player.last_power_jump = current_time
                    else:
                        show_cooldown_msg = True
                        cooldown_msg_timer = current_time

        if player.vel_y > 0:
            hits = pygame.sprite.spritecollide(player, platforms, False)
            for hit in hits:
                if player.rect.bottom <= hit.rect.bottom + 14:
                    player.rect.bottom = hit.rect.top
                    player.vel_y = -10

        while len(platforms) < 8:
            new_platform = add_next_platform(platforms)
            all_sprites.add(new_platform)

        # Losowe przeszkody - z ochroną głowy, gdy gracz jest wysoko
        if random.random() < OBSTACLE_CHANCE_PER_FRAME:
            if player.rect.top < SCREEN_HEIGHT // 4:
                # Safe zone: szerokość gracza + bufor
                safe_margin = 30
                safe_left = max(0, player.rect.left - safe_margin)
                safe_right = min(SCREEN_WIDTH, player.rect.right + safe_margin)
                possible_ranges = []
                # Dodajemy tylko zakresy z sensem!
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
                # Jak nie ma gdzie wrzucić, nie spawnujemy przeszkody
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
        if player.rect.top > SCREEN_HEIGHT:
            running = False

        player.update()
        screen.fill(WHITE)
        all_sprites.draw(screen)
        score_text = font.render(f"Wynik: {score}", True, BLACK)
        screen.blit(score_text, (12, 12))

        cd_left = POWER_JUMP_CD - (current_time - player.last_power_jump)
        if cd_left < 0: cd_left = 0
        cd_txt = font.render(f"Power Jump CD: {cd_left:.1f}s", True, (80, 80, 240))
        screen.blit(cd_txt, (SCREEN_WIDTH - cd_txt.get_width() - 16, 12))

        if show_cooldown_msg:
            draw_alert("POWER JUMP NA COOLDOWNIE!")
            if current_time - cooldown_msg_timer > 1.0:
                show_cooldown_msg = False

        pygame.display.flip()

    return score

def show_game_over(score):
    button_rect = pygame.Rect(SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT//2 + 30, 220, 50)
    waiting = True

    while waiting:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)
        over_text = big_font.render("KONIEC GRY", True, (200, 0, 0))
        score_text = font.render(f"Twój wynik: {score}", True, BLACK)
        screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//2 - 90))
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2 - 40))
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
        score = game_loop()
        show_game_over(score)

if __name__ == '__main__':
    main()

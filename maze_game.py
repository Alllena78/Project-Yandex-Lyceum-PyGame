import pygame
import sys
import os
import math
import random

# Параметры окна и игры
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
TILE_SIZE = 40

# Цвета
BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
RED    = (255, 0, 0)
GREEN  = (0, 255, 0)
BLUE   = (0, 0, 255)
GRAY   = (100, 100, 100)
YELLOW = (255, 255, 0)

# Дополнительные цвета для оформления
DARK_OVERLAY      = (0, 0, 0, 180)
BUTTON_COLOR      = (50, 50, 50)
BUTTON_TEXT_COLOR = (255, 255, 255)
WALL_COLOR        = (240, 240, 240)
GRID_COLOR        = (150, 150, 150)

# План лабиринта 
MAZE_LAYOUT = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,0,1,1,1,1,0,1,0,1,0,1,0,1,0,1],
    [1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,1,1,1,1,0,1,1,1,0,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1],
    [1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,1,1,1,0,1,1,1,0,1,1,1,0,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,1,1,1,1,0,1,1,1,0,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]

START_POS = (1, 1)
EXIT_POS  = (13, 18)

# --- Класс для эффекта частиц ---
class Particle:
    def __init__(self, pos, velocity, lifetime, color, size):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.lifetime = lifetime
        self.initial_lifetime = lifetime
        self.color = color  # Цвет как (R, G, B)
        self.size = size

    def update(self, dt):
        self.pos += self.velocity * dt
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = max(0, int(255 * (self.lifetime / self.initial_lifetime)))
            # Создаем поверхность для частицы с альфа-каналом
            particle_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            # Рисуем круг на этой поверхности
            pygame.draw.circle(particle_surf, self.color + (alpha,), (self.size, self.size), self.size)
            surface.blit(particle_surf, (self.pos.x - self.size, self.pos.y - self.size))

# --- Функции для рисования и загрузки ресурсов ---
def draw_text_with_shadow(surface, text, font, color, pos, shadow_color=BLACK, offset=(2,2)):
    surface.blit(font.render(text, True, shadow_color), (pos[0]+offset[0], pos[1]+offset[1]))
    surface.blit(font.render(text, True, color), pos)

def draw_button(surface, text, font, center, padding=10):
    txt_surf = font.render(text, True, BUTTON_TEXT_COLOR)
    txt_rect = txt_surf.get_rect(center=center)
    btn_rect = txt_rect.inflate(padding*2, padding*2)
    pygame.draw.rect(surface, BUTTON_COLOR, btn_rect, border_radius=8)
    pygame.draw.rect(surface, GRID_COLOR, btn_rect, 2, border_radius=8)
    surface.blit(font.render(text, True, BLACK), txt_rect.move(2,2))
    surface.blit(txt_surf, txt_rect)

def load_sound(name):
    fullname = os.path.join('data', name)
    if not os.path.exists(fullname):
        print("Звуковой файл", fullname, "не найден")
        return None
    try:
        return pygame.mixer.Sound(fullname)
    except pygame.error:
        print("Невозможно загрузить звук:", name)
        return None

def load_image(name):
    fullname = os.path.join('data', name)
    if not os.path.exists(fullname):
        print("Изображение", fullname, "не найдено")
        return None
    try:
        return pygame.image.load(fullname).convert_alpha()
    except pygame.error:
        print("Невозможно загрузить изображение:", name)
        return None

def is_dead_end(maze, row, col):
    if maze[row][col] != 0:
        return False
    walls = 0
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        if maze[row+dr][col+dc] == 1:
            walls += 1
    return walls >= 3

# --- Основной класс игры ---
class MazeGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Лабиринт")
        self.clock = pygame.time.Clock()
        self.state = 'SPLASH'
        self.debug_mode = False
        self.splash_sound_played = False
        self.load_resources()
        self.font_large = pygame.font.SysFont("Arial", 48)
        self.font_medium = pygame.font.SysFont("Arial", 32)
        self.font_small = pygame.font.SysFont("Arial", 24)
        self.player_pos = list(START_POS)
        self.start_time = None
        self.elapsed_time = 0
        self.best_time = self.load_best_time()
        self.dead_end_triggered = False
        self.splash_start_time = pygame.time.get_ticks()
        self.maze_surface = pygame.Surface((len(MAZE_LAYOUT[0])*TILE_SIZE, len(MAZE_LAYOUT)*TILE_SIZE), pygame.SRCALPHA)
        self.update_count = 0
        self.particles = []  # Список для частиц

    def load_resources(self):
        self.player_image = load_image("player.png")
        if self.player_image is None:
            self.player_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.player_image.fill(BLUE)
        else:
            self.player_image = pygame.transform.scale(self.player_image, (TILE_SIZE, TILE_SIZE))
        self.exit_image = load_image("exit.png")
        if self.exit_image is None:
            self.exit_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.exit_image.fill(GREEN)
        else:
            self.exit_image = pygame.transform.scale(self.exit_image, (TILE_SIZE, TILE_SIZE))
        self.background_image = load_image("background.png")
        if self.background_image is None:
            self.background_image = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.background_image.fill(GRAY)
        else:
            self.background_image = pygame.transform.scale(self.background_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.move_sound = load_sound("move.wav")
        self.dead_end_sound = load_sound("dead_end.wav")
        self.splash_sound = load_sound("splash.wav")
        self.game_over_sound = load_sound("game_over.wav")
        music_file = os.path.join("data", "background_music.wav")
        if os.path.exists(music_file):
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print("Ошибка загрузки фоновой музыки:", e)

    def load_best_time(self):
        best = None
        if os.path.exists("record.txt"):
            try:
                with open("record.txt", "r") as f:
                    best = float(f.read().strip())
            except Exception as e:
                print("Ошибка чтения рекорда:", e)
        return best

    def save_best_time(self, time_taken):
        try:
            with open("record.txt", "w") as f:
                f.write(str(time_taken))
        except Exception as e:
            print("Ошибка сохранения рекорда:", e)

    def reset_game(self):
        self.player_pos = list(START_POS)
        self.start_time = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.dead_end_triggered = False

    def spawn_particles(self, pos, count, color, lifetime, size, speed_range):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0, speed_range)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            p = Particle(pos, velocity, lifetime, color, size)
            self.particles.append(p)

    def update_particles(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.lifetime > 0]

    def draw_particles(self, surface):
        for p in self.particles:
            p.draw(surface)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:
                    self.debug_mode = not self.debug_mode

            if self.state == 'SPLASH':
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self.state = 'MENU'
            elif self.state == 'MENU':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        self.reset_game()
                        self.start_time = pygame.time.get_ticks()
                        self.state = 'GAME'
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_r:
                        self.state = 'RECORD'
                    elif event.key == pygame.K_a:
                        self.state = 'ABOUT'
            elif self.state == 'GAME':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.move_player(-1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.move_player(1, 0)
                    elif event.key == pygame.K_LEFT:
                        self.move_player(0, -1)
                    elif event.key == pygame.K_RIGHT:
                        self.move_player(0, 1)
            elif self.state in ('GAME_OVER', 'RECORD', 'ABOUT'):
                if event.type == pygame.KEYDOWN:
                    self.state = 'MENU'

    def move_player(self, d_row, d_col):
        new_row = self.player_pos[0] + d_row
        new_col = self.player_pos[1] + d_col
        if new_row < 0 or new_row >= len(MAZE_LAYOUT) or new_col < 0 or new_col >= len(MAZE_LAYOUT[0]):
            return
        if MAZE_LAYOUT[new_row][new_col] == 1:
            return
        self.player_pos = [new_row, new_col]
        if self.move_sound:
            self.move_sound.play()

        # Расчет позиции игрока в пикселях (для эффекта частиц)
        maze_width = len(MAZE_LAYOUT[0]) * TILE_SIZE
        maze_height = len(MAZE_LAYOUT) * TILE_SIZE
        maze_x = (WINDOW_WIDTH - maze_width) // 2
        maze_y = (WINDOW_HEIGHT - maze_height) // 2
        player_pixel = (maze_x + self.player_pos[1] * TILE_SIZE + TILE_SIZE/2,
                        maze_y + self.player_pos[0] * TILE_SIZE + TILE_SIZE/2)
        # Эффект частиц при шаге
        self.spawn_particles(player_pixel, count=5, color=GRAY, lifetime=0.5, size=3, speed_range=30)

        if is_dead_end(MAZE_LAYOUT, new_row, new_col) and not self.dead_end_triggered:
            if self.dead_end_sound:
                self.dead_end_sound.play()
            self.dead_end_triggered = True
        else:
            self.dead_end_triggered = False

        if (new_row, new_col) == EXIT_POS:
            # Эффект частиц при достижении выхода
            self.spawn_particles(player_pixel, count=20, color=YELLOW, lifetime=1.0, size=4, speed_range=60)
            self.state = 'GAME_OVER'
            self.elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000.0
            if self.game_over_sound:
                self.game_over_sound.play()
            if self.best_time is None or self.elapsed_time < self.best_time:
                self.best_time = self.elapsed_time
                self.save_best_time(self.best_time)

    def update_game(self):
        self.elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000.0
        dt = self.clock.get_time() / 1000.0
        self.update_particles(dt)
        self.update_count += 1

    def draw_debug_info(self):
        debug = self.font_small.render(f"DEBUG | Состояние: {self.state} | Позиция: {self.player_pos} | Обновлений: {self.update_count}", True, RED)
        self.screen.blit(debug, (10, WINDOW_HEIGHT - 30))

    def draw_splash(self):
        self.screen.blit(self.background_image, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(DARK_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        title = "Добро пожаловать в Лабиринт!"
        instruction = "Нажмите любую клавишу для продолжения..."
        t_size = self.font_large.size(title)
        i_size = self.font_small.size(instruction)
        t_pos = ((WINDOW_WIDTH - t_size[0]) // 2, WINDOW_HEIGHT // 2 - 80)
        i_pos = ((WINDOW_WIDTH - i_size[0]) // 2, WINDOW_HEIGHT // 2 + 20)
        draw_text_with_shadow(self.screen, title, self.font_large, WHITE, t_pos)
        draw_text_with_shadow(self.screen, instruction, self.font_small, WHITE, i_pos)
        if not self.splash_sound_played and self.splash_sound:
            self.splash_sound.play()
            self.splash_sound_played = True

    def draw_menu(self):
        self.screen.blit(self.background_image, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(DARK_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        title = "Лабиринт"
        t_size = self.font_large.size(title)
        t_pos = ((WINDOW_WIDTH - t_size[0]) // 2, WINDOW_HEIGHT // 4)
        draw_text_with_shadow(self.screen, title, self.font_large, YELLOW, t_pos)
        draw_button(self.screen, "Нажмите S, чтобы начать", self.font_medium, (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 40))
        draw_button(self.screen, "Нажмите R, чтобы посмотреть рекорд", self.font_medium, (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 10))
        draw_button(self.screen, "Нажмите A, чтобы узнать об игре", self.font_medium, (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 60))
        draw_button(self.screen, "Нажмите Q, чтобы выйти", self.font_medium, (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 110))

    def draw_record(self):
        self.screen.blit(self.background_image, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(DARK_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        title = "Рекорд"
        t_size = self.font_large.size(title)
        t_pos = ((WINDOW_WIDTH - t_size[0]) // 2, WINDOW_HEIGHT // 4)
        draw_text_with_shadow(self.screen, title, self.font_large, WHITE, t_pos)
        rec_text = "Лучшее время: " + (f"{self.best_time:.2f} сек" if self.best_time is not None else "нет")
        r_size = self.font_medium.size(rec_text)
        r_pos = ((WINDOW_WIDTH - r_size[0]) // 2, WINDOW_HEIGHT // 2)
        draw_text_with_shadow(self.screen, rec_text, self.font_medium, YELLOW, r_pos)
        info = "Нажмите любую клавишу для возврата в меню."
        i_size = self.font_small.size(info)
        i_pos = ((WINDOW_WIDTH - i_size[0]) // 2, WINDOW_HEIGHT - 80)
        draw_text_with_shadow(self.screen, info, self.font_small, RED, i_pos)

    def draw_about(self):
        self.screen.blit(self.background_image, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(DARK_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        title = "Об игре"
        about_lines = [
            "Это простая игра-лабиринт, разработанная с использованием PyGame.",
            "Пробегите лабиринт как можно быстрее.",
            "Попробуйте побить свой личный рекорд!",
            "Наслаждайтесь игрой и весёлитесь!"
        ]
        t_size = self.font_large.size(title)
        draw_text_with_shadow(self.screen, title, self.font_large, WHITE, ((WINDOW_WIDTH-t_size[0])//2, 80))
        for idx, line in enumerate(about_lines):
            l_size = self.font_small.size(line)
            l_pos = ((WINDOW_WIDTH-l_size[0])//2, 150 + idx*40)
            draw_text_with_shadow(self.screen, line, self.font_small, YELLOW, l_pos)
        info = "Нажмите любую клавишу для возврата в меню."
        i_size = self.font_small.size(info)
        i_pos = ((WINDOW_WIDTH-i_size[0])//2, WINDOW_HEIGHT-80)
        draw_text_with_shadow(self.screen, info, self.font_small, RED, i_pos)

    def draw_maze(self):
        self.maze_surface.fill((0, 0, 0, 0))
        for row in range(len(MAZE_LAYOUT)):
            for col in range(len(MAZE_LAYOUT[0])):
                rect = pygame.Rect(col*TILE_SIZE, row*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if MAZE_LAYOUT[row][col] == 1:
                    pygame.draw.rect(self.maze_surface, WALL_COLOR, rect)
                pygame.draw.rect(self.maze_surface, GRID_COLOR, rect, 1)
        exit_rect = pygame.Rect(EXIT_POS[1]*TILE_SIZE, EXIT_POS[0]*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.maze_surface.blit(self.exit_image, exit_rect)

    def draw_game(self):
        self.screen.blit(self.background_image, (0, 0))
        self.draw_maze()
        maze_width = len(MAZE_LAYOUT[0]) * TILE_SIZE
        maze_height = len(MAZE_LAYOUT) * TILE_SIZE
        maze_x = (WINDOW_WIDTH - maze_width) // 2
        maze_y = (WINDOW_HEIGHT - maze_height) // 2
        self.screen.blit(self.maze_surface, (maze_x, maze_y))
        p_x = maze_x + self.player_pos[1] * TILE_SIZE
        p_y = maze_y + self.player_pos[0] * TILE_SIZE
        self.screen.blit(self.player_image, pygame.Rect(p_x, p_y, TILE_SIZE, TILE_SIZE))
        timer = f"Время: {self.elapsed_time:.2f} сек"
        draw_text_with_shadow(self.screen, timer, self.font_small, YELLOW, (10, 10))
        # Отрисовка частиц (эффект частиц поверх всего)
        self.draw_particles(self.screen)

    def draw_game_over(self):
        self.screen.blit(self.background_image, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(DARK_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        congrats = "Поздравляем!"
        your_time = f"Ваше время: {self.elapsed_time:.2f} сек"
        best_time = f"Лучшее время: {self.best_time:.2f} сек" if self.best_time is not None else "Лучшее время: N/A"
        restart = "Нажмите R для перезапуска или Q для выхода"
        c_size = self.font_large.size(congrats)
        y_size = self.font_medium.size(your_time)
        b_size = self.font_medium.size(best_time)
        r_size = self.font_small.size(restart)
        c_pos = ((WINDOW_WIDTH - c_size[0]) // 2, WINDOW_HEIGHT // 4)
        y_pos = ((WINDOW_WIDTH - y_size[0]) // 2, WINDOW_HEIGHT // 2 - 40)
        b_pos = ((WINDOW_WIDTH - b_size[0]) // 2, WINDOW_HEIGHT // 2 + 10)
        r_pos = ((WINDOW_WIDTH - r_size[0]) // 2, WINDOW_HEIGHT - 80)
        draw_text_with_shadow(self.screen, congrats, self.font_large, GREEN, c_pos)
        draw_text_with_shadow(self.screen, your_time, self.font_medium, WHITE, y_pos)
        draw_text_with_shadow(self.screen, best_time, self.font_medium, WHITE, b_pos)
        draw_text_with_shadow(self.screen, restart, self.font_small, WHITE, r_pos)

    def run(self):
        while True:
            self.handle_events()
            if self.state == 'SPLASH':
                self.draw_splash()
            elif self.state == 'MENU':
                self.draw_menu()
            elif self.state == 'GAME':
                self.update_game()
                self.draw_game()
            elif self.state == 'GAME_OVER':
                self.draw_game_over()
            elif self.state == 'RECORD':
                self.draw_record()
            elif self.state == 'ABOUT':
                self.draw_about()
            if self.debug_mode:
                self.draw_debug_info()
            pygame.display.flip()
            self.clock.tick(FPS)
            if self.update_count % 1000 == 0 and self.update_count != 0:
                print("Update count:", self.update_count)

    def draw_record(self):
        self.screen.blit(self.background_image, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(DARK_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        title = "Рекорд"
        t_size = self.font_large.size(title)
        t_pos = ((WINDOW_WIDTH - t_size[0]) // 2, WINDOW_HEIGHT // 4)
        draw_text_with_shadow(self.screen, title, self.font_large, WHITE, t_pos)
        rec = "Лучшее время: " + (f"{self.best_time:.2f} сек" if self.best_time is not None else "нет")
        r_size = self.font_medium.size(rec)
        r_pos = ((WINDOW_WIDTH - r_size[0]) // 2, WINDOW_HEIGHT // 2)
        draw_text_with_shadow(self.screen, rec, self.font_medium, YELLOW, r_pos)
        info = "Нажмите любую клавишу для возврата в меню."
        i_size = self.font_small.size(info)
        i_pos = ((WINDOW_WIDTH - i_size[0]) // 2, WINDOW_HEIGHT - 80)
        draw_text_with_shadow(self.screen, info, self.font_small, RED, i_pos)

    def draw_about(self):
        self.screen.blit(self.background_image, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(DARK_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        title = "Об игре"
        about_lines = [
            "Это простая игра-лабиринт, разработанная с использованием PyGame.",
            "Пробегите лабиринт как можно быстрее.",
            "Попробуйте побить свой личный рекорд!",
            "Наслаждайтесь игрой и весёлитесь!"
        ]
        t_size = self.font_large.size(title)
        draw_text_with_shadow(self.screen, title, self.font_large, WHITE, ((WINDOW_WIDTH-t_size[0])//2, 80))
        for idx, line in enumerate(about_lines):
            l_size = self.font_small.size(line)
            l_pos = ((WINDOW_WIDTH-l_size[0])//2, 150 + idx*40)
            draw_text_with_shadow(self.screen, line, self.font_small, YELLOW, l_pos)
        info = "Нажмите любую клавишу для возврата в меню."
        i_size = self.font_small.size(info)
        i_pos = ((WINDOW_WIDTH-i_size[0])//2, WINDOW_HEIGHT-80)
        draw_text_with_shadow(self.screen, info, self.font_small, RED, i_pos)

    def draw_particles(self, surface):
        for p in self.particles:
            p.draw(surface)

    def update_particles(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.lifetime > 0]

    def draw_game(self):
        self.screen.blit(self.background_image, (0, 0))
        self.draw_maze()
        maze_width = len(MAZE_LAYOUT[0]) * TILE_SIZE
        maze_height = len(MAZE_LAYOUT) * TILE_SIZE
        maze_x = (WINDOW_WIDTH - maze_width) // 2
        maze_y = (WINDOW_HEIGHT - maze_height) // 2
        self.screen.blit(self.maze_surface, (maze_x, maze_y))
        p_x = maze_x + self.player_pos[1] * TILE_SIZE
        p_y = maze_y + self.player_pos[0] * TILE_SIZE
        self.screen.blit(self.player_image, pygame.Rect(p_x, p_y, TILE_SIZE, TILE_SIZE))
        timer = f"Время: {self.elapsed_time:.2f} сек"
        draw_text_with_shadow(self.screen, timer, self.font_small, YELLOW, (10, 10))
        self.draw_particles(self.screen)

if __name__ == '__main__':
    game = MazeGame()
    game.run()

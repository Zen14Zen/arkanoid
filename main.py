# main.py — Арканоид, РГР
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame, math, random
from settings import *
from sprites  import Paddle, Ball, Brick, BonusDrop, Star, explode, Particle
from levels   import LEVELS


# ═══════════════════════════════════════════════════════
# Утилиты
# ═══════════════════════════════════════════════════════

def draw_text(surf, text, size, x, y,
              color=WHITE, anchor="center", bold=False):
    f   = pygame.font.SysFont("consolas", size, bold=bold)
    img = f.render(text, True, color)
    r   = img.get_rect()
    setattr(r, anchor, (x, y))
    surf.blit(img, r)


def load_hi():
    try:
        with open(SAVES_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_hi(score):
    try:
        with open(SAVES_FILE, "w") as f:
            f.write(str(score))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════
# Фон
# ═══════════════════════════════════════════════════════

class Background:
    def __init__(self):
        self.stars = [Star() for _ in range(100)]

    def draw(self, screen):
        screen.fill(BG)
        for s in self.stars:
            s.draw(screen)


# ═══════════════════════════════════════════════════════
# Менеджер рекордов
# ═══════════════════════════════════════════════════════

class ScoreManager:
    def __init__(self):
        self.score = 0
        self.hi    = load_hi()

    def add(self, pts):
        self.score += pts
        if self.score > self.hi:
            self.hi = self.score

    def reset(self):
        self.score = 0


# ═══════════════════════════════════════════════════════
# ГЛАВНОЕ МЕНЮ
# ═══════════════════════════════════════════════════════

class MenuState:
    def __init__(self, screen, sm=None):
        self.screen = screen
        self.bg     = Background()
        self.sm     = sm or ScoreManager()
        self._t     = 0

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return PlayState(self.screen, self.sm, level=1)
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
        return self

    def update(self):
        self._t += 1

    def draw(self):
        self.bg.draw(self.screen)

        draw_text(self.screen, "АРКАНОИД", 62,
                  WIDTH//2, 150, (80, 210, 255), bold=True)
        draw_text(self.screen, "РГР  ·  Python  ·  Pygame", 18,
                  WIDTH//2, 218, GRAY)

        if self._t % 70 < 46:
            draw_text(self.screen, "ENTER — начать игру", 22,
                      WIDTH//2, 320, SCORE_CLR)

        # Управление
        for i, line in enumerate([
            "← →  /  A D  —  платформа",
            "ПРОБЕЛ  —  запуск мяча",
            "ESC  —  пауза",
        ]):
            draw_text(self.screen, line, 17,
                      WIDTH//2, 400 + i*28, GRAY)

        if self.sm.hi > 0:
            draw_text(self.screen, f"РЕКОРД  {self.sm.hi:07d}", 20,
                      WIDTH//2, 530, (160, 160, 255))

        pygame.display.flip()


# ═══════════════════════════════════════════════════════
# ИГРОВОЙ ПРОЦЕСС
# ═══════════════════════════════════════════════════════

class PlayState:
    def __init__(self, screen, sm, level=1):
        self.screen = screen
        self.sm     = sm
        self.level  = level
        self.lives  = 3
        self.bg     = Background()

        # Группы
        self.bricks    = pygame.sprite.Group()
        self.drops     = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.balls     = pygame.sprite.Group()

        # Объекты
        self.paddle = Paddle()
        self._spawn_ball()
        self._build_level()

        # Флэш
        self._msg      = ""
        self._msg_t    = 0

        # Множитель мячей ожидающих после multi-бонуса
        self._multi_pending = False

    # ── Построить уровень ──────────────────────────────
    def _build_level(self):
        self.bricks.empty()
        idx    = min(self.level - 1, len(LEVELS) - 1)
        layout = LEVELS[idx]
        for row, line in enumerate(layout):
            for col, val in enumerate(line):
                if val == 0:
                    continue
                hp  = BRICK_HP[row] if val == 1 else 2
                clr = BRICK_COLORS[row]
                self.bricks.add(Brick(col, row, hp, clr))

    def _spawn_ball(self):
        b = Ball(self.paddle.rect.centerx, PAD_Y - BALL_R - 1)
        self.balls.add(b)
        return b

    # ── Обработка событий ─────────────────────────────
    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return PauseState(self.screen, self)
                if e.key == pygame.K_SPACE:
                    for b in self.balls:
                        if b.glued:
                            b.launch()
        return self

    # ── Обновление ────────────────────────────────────
    def update(self):
        self.paddle.update()
        self.particles.update()
        self.drops.update()

        for ball in list(self.balls):
            ball.update(self.paddle)
            if ball.glued:
                continue

            # Отскок от платформы
            if (ball.rect.bottom >= self.paddle.rect.top and
                    ball.rect.bottom <= self.paddle.rect.bottom + 8 and
                    ball.rect.centerx >= self.paddle.rect.left and
                    ball.rect.centerx <= self.paddle.rect.right and
                    ball.vy > 0):
                ball.bounce_paddle(self.paddle)
                if self.paddle.sticky:
                    ball.glued = True
                    self.paddle.sticky = False

            # Мяч потерян
            if ball.is_lost():
                ball.kill()

        # Все мячи потеряны
        if len(self.balls) == 0:
            self.lives -= 1
            if self.lives <= 0:
                save_hi(self.sm.hi)
                return GameOverState(self.screen, self.sm, self.level)
            self._spawn_ball()
            self._flash("ЖИЗНЬ ПОТЕРЯНА!", 90)

        # Мяч vs блоки
        for ball in list(self.balls):
            if ball.glued:
                continue
            hits = pygame.sprite.spritecollide(ball, self.bricks, False)
            for brick in hits:
                self._resolve_ball_brick(ball, brick)

        # Бонусы vs платформа
        caught = pygame.sprite.spritecollide(
            self.paddle, self.drops, True)
        for drop in caught:
            self._apply_bonus(drop.kind)

        # Уровень пройден
        if len(self.bricks) == 0:
            save_hi(self.sm.hi)
            if self.level >= MAX_LEVELS:
                return WinState(self.screen, self.sm)
            return LevelUpState(self.screen, self.sm,
                                self.level, self.lives)

        # Флэш
        if self._msg_t > 0:
            self._msg_t -= 1

        return self

    def _resolve_ball_brick(self, ball, brick):
        """Определяем с какой стороны удар и меняем направление"""
        br  = brick.rect
        bl  = ball.rect

        # Перекрытие по осям
        ox = min(bl.right, br.right) - max(bl.left,  br.left)
        oy = min(bl.bottom,br.bottom) - max(bl.top,   br.top)

        if ox <= 0 or oy <= 0:
            return

        if ox < oy:
            ball.vx *= -1
            # Раздвигаем
            if bl.centerx < br.centerx:
                ball._x = float(br.left  - BALL_R - 1)
            else:
                ball._x = float(br.right + BALL_R + 1)
        else:
            ball.vy *= -1
            if bl.centery < br.centery:
                ball._y = float(br.top   - BALL_R - 1)
            else:
                ball._y = float(br.bottom + BALL_R + 1)

        ball.rect.center = (int(ball._x), int(ball._y))

        destroyed = brick.hit()
        if destroyed:
            self.sm.add(brick.score)
            explode(self.particles,
                    brick.rect.centerx, brick.rect.centery,
                    brick.color)
            brick.kill()
            # Бонус?
            if random.random() < BONUS_CHANCE:
                kind = random.choice(["wide", "life", "slow", "multi"])
                self.drops.add(
                    BonusDrop(brick.rect.centerx,
                              brick.rect.centery, kind))

    def _apply_bonus(self, kind):
        if kind == "wide":
            self.paddle.widen()
            self._flash("ПЛАТФОРМА ШИРЕ!", 70)
        elif kind == "life":
            self.lives = min(5, self.lives + 1)
            self._flash("+ЖИЗНЬ!", 70)
        elif kind == "slow":
            for b in self.balls:
                spd = math.hypot(b.vx, b.vy)
                f   = max(0.6, (BALL_SPEED - 1) / spd)
                b.vx *= f; b.vy *= f
            self._flash("ЗАМЕДЛЕНИЕ!", 70)
        elif kind == "multi":
            new_balls = []
            for b in list(self.balls):
                if b.glued:
                    continue
                for angle in [-25, 25]:
                    nb   = Ball(b.rect.centerx, b.rect.centery)
                    spd  = math.hypot(b.vx, b.vy)
                    rad  = math.atan2(b.vy, b.vx) + math.radians(angle)
                    nb.vx    = spd * math.cos(rad)
                    nb.vy    = spd * math.sin(rad)
                    nb.glued = False
                    new_balls.append(nb)
            for nb in new_balls:
                self.balls.add(nb)
            self._flash("x3 МЯЧЕЙ!", 70)

    def _flash(self, msg, dur=80):
        self._msg   = msg
        self._msg_t = dur

    # ── Отрисовка ─────────────────────────────────────
    def draw(self):
        self.bg.draw(self.screen)

        # Блоки
        self.bricks.draw(self.screen)

        # Мячи (след + спрайт)
        for b in self.balls:
            b.draw_trail(self.screen)
        self.balls.draw(self.screen)

        # Платформа
        self.screen.blit(self.paddle.image, self.paddle.rect)

        # Бонусы
        self.drops.draw(self.screen)

        # Частицы
        self.particles.draw(self.screen)

        # HUD — верхняя полоска
        pygame.draw.rect(self.screen, (18, 18, 45),
                         (0, 0, WIDTH, 46))
        pygame.draw.line(self.screen, (60, 60, 120),
                         (0, 46), (WIDTH, 46), 1)

        draw_text(self.screen, f"СЧЁТ  {self.sm.score:07d}", 20,
                  12, 23, SCORE_CLR, "midleft")
        draw_text(self.screen, f"УРОВЕНЬ  {self.level} / {MAX_LEVELS}", 20,
                  WIDTH//2, 23, LEVEL_CLR)
        draw_text(self.screen, f"РЕКОРД  {self.sm.hi:07d}", 20,
                  WIDTH - 12, 23, (160, 160, 220), "midright")

        # Жизни — сердечки
        for i in range(self.lives):
            cx = 14 + i * 22
            cy = HEIGHT - 18
            # простое сердечко из кругов + треугольника
            pygame.draw.circle(self.screen, LIVES_CLR, (cx - 4, cy - 3), 5)
            pygame.draw.circle(self.screen, LIVES_CLR, (cx + 4, cy - 3), 5)
            pts = [(cx - 9, cy - 1), (cx + 9, cy - 1), (cx, cy + 9)]
            pygame.draw.polygon(self.screen, LIVES_CLR, pts)

        # Прогресс уровня
        total   = sum(1 for b in self.bricks)   # текущих блоков
        # Нам нужно исходное количество — храним в _total_bricks
        if not hasattr(self, '_total_bricks'):
            self._total_bricks = max(1, total)
        destroyed = self._total_bricks - total
        prog      = min(1.0, destroyed / self._total_bricks)
        bw, bh    = 180, 8
        bx        = WIDTH//2 - bw//2
        by        = HEIGHT - 14
        pygame.draw.rect(self.screen, (40, 40, 70),
                         (bx, by, bw, bh), border_radius=3)
        pygame.draw.rect(self.screen, (80, 200, 100),
                         (bx, by, int(bw * prog), bh), border_radius=3)

        # Широкий таймер
        if self.paddle.wide_timer > 0:
            draw_text(self.screen, "WIDE", 14,
                      WIDTH - 55, HEIGHT - 18, (80, 200, 255))

        # Флэш
        if self._msg_t > 0:
            draw_text(self.screen, self._msg, 30,
                      WIDTH//2, HEIGHT//2 - 30, SCORE_CLR)

        pygame.display.flip()


# ═══════════════════════════════════════════════════════
# ПАУЗА
# ═══════════════════════════════════════════════════════

class PauseState:
    def __init__(self, screen, playing):
        self.screen  = screen
        self.playing = playing

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return self.playing
                if e.key == pygame.K_q:
                    save_hi(self.playing.sm.hi)
                    return MenuState(self.screen, self.playing.sm)
        return self

    def update(self): pass

    def draw(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        draw_text(self.screen, "ПАУЗА", 54, WIDTH//2, HEIGHT//2 - 60,
                  (80, 210, 255), bold=True)
        draw_text(self.screen, "ESC — продолжить", 22,
                  WIDTH//2, HEIGHT//2 + 16, WHITE)
        draw_text(self.screen, "Q — в главное меню", 22,
                  WIDTH//2, HEIGHT//2 + 50, GRAY)
        pygame.display.flip()


# ═══════════════════════════════════════════════════════
# ПЕРЕХОД УРОВНЯ
# ═══════════════════════════════════════════════════════

class LevelUpState:
    def __init__(self, screen, sm, level, lives):
        self.screen = screen
        self.sm     = sm
        self.level  = level
        self.lives  = lives
        self.bg     = Background()
        self._t     = 0

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    ps = PlayState(self.screen, self.sm, self.level + 1)
                    ps.lives = self.lives
                    return ps
        return self

    def update(self):
        self._t += 1

    def draw(self):
        self.bg.draw(self.screen)
        draw_text(self.screen, f"УРОВЕНЬ {self.level} ПРОЙДЕН!", 44,
                  WIDTH//2, 200, (80, 255, 140), bold=True)
        draw_text(self.screen, f"СЧЁТ:  {self.sm.score:07d}", 28,
                  WIDTH//2, 290, SCORE_CLR)
        draw_text(self.screen, f"Следующий: УРОВЕНЬ {self.level + 1}", 22,
                  WIDTH//2, 345, LEVEL_CLR)
        if self._t % 70 < 46:
            draw_text(self.screen, "ENTER — продолжить", 22,
                      WIDTH//2, 430, WHITE)
        pygame.display.flip()


# ═══════════════════════════════════════════════════════
# GAME OVER
# ═══════════════════════════════════════════════════════

class GameOverState:
    def __init__(self, screen, sm, level):
        self.screen = screen
        self.sm     = sm
        self.level  = level
        self.bg     = Background()
        self._t     = 0

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    new_sm = ScoreManager()
                    new_sm.hi = self.sm.hi
                    return PlayState(self.screen, new_sm, level=1)
                if e.key == pygame.K_ESCAPE:
                    return MenuState(self.screen, self.sm)
        return self

    def update(self): self._t += 1

    def draw(self):
        self.bg.draw(self.screen)
        draw_text(self.screen, "ИГРА ОКОНЧЕНА", 52,
                  WIDTH//2, 180, (255, 60, 60), bold=True)
        draw_text(self.screen, f"СЧЁТ:  {self.sm.score:07d}", 30,
                  WIDTH//2, 278, SCORE_CLR)
        draw_text(self.screen, f"РЕКОРД:  {self.sm.hi:07d}", 22,
                  WIDTH//2, 326, (160, 160, 255))
        draw_text(self.screen, f"Достигнут уровень {self.level}", 20,
                  WIDTH//2, 372, GRAY)
        if self._t % 70 < 46:
            draw_text(self.screen, "ENTER — заново", 22,
                      WIDTH//2, 450, WHITE)
        draw_text(self.screen, "ESC — главное меню", 18,
                  WIDTH//2, 484, GRAY)
        pygame.display.flip()


# ═══════════════════════════════════════════════════════
# ПОБЕДА
# ═══════════════════════════════════════════════════════

class WinState:
    def __init__(self, screen, sm):
        self.screen = screen
        self.sm     = sm
        self.bg     = Background()
        self._t     = 0

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                return MenuState(self.screen, self.sm)
        return self

    def update(self): self._t += 1

    def draw(self):
        self.bg.draw(self.screen)
        draw_text(self.screen, "ПОБЕДА!", 64,
                  WIDTH//2, 170, (80, 255, 140), bold=True)
        draw_text(self.screen, "Все уровни пройдены!", 26,
                  WIDTH//2, 265, WHITE)
        draw_text(self.screen, f"ИТОГ:  {self.sm.score:07d}", 30,
                  WIDTH//2, 320, SCORE_CLR)
        draw_text(self.screen, f"РЕКОРД:  {self.sm.hi:07d}", 22,
                  WIDTH//2, 368, (160, 160, 255))
        if self._t % 70 < 46:
            draw_text(self.screen, "Нажми любую клавишу", 20,
                      WIDTH//2, 460, GRAY)
        pygame.display.flip()


# ═══════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    sm    = ScoreManager()
    state = MenuState(screen, sm)

    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                save_hi(sm.hi)
                pygame.quit(); sys.exit()

        new = state.handle(events)
        if new is not state:
            state = new
        else:
            result = state.update()
            if result is not None:
                state = result
            state.draw()

        clock.tick(FPS)


if __name__ == "__main__":
    main()

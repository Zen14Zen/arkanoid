# sprites.py
import pygame, math, random
from settings import *


# ── Фоновые звёзды ───────────────────────────────────────────
class Star:
    def __init__(self):
        self.x     = random.randint(0, WIDTH)
        self.y     = random.randint(0, HEIGHT)
        self.r     = random.randint(1, 2)
        self.alpha = random.randint(60, 200)

    def draw(self, screen):
        pygame.draw.circle(screen, (self.alpha,)*3,
                           (self.x, self.y), self.r)


# ── Частицы ──────────────────────────────────────────────────
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (3, 3), 3)
        self.rect  = self.image.get_rect(center=(x, y))
        a          = random.uniform(0, math.tau)
        sp         = random.uniform(1.5, 5)
        self.vx    = math.cos(a) * sp
        self.vy    = math.sin(a) * sp
        self.life  = random.randint(15, 30)
        self._x    = float(x)
        self._y    = float(y)

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill(); return
        self._x += self.vx
        self._y += self.vy
        self.vy += 0.15
        self.rect.center = (int(self._x), int(self._y))
        self.image.set_alpha(int(255 * self.life / 30))


def explode(group, x, y, color, n=14):
    for _ in range(n):
        group.add(Particle(x, y, color))


# ── Платформа ────────────────────────────────────────────────
class Paddle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self._build(PAD_W)
        self.rect = self.image.get_rect(centerx=WIDTH // 2, y=PAD_Y)
        self._x   = float(self.rect.x)
        self.sticky   = False   # бонус: мяч прилипает
        self.wide_timer = 0     # кадров расширения

    def _build(self, w):
        self.image = pygame.Surface((w, PAD_H), pygame.SRCALPHA)
        body = pygame.Rect(0, 0, w, PAD_H)
        pygame.draw.rect(self.image, PAD_CLR, body, border_radius=7)
        pygame.draw.rect(self.image, PAD_EDGE_CLR, body, 2, border_radius=7)
        # Блик
        pygame.draw.rect(self.image, (200, 230, 255),
                         (4, 2, w - 8, 4), border_radius=3)

    def update(self):
        if self.wide_timer > 0:
            self.wide_timer -= 1
            if self.wide_timer == 0:
                cx = self.rect.centerx
                self._build(PAD_W)
                self.rect = self.image.get_rect(centerx=cx, y=PAD_Y)
                self._x   = float(self.rect.x)

        keys = pygame.key.get_pressed()
        dx   = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= PAD_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += PAD_SPEED
        self._x = max(0, min(WIDTH - self.rect.width, self._x + dx))
        self.rect.x = int(self._x)

    def widen(self, duration=400):
        cx = self.rect.centerx
        self._build(PAD_W + 50)
        self.rect = self.image.get_rect(centerx=cx, y=PAD_Y)
        self._x   = float(self.rect.x)
        self.wide_timer = duration


# ── Мяч ─────────────────────────────────────────────────────
class Ball(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        d          = BALL_R * 2
        self.image = pygame.Surface((d, d), pygame.SRCALPHA)
        # Тело
        pygame.draw.circle(self.image, BALL_CLR, (BALL_R, BALL_R), BALL_R)
        # Блик
        pygame.draw.circle(self.image, (255, 255, 200),
                           (BALL_R - 3, BALL_R - 3), BALL_R // 3)
        self.rect  = self.image.get_rect(center=(x, y))
        angle      = random.uniform(-60, 60)   # градусов от вертикали
        self.vx    = BALL_SPEED * math.sin(math.radians(angle))
        self.vy    = -BALL_SPEED
        self._x    = float(x)
        self._y    = float(y)
        self.glued = True   # ждём старта (пробел)
        self.trail = []     # след

    def launch(self):
        self.glued = False

    def update(self, paddle=None):
        if self.glued and paddle:
            self._x = float(paddle.rect.centerx)
            self._y = float(PAD_Y - BALL_R - 1)
            self.rect.center = (int(self._x), int(self._y))
            return

        # Сохраняем след
        self.trail.append((int(self._x), int(self._y)))
        if len(self.trail) > 8:
            self.trail.pop(0)

        self._x += self.vx
        self._y += self.vy

        # Стены
        if self._x - BALL_R < 0:
            self._x = float(BALL_R)
            self.vx = abs(self.vx)
        if self._x + BALL_R > WIDTH:
            self._x = float(WIDTH - BALL_R)
            self.vx = -abs(self.vx)
        if self._y - BALL_R < 0:
            self._y = float(BALL_R)
            self.vy = abs(self.vy)

        self.rect.center = (int(self._x), int(self._y))

    def draw_trail(self, screen):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(80 * i / len(self.trail)) if self.trail else 0
            r     = max(1, BALL_R - (len(self.trail) - i))
            s     = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*BALL_CLR, alpha), (r, r), r)
            screen.blit(s, (tx - r, ty - r))

    def bounce_paddle(self, paddle):
        """Угол отскока зависит от точки попадания"""
        rel = (self._x - paddle.rect.centerx) / (paddle.rect.width / 2)
        rel = max(-0.95, min(0.95, rel))
        angle = rel * 65   # от -65° до +65°
        speed = min(BALL_MAX, math.hypot(self.vx, self.vy) + 0.1)
        self.vx = speed * math.sin(math.radians(angle))
        self.vy = -abs(speed * math.cos(math.radians(angle)))
        self._y = float(paddle.rect.top - BALL_R - 1)

    def is_lost(self):
        return self._y - BALL_R > HEIGHT + 20


# ── Блок ─────────────────────────────────────────────────────
class Brick(pygame.sprite.Sprite):
    def __init__(self, col, row, hp, color):
        super().__init__()
        self.hp       = hp
        self.max_hp   = hp
        self.color    = color
        self.score    = BRICK_SCORES[row]
        self._make_image()
        x = BRICK_PAD_X + col * (BRICK_W + BRICK_GAP)
        y = BRICK_PAD_Y + row * (BRICK_H + BRICK_GAP)
        self.rect = self.image.get_rect(topleft=(x, y))

    def _make_image(self):
        self.image = pygame.Surface((BRICK_W, BRICK_H), pygame.SRCALPHA)
        # Затемнение если повреждён
        alpha = 255 if self.hp == self.max_hp else 160
        clr   = (*self.color[:3], alpha)
        pygame.draw.rect(self.image, clr,
                         (0, 0, BRICK_W, BRICK_H), border_radius=4)
        # Блик
        if self.hp == self.max_hp:
            light = tuple(min(255, c + 80) for c in self.color[:3])
            pygame.draw.rect(self.image, (*light, 140),
                             (3, 2, BRICK_W - 6, 5), border_radius=2)
        # Трещина при hp=1 и max=2
        if self.max_hp == 2 and self.hp == 1:
            pygame.draw.line(self.image, (0, 0, 0, 180),
                             (BRICK_W//3, 2), (BRICK_W//2, BRICK_H-2), 2)
            pygame.draw.line(self.image, (0, 0, 0, 180),
                             (BRICK_W//2, BRICK_H//2),
                             (BRICK_W*2//3, BRICK_H-2), 2)
        # Рамка
        pygame.draw.rect(self.image, (0, 0, 0, 80),
                         (0, 0, BRICK_W, BRICK_H), 1, border_radius=4)

    def hit(self):
        self.hp -= 1
        self._make_image()
        return self.hp <= 0   # True = уничтожен


# ── Бонус (падающий) ─────────────────────────────────────────
class BonusDrop(pygame.sprite.Sprite):
    # kind: "wide" "life" "slow" "multi"
    COLORS = {"wide": (80, 200, 255),
               "life": (255, 80, 120),
               "slow": (100, 255, 160),
               "multi":(255, 200, 50)}
    LABELS = {"wide": "WIDE", "life": "+❤",
               "slow": "SLOW", "multi":"x3"}

    def __init__(self, x, y, kind):
        super().__init__()
        self.kind  = kind
        clr        = self.COLORS[kind]
        w, h       = 52, 22
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, clr, (0, 0, w, h), border_radius=6)
        pygame.draw.rect(self.image, WHITE, (0, 0, w, h), 1, border_radius=6)
        font = pygame.font.SysFont("consolas", 14, bold=True)
        txt  = font.render(self.LABELS[kind], True, (20, 20, 40))
        self.image.blit(txt, txt.get_rect(center=(w//2, h//2)))
        self.rect  = self.image.get_rect(center=(x, y))
        self._y    = float(y)

    def update(self):
        self._y   += BONUS_SPEED
        self.rect.y = int(self._y)
        if self.rect.top > HEIGHT + 10:
            self.kill()

# settings.py
WIDTH, HEIGHT = 800, 650
FPS           = 60
TITLE         = "Арканоид — РГР"

# Цвета
BG            = (8,   8,  22)
WHITE         = (255, 255, 255)
GRAY          = (120, 120, 150)
SCORE_CLR     = (255, 230,  50)
LIVES_CLR     = (255,  80,  80)
LEVEL_CLR     = (80,  210, 255)

# Платформа
PAD_W         = 110
PAD_H         = 14
PAD_Y         = HEIGHT - 55
PAD_SPEED     = 7
PAD_CLR       = (80,  180, 255)
PAD_EDGE_CLR  = (180, 230, 255)

# Мяч
BALL_R        = 9
BALL_SPEED    = 5.5
BALL_MAX      = 10.0
BALL_CLR      = (255, 240, 100)

# Блоки
BRICK_COLS    = 10
BRICK_ROWS    = 6
BRICK_W       = 68
BRICK_H       = 24
BRICK_PAD_X   = 16
BRICK_PAD_Y   = 70
BRICK_GAP     = 4

# Очки за блок (по рядам, сверху)
BRICK_SCORES  = [70, 60, 50, 40, 30, 20]

# Цвета блоков по рядам
BRICK_COLORS  = [
    (255,  60,  80),   # красный
    (255, 130,  30),   # оранжевый
    (255, 220,  30),   # жёлтый
    ( 60, 200,  80),   # зелёный
    ( 40, 160, 255),   # синий
    (160,  80, 255),   # фиолетовый
]

# Прочность (хитов) по рядам (1 или 2)
BRICK_HP      = [2, 2, 1, 1, 1, 1]

# Бонусы
BONUS_CHANCE  = 0.18   # вероятность выпадения
BONUS_SPEED   = 3.0

# Уровни
MAX_LEVELS    = 5
SAVES_FILE    = "highscore.txt"

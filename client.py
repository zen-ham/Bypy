import pygame
import random
import math

pygame.init()
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PvP Game with Lobby")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

clock = pygame.time.Clock()
FPS = 60

# Player and Game variables
player_width, player_height = 50, 50
player_speed = 5
jump_strength = 15
gravity = 1
max_players = 8
player_hp = 100
wrecking_ball_radius = 30
chain_length = 150  # Increased chain length
wrecking_ball_mass = 0.5  # Easier to throw (lighter)
wrecking_ball_friction = 0.95  # Friction to slow down the wrecking ball

# Map and PvP settings
pvp_enabled = False
current_map = 'lobby'
yellow_block = pygame.Rect(WIDTH - 150, HEIGHT - 100, 100, 50)

# Function to generate random platforms
def generate_random_map():
    platforms = []
    for _ in range(random.randint(3, 6)):  # Random number of platforms
        width = random.randint(200, 400)
        height = 20
        x = random.randint(0, WIDTH - width)
        y = random.randint(HEIGHT // 3, HEIGHT - 100)
        platforms.append(pygame.Rect(x, y, width, height))
    return platforms

lobby_platforms = [
    pygame.Rect(200, HEIGHT - 100, 400, 20),
]
pvp_map_platforms = generate_random_map()  # Generate initial random map

current_player_index = 0

class Player:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        self.hp = player_hp
        self.rect = pygame.Rect(self.x, self.y, player_width, player_height)
        self.wrecking_ball_pos = (self.x, self.y + chain_length)
        self.wrecking_ball_vel = [0, 0]
        self.angle = 0

    def handle_input(self, keys):
        if keys[pygame.K_a]:
            self.vel_x = -player_speed
        elif keys[pygame.K_d]:
            self.vel_x = player_speed
        else:
            self.vel_x = 0

        if ((keys[pygame.K_SPACE]) or (keys[pygame.K_w])) and not self.is_jumping:
            self.vel_y = -jump_strength
            self.is_jumping = True

    def update(self, is_active):
        if not is_active:
            self.vel_x = 0
        self.vel_y += gravity
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.topleft = (self.x, self.y)

        self.update_wrecking_ball()
        self.handle_collisions()

        if self.y + player_height > HEIGHT:
            self.y = HEIGHT - player_height
            self.vel_y = 0
            self.is_jumping = False

    def update_wrecking_ball(self):
        # Wrecking ball physics based on player's position and momentum
        px, py = self.rect.center
        wx, wy = self.wrecking_ball_pos

        # Calculate the distance and direction between the player and the wrecking ball
        dx = wx - px
        dy = wy - py
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 0.01  # Avoid division by zero

        # Force to keep the ball at chain length
        force = (dist - chain_length) * 0.05
        angle = math.atan2(dy, dx)

        # Update wrecking ball position
        self.wrecking_ball_vel[0] += -math.cos(angle) * force * wrecking_ball_mass
        self.wrecking_ball_vel[1] += -math.sin(angle) * force * wrecking_ball_mass + gravity

        # Slow down wrecking ball if player is not moving
        if self.vel_x == 0 and self.vel_y == 0:
            self.wrecking_ball_vel[0] *= wrecking_ball_friction
            self.wrecking_ball_vel[1] *= wrecking_ball_friction

        wx += self.wrecking_ball_vel[0]
        wy += self.wrecking_ball_vel[1]

        # Update wrecking ball position
        self.wrecking_ball_pos = (wx, wy)

    def handle_collisions(self):
        platforms = lobby_platforms if current_map == 'lobby' else pvp_map_platforms
        on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform) and self.vel_y > 0:
                if self.rect.bottom <= platform.top + self.vel_y:
                    self.y = platform.y - player_height
                    self.vel_y = 0
                    self.is_jumping = False
                    on_ground = True
        if not on_ground:
            self.is_jumping = True

    def draw(self):
        # Draw player
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, player_width, 5))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, player_width * (self.hp / player_hp), 5))
        pygame.draw.line(screen, BLACK, self.rect.center, self.wrecking_ball_pos, 5)
        pygame.draw.circle(screen, BLACK, (int(self.wrecking_ball_pos[0]), int(self.wrecking_ball_pos[1])), wrecking_ball_radius)

def switch_player():
    global current_player_index
    if players:
        current_player_index = (current_player_index + 1) % len(players)

def add_player():
    if len(players) < max_players:
        new_x = 100 + len(players) * 100
        new_player = Player(new_x, HEIGHT - 150, [BLUE, RED, GREEN, BLACK][len(players) % 4])
        players.append(new_player)

def handle_pvp_collisions():
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            if wrecking_ball_hits_head(players[i], players[j]):
                players[j].hp -= 1

def wrecking_ball_hits_head(player, target):
    wx, wy = player.wrecking_ball_pos
    return target.rect.collidepoint(wx, wy)

def switch_to_pvp():
    global pvp_enabled, current_map
    pvp_enabled = True
    current_map = 'pvp_map'
    global pvp_map_platforms
    pvp_map_platforms = generate_random_map()

def check_for_pvp_start():
    global yellow_block
    if yellow_block and any(player.rect.colliderect(yellow_block) for player in players):
        yellow_block = None
        switch_to_pvp()

players = []
yellow_block_exists = True

running = True
while running:
    screen.fill(WHITE)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                switch_player()
            if event.key == pygame.K_i:
                add_player()
    keys = pygame.key.get_pressed()
    for i, player in enumerate(players):
        if i == current_player_index:
            player.handle_input(keys)
        player.update(is_active=(i == current_player_index))
    if yellow_block_exists:
        check_for_pvp_start()
    if pvp_enabled:
        handle_pvp_collisions()
    for player in players:
        player.draw()
    platforms = lobby_platforms if current_map == 'lobby' else pvp_map_platforms
    for platform in platforms:
        pygame.draw.rect(screen, BLACK, platform)
    if yellow_block:
        pygame.draw.rect(screen, YELLOW, yellow_block)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

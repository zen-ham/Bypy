import pygame
import random

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Swap Game with Gravity and Inactive Player Stopping")

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# Player settings
player_width, player_height = 50, 50
player_speed = 5
jump_strength = -15
gravity = 1
max_players = 8
player_hp = 100
pvp_enabled = False

# Initial platforms (for the lobby)
lobby_platforms = [
    pygame.Rect(200, HEIGHT - 100, 600, 20),
    pygame.Rect(WIDTH // 2 - 200, HEIGHT - 200, 400, 20)
]

# PvP map platforms
pvp_map_platforms = [
    pygame.Rect(50, HEIGHT - 200, 500, 20),
    pygame.Rect(600, HEIGHT - 300, 500, 20),
    pygame.Rect(400, HEIGHT - 400, 400, 20)
]

# Current game state
current_player_index = 0
current_map = 'lobby'
yellow_block = pygame.Rect(WIDTH - 150, HEIGHT - 100, 100, 50)

# Define a function to generate new maps
def generate_random_map():
    global lobby_platforms, pvp_map_platforms
    num_platforms = random.randint(2, 5)  # Random number of platforms
    min_width = 200
    max_width = 600
    min_height = 20
    max_height = 40

    # Generate new platforms for the lobby
    lobby_platforms = []
    for _ in range(num_platforms):
        x = random.randint(0, WIDTH - max_width)
        y = random.randint(HEIGHT // 2, HEIGHT - min_height)
        width = random.randint(min_width, max_width)
        height = min_height
        lobby_platforms.append(pygame.Rect(x, y, width, height))

    # Generate new platforms for PvP map
    pvp_map_platforms = []
    for _ in range(num_platforms):
        x = random.randint(0, WIDTH - max_width)
        y = random.randint(HEIGHT // 2, HEIGHT - min_height)
        width = random.randint(min_width, max_width)
        height = min_height
        pvp_map_platforms.append(pygame.Rect(x, y, width, height))

# Player class
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

    def handle_input(self, keys):
        """Handle input for the current player only."""
        if keys[pygame.K_a]:
            self.vel_x = -player_speed
        elif keys[pygame.K_d]:
            self.vel_x = player_speed
        else:
            self.vel_x = 0

        if keys[pygame.K_w] and not self.is_jumping:
            self.vel_y = jump_strength
            self.is_jumping = True

    def update(self, is_active):
        """Apply gravity and update position. Stop horizontal movement if not active."""
        if not is_active:
            self.vel_x = 0

        self.vel_y += gravity
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.topleft = (self.x, self.y)
        self.handle_collisions()

        # Prevent falling below the screen
        if self.y + player_height > HEIGHT:
            self.y = HEIGHT - player_height
            self.vel_y = 0
            self.is_jumping = False

    def handle_collisions(self):
        if current_map == 'lobby':
            platforms = lobby_platforms
        else:
            platforms = pvp_map_platforms

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
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, player_width, 5))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, player_width * (self.hp / player_hp), 5))

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
            if players[i].rect.colliderect(players[j].rect):
                players[i].hp -= 1
                players[j].hp -= 1

def switch_to_pvp():
    global pvp_enabled, current_map
    pvp_enabled = True
    current_map = 'pvp_map'

def check_for_pvp_start():
    for player in players:
        if player.rect.colliderect(yellow_block):
            switch_to_pvp()

def remove_dead_players():
    global players, current_player_index
    players = [player for player in players if player.hp > 0]
    if not players:
        generate_random_map()  # Generate new map when all players are dead
        pvp_enabled = False  # Disable PvP mode after map change
        current_map = 'lobby'  # Reset map to lobby
    if current_player_index >= len(players):
        current_player_index = 0

players = []

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

    if current_map == 'lobby':
        check_for_pvp_start()
    if pvp_enabled:
        handle_pvp_collisions()

    remove_dead_players()

    for player in players:
        player.draw()

    if current_map == 'lobby':
        for platform in lobby_platforms:
            pygame.draw.rect(screen, BLACK, platform)
        pygame.draw.rect(screen, YELLOW, yellow_block)
    elif current_map == 'pvp_map':
        for platform in pvp_map_platforms:
            pygame.draw.rect(screen, BLACK, platform)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

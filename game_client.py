import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import math, sys, pygame, random, pyperclip, threading, zhmiscellany, time
from ice_manager import MultiPeerManager


def scale_value(value, base_value, actual_value):
    return value * (actual_value / base_value)


def reverse_scale_value(value, base_value, actual_value):
    return value / (actual_value / base_value)


def generate_random_map():
    platforms = []
    for _ in range(random.randint(3, 6)):
        base_width = random.randint(200, 400)
        base_height = 20
        base_x = random.randint(0, BASE_WIDTH - base_width)
        base_y = random.randint(BASE_HEIGHT // 3, BASE_HEIGHT - 100)
        width = scale_value(base_width, BASE_WIDTH, WIDTH)
        height = scale_value(base_height, BASE_HEIGHT, HEIGHT)
        x = scale_value(base_x, BASE_WIDTH, WIDTH)
        y = scale_value(base_y, BASE_HEIGHT, HEIGHT)
        platforms.append(pygame.Rect(x, y, width, height))
    return platforms


def randomcolor(color):
    random_object = random.Random()
    random_object.seed(color*5)
    primary_color = random_object.choice([0, 1, 2])
    secondary_color = random_object.choice([i for i in range(3) if i != primary_color])
    rgb = [0, 0, 0]
    rgb[primary_color] = random_object.randint(200, 255)
    rgb[secondary_color] = random_object.randint(0, 55)
    rgb[3 - primary_color - secondary_color] = random_object.randint(50, 200)
    return tuple(rgb)


class Player:
    def __init__(self, x, y, color, player_id):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = True
        self.hp = player_hp
        self.rect = pygame.Rect(self.x, self.y, player_width, player_height)
        #self.wrecking_ball_pos = (self.x, self.y + chain_length)
        #self.wrecking_ball_vel = [0, 0]
        self.angle = 0
        self.player_id = player_id

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

    def update(self):
        if self.is_jumping:
            self.vel_y += gravity
            self.x += self.vel_x
            self.y += self.vel_y
            self.rect.topleft = (self.x, self.y)

        #self.update_wrecking_ball()
        self.handle_collisions()
        if self.y + player_height > HEIGHT:
            self.y = HEIGHT - player_height
            self.vel_y = 0
            self.is_jumping = False

    def update_collider(self):
        self.rect.topleft = (self.x, self.y)

    def update_wrecking_ball(self):
        px, py = self.rect.center
        wx, wy = self.wrecking_ball_pos
        dx = wx - px
        dy = wy - py
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 0.01
        force = (dist - chain_length) * 0.05
        angle = math.atan2(dy, dx)
        self.wrecking_ball_vel[0] += -math.cos(angle) * force * wrecking_ball_mass
        self.wrecking_ball_vel[1] += -math.sin(angle) * force * wrecking_ball_mass + gravity
        if self.vel_x == 0 and self.vel_y == 0:
            self.wrecking_ball_vel[0] *= wrecking_ball_friction
            self.wrecking_ball_vel[1] *= wrecking_ball_friction
        wx += self.wrecking_ball_vel[0]
        wy += self.wrecking_ball_vel[1]
        self.wrecking_ball_pos = (wx, wy)

    def handle_collisions(self):
        #self.update_collider()
        platforms = lobby_platforms if current_map == 'lobby' else pvp_map_platforms
        on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform) and self.vel_y >= 0:
                if self.rect.bottom <= platform.top + self.vel_y:
                    self.y = platform.y - player_height
                    self.vel_y = 0
                    self.is_jumping = False
                    on_ground = True
                    self.update_collider()
                    break
                    #while not self.rect.colliderect(platform):
                    #    self.y += 0.1
                    #    self.update_collider()
        if not on_ground:
            self.is_jumping = True
        #print(on_ground)


    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, player_width, 5))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, player_width * (self.hp / player_hp), 5))
        #pygame.draw.line(screen, BLACK, self.rect.center, self.wrecking_ball_pos, 5)
        #pygame.draw.circle(screen, BLACK, (int(self.wrecking_ball_pos[0]), int(self.wrecking_ball_pos[1])), wrecking_ball_radius)

def add_player(player_id):
    new_x = scale_value(100 + len(players) * 100, BASE_WIDTH, WIDTH)

    new_player = Player(new_x, scale_value(HEIGHT - 150, BASE_HEIGHT, HEIGHT), randomcolor(player_id), player_id)
    players[player_id] = new_player

#def handle_pvp_collisions():
#    for i in range(len(players)):
#        for j in range(i + 1, len(players)):
#            if wrecking_ball_hits_head(players[i], players[j]):
#                players[j].hp -= 1

#def wrecking_ball_hits_head(player, target):
#    wx, wy = player.wrecking_ball_pos
#    return target.rect.collidepoint(wx, wy)


def switch_to_pvp():
    global pvp_enabled, current_map, pvp_map_platforms
    pvp_enabled = True
    current_map = 'pvp_map'
    pvp_map_platforms = generate_random_map()


def check_for_pvp_start():
    global yellow_block
    if yellow_block and any(player.rect.colliderect(yellow_block) for player in players.values()):
        yellow_block = None
        switch_to_pvp()


def display_player_coords():
    y_offset = 0
    for player_id in players:
        #print(player_coords)
        player = players[player_id]
        text = f"Player {player_id}: ({player.x:.0f}, {player.y:.0f})"
        screen.blit(font.render(text, True, player.color), (10, 10 + y_offset))
        y_offset += 30


class TextBox:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (255, 255, 255)
        self.active = False
        self.FONT = pygame.font.Font(None, 36)
        self.code = ''
        self.txt_surface = self.FONT.render(self.code, True, self.color)
        self.max_length = 9
        self.text = ''

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = (0, 255, 0) if self.active else (255, 255, 255)

        if event.type == pygame.KEYDOWN:
            if self.active:
                if (event.key == pygame.K_RETURN):
                    self.code = self.text
                    print(f"Room code entered: {self.text}")
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    pasted_text = pyperclip.paste()
                    allowed_text = pasted_text[:self.max_length - len(self.text)]
                    self.text += allowed_text
                elif len(self.text) < self.max_length:
                    self.text += event.unicode
                self.text = self.text[:self.max_length]
                self.code = self.text
                self.txt_surface = self.FONT.render(self.text, True, self.color)
        return False

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

class Button:
    def __init__(self, text, x, y, w, h, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (0, 255, 0)
        code = text
        self.callback = callback
        self.FONT = pygame.font.Font(None, 36)
        self.txt_surface = self.FONT.render(code, True, (255, 255, 255))

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False


def host_room():
    print("Hosting room...")


def join_room():
    print("Joining Room...")


def room_selection_screen():
    input_box_width = scale_value(300, BASE_WIDTH, WIDTH)
    input_box_height = scale_value(50, BASE_HEIGHT, HEIGHT)
    host_button_width = scale_value(250, BASE_WIDTH, WIDTH)
    host_button_height = scale_value(50, BASE_HEIGHT, HEIGHT)
    button_vertical_padding = scale_value(80, BASE_HEIGHT, HEIGHT)
    input_box_x = (WIDTH/2) - (input_box_width/2)
    input_box_y = (HEIGHT/2) - (input_box_height/2)
    join_button_x = (WIDTH/2) - (host_button_width/2)
    join_button_y = ((HEIGHT/2) - (host_button_width/2)) + (button_vertical_padding*2) # move this button down a bit
    host_button_x = (WIDTH/2) - (host_button_width/2)
    host_button_y = ((HEIGHT/2) - (host_button_width/2)) + (button_vertical_padding*3)
    input_box = TextBox(input_box_x, input_box_y, input_box_width, input_box_height)
    join_button = Button("Join Room", join_button_x, join_button_y, host_button_width, host_button_height, join_room)
    host_button = Button("Host Room", host_button_x, host_button_y, host_button_width, host_button_height, host_room)
    selecting_room = True
    joined_room = None

    while joined_room is None:
        while selecting_room:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                room_code_entered = input_box.handle_event(event)
                join_button_clicked = join_button.handle_event(event)
                host_button_clicked = host_button.handle_event(event)

                if room_code_entered or host_button_clicked or join_button_clicked:
                    selecting_room = False

            screen.fill((50, 50, 50))
            FONT = pygame.font.Font(None, 36)
            room_code_text = FONT.render("Enter Room Code:", True, WHITE)

            text_width, text_height = room_code_text.get_size()
            text_x = (WIDTH - text_width) // 2
            text_y = input_box_y - text_height - 20
            

            screen.blit(room_code_text, (text_x, text_y))

            input_box.draw(screen)
            join_button.draw(screen)
            host_button.draw(screen)

            pygame.display.flip()
            clock.tick(FPS)

            code = input_box.code

        ice_handler.connect(code)
        ice_handler.wait_for_connection()
        for connection in ice_handler.peer_datachannel_objects:
            if connection['is_established']['data']:
                joined_room = connection['connection_id']

    return joined_room

def apply_hue_variation(image, variation_amount):
    # Create a copy of the original image
    image_copy = image.copy()
    
    # Create random hue variations
    hue_shift = random.randint(-variation_amount, variation_amount)
    brightness_shift = random.randint(-variation_amount, variation_amount)

    # Apply color tinting by modifying the surface color
    for x in range(image_copy.get_width()):
        for y in range(image_copy.get_height()):
            r, g, b, a = image_copy.get_at((x, y))  # Get pixel color (with alpha)
            r = max(0, min(255, r + hue_shift + brightness_shift))
            g = max(0, min(255, g + hue_shift + brightness_shift))
            b = max(0, min(255, b + hue_shift + brightness_shift))
            image_copy.set_at((x, y), (r, g, b, a))  # Set modified color back to the image
    
    return image_copy



def main_game(room_id):
    global yellow_block_exists
    running = True
    if mode == 'test':
        controlled_player_id = 0
    else:
        ice_handler.peer_datachannel_objects[room_id]['server_side_id']['hook'].wait()
        controlled_player_id = ice_handler.peer_datachannel_objects[room_id]['server_side_id']['data']
    print(f'Your id: {controlled_player_id}')
    add_player(controlled_player_id)
    background = pygame.image.load(f'assets\\mine{random.randint(1,9)}.jpg')
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
<<<<<<< HEAD
    pygame.mixer.music.load(r'assets/Tussle Among Trees.mp3')
    pygame.mixer.music.play()
=======
    fps = 0
    frame_start = 0
    rolling_fps_tracker = []
>>>>>>> 28087dd22121bc8ba48c8927978146efa19dbb1a
    while running:
        fps = 1/(time.time()-frame_start)
        rolling_fps_tracker.append(fps)
        rolling_fps_tracker = rolling_fps_tracker[-60:]
        avg_fps = sum(rolling_fps_tracker)/len(rolling_fps_tracker)
        frame_start = time.time()
        screen.blit(background, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        for i, player in enumerate(players.values()):
            if i == current_player_index:
                player.handle_input(keys)
            player.update()

        #if yellow_block_exists:
        #    check_for_pvp_start()

        #if pvp_enabled:
        #    handle_pvp_collisions()

        for player in players.values():
            player.draw()

        for platform_image, platform_pos in precomputed_platforms:
            screen.blit(platform_image, platform_pos)
        if yellow_block:
            pygame.draw.rect(screen, YELLOW, yellow_block)

        display_player_coords()

        if mode == 'test':
            pass
        else:
            #ice_handler.send_message(room_id, {'udp': True, 'relay': True, 'content': {'player_id': controlled_player_id, 'xy': (players[controlled_player_id].x, players[controlled_player_id].y)}})

            while ice_handler.peer_datachannel_objects[room_id]['incoming_packets']['data']:
                packet = ice_handler.peer_datachannel_objects[room_id]['incoming_packets']['data'].pop(0)
                print(f'Received on connection {room_id}: {packet}')
                if type(packet['content']) == dict:
                    packet_content_dict = packet['content']
                    inc_pid = packet_content_dict['player_id']
                    if inc_pid not in players:
                        add_player(inc_pid)
                    players[inc_pid].x, players[inc_pid].y = packet_content_dict['xy']
<<<<<<< HEAD
        
=======
        screen.blit(font.render(f"{round(avg_fps, 2)}", True, (0, 200, 0)), (10, 20))
>>>>>>> 28087dd22121bc8ba48c8927978146efa19dbb1a
        pygame.display.flip()
        clock.tick(FPS)

zhmiscellany.misc.die_on_key('f8')

pygame.init()

# Get the display info
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
WIDTH = round(WIDTH/1.5)
HEIGHT = round(HEIGHT/1.5)
BASE_WIDTH, BASE_HEIGHT = 1920, 1080

lobby_platforms = [
    pygame.Rect(
        scale_value(BASE_WIDTH/3, BASE_WIDTH, WIDTH),
        scale_value(BASE_HEIGHT - 170, BASE_HEIGHT, HEIGHT),
        scale_value(700, BASE_WIDTH, WIDTH),
        scale_value(80, BASE_HEIGHT, HEIGHT)
    ),
        pygame.Rect(
        scale_value(BASE_WIDTH/8, BASE_WIDTH, WIDTH),
        scale_value(BASE_HEIGHT - 320, BASE_HEIGHT, HEIGHT),
        scale_value(400, BASE_WIDTH, WIDTH),
        scale_value(80, BASE_HEIGHT, HEIGHT)
    ),
        pygame.Rect(
        scale_value(BASE_WIDTH/1.4, BASE_WIDTH, WIDTH),
        scale_value(BASE_HEIGHT - 320, BASE_HEIGHT, HEIGHT),
        scale_value(400, BASE_WIDTH, WIDTH),
        scale_value(80, BASE_HEIGHT, HEIGHT)
    ),
]

platform_image = pygame.image.load(r'assets\bigRockWall.png')
precomputed_platforms = []
for platform in lobby_platforms:
    scaled_platform = pygame.transform.scale(platform_image, (platform.width, platform.height))
    varied_platform = apply_hue_variation(scaled_platform, 40)
    precomputed_platforms.append((varied_platform, platform.topleft))

pvp_map_platforms = generate_random_map()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ByPy")

BROWN = (139, 69, 19)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
#COLORS = (YELLOW, BLUE, GREEN, RED)
clock = pygame.time.Clock()
FPS = 60
player_width, player_height = 50, 50
player_speed = reverse_scale_value(5, BASE_WIDTH, WIDTH)
jump_strength = 15
<<<<<<< HEAD
gravity = scale_value(1, BASE_HEIGHT, HEIGHT)
=======
gravity = reverse_scale_value(0.65, BASE_HEIGHT, HEIGHT)
>>>>>>> 28087dd22121bc8ba48c8927978146efa19dbb1a
print(gravity)
player_hp = 100
wrecking_ball_radius = 30
chain_length = 150
wrecking_ball_mass = 0.5
wrecking_ball_friction = 0.95
font = pygame.font.SysFont('Arial', 24)
pvp_enabled = False
current_map = 'lobby'
yellow_block = pygame.Rect(WIDTH - 150, HEIGHT - 100, 100, 50)

# ice stuff
ice_handler = MultiPeerManager()

current_player_index = 0
players = {}
yellow_block_exists = True

running = True
input_box = TextBox(200, 150, 200, 40)
host_button = Button("Host a Room", 200, 250, 200, 50, host_room)


if __name__ == "__main__":
    mode = None
    pygame.mixer.init()
    pygame.mixer.music.set_volume(0.15)
    pygame.mixer.music.load(r'assets\Oggy and the cockroaches theme song - _High quality_.mp3')
    pygame.mixer.music.play()
    if len(sys.argv) != 1:
        if sys.argv[1] == 'test':
            mode = sys.argv[1]

    if mode == 'test':
        room_id = 0
    else:
        room_id = room_selection_screen()
    main_game(room_id)

    pygame.quit()

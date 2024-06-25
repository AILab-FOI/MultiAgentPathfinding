import pygame
from queue import PriorityQueue

# Define Player class
class Player:
    def __init__(self, color, start_pos):
        self.rect = pygame.Rect(start_pos[0], start_pos[1], 16, 16)
        self.color = color
        self.path = []

    def set_position(self, x, y):
        self.rect.x = x
        self.rect.y = y

# Define Wall and Door classes
class Wall:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], 16, 16)

class Door:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], 16, 16)
        self.open = False

# Define heuristic function
def heuristic(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return abs(x1 - x2) + abs(y1 - y2)

# A* algorithm implementation
def find_path(start, end, walls, doors):
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}

    while not open_set.empty():
        _, current = open_set.get()

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_pos = (current[0] + dx, current[1] + dy)
            if next_pos in walls or (next_pos in doors and not doors[next_pos]) or next_pos[0] < 0 or next_pos[0] >= len(level[0]) or next_pos[1] < 0 or next_pos[1] >= len(level):
                continue

            tentative_g_score = g_score[current] + 1
            if next_pos not in g_score or tentative_g_score < g_score[next_pos]:
                came_from[next_pos] = current
                g_score[next_pos] = tentative_g_score
                f_score[next_pos] = g_score[next_pos] + heuristic(next_pos, end)
                open_set.put((f_score[next_pos], next_pos))
    return []

# Function to find best path considering the door opening
def find_best_path(start, end, walls, key_pos, doors):
    initial_path = find_path(start, end, walls, doors)

    # Simulate opening the doors
    for door_pos in doors:
        doors[door_pos] = True

    # Find the path from start to the key, then from key to the end
    key_path = find_path(start, key_pos, walls, doors)
    new_path = find_path(key_pos, end, walls, doors)
    combined_path = key_path + new_path[1:] if key_path and new_path else None

    # Reset door status
    for door_pos in doors:
        doors[door_pos] = False

    # Compare initial path and combined path, and return the shortest one
    if combined_path:
        return initial_path if len(initial_path) < len(combined_path) else combined_path
    return initial_path

# Initialize pygame
pygame.init()

# Initialize screen and clock
pygame.display.set_caption("Get to the red square!")
screen = pygame.display.set_mode((360, 378))
clock = pygame.time.Clock()

# Define the level
level = [
    "WWWWWWWWWWWWWWWWWWWW",
    "W   P        P     W",
    "WWWWW WWWW WWWWW W W",
    "W W W W      W W W W",
    "W W W WW WWW W W W W",
    "W W W      W W W W W",
    "W W WWWW WWW W W W W",
    "W W W      W WDW W W",
    "W W W WWWW W W W W W",
    "W W W      W W W W W",
    "W WWW WWWWWW W W W W",
    "W      W         W W",
    "W WWWW W WWW W W W W",
    "W W    W W W W W W W",
    "W W WWWW W W W W W W",
    "W W      W W W W WWW",
    "W W WWWWWW W W W W W",
    "W W        W W W W W",
    "WVWW WWWWWWWWWWWVW W",
    "W             E    W",
    "WWWWWWWWWWWWWWWWWWWW"
]

# Create walls, doors and find start and end positions
walls = set()
doors = {}
start_pos_yellow = None
start_pos_blue = None
end_pos = None
key_pos = None
x = y = 0
for row in level:
    for col in row:
        if col == "W":
            walls.add((x // 18, y // 18))
        elif col == "P":
            if not start_pos_yellow:
                start_pos_yellow = (x // 18, y // 18)
            else:
                start_pos_blue = (x // 18, y // 18)
        elif col == "E":
            end_pos = (x // 18, y // 18)
        elif col == "D":
            key_pos = (x // 18, y // 18)
        elif col == "V":
            doors[(x // 18, y // 18)] = False
        x += 18
    y += 18
    x = 0

# Set initial positions for yellow and blue squares
yellow_player = Player((255, 200, 0), (start_pos_yellow[0] * 18, start_pos_yellow[1] * 18))
blue_player = Player((0, 0, 255), (start_pos_blue[0] * 18, start_pos_blue[1] * 18))

# Find best paths for yellow and blue squares
yellow_path = find_best_path(start_pos_yellow, end_pos, walls.copy(), key_pos, doors.copy())
blue_path = find_best_path(start_pos_blue, end_pos, walls.copy(), key_pos, doors.copy())

# Drawing functions
def draw_path(path, color):
    for i in range(len(path) - 1):
        pygame.draw.line(screen, color, (path[i][0] * 18 + 8, path[i][1] * 18 + 8), (path[i + 1][0] * 18 + 8, path[i + 1][1] * 18 + 8), 3)

def render_game():
    screen.fill((0, 0, 0))
    for wall in walls:
        pygame.draw.rect(screen, (0, 128, 64), pygame.Rect(wall[0] * 18, wall[1] * 18, 16, 16))
    for door_pos, is_open in doors.items():
        if not is_open:
            pygame.draw.rect(screen, (128, 0, 0), pygame.Rect(door_pos[0] * 18, door_pos[1] * 18, 16, 16))
    pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(end_pos[0] * 18, end_pos[1] * 18, 16, 16))
    pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(key_pos[0] * 18, key_pos[1] * 18, 16, 16))  # Drawing the key as green
    pygame.draw.rect(screen, yellow_player.color, yellow_player.rect)
    pygame.draw.rect(screen, blue_player.color, blue_player.rect)
    draw_path(yellow_path, (255, 255, 0))
    draw_path(blue_path, (0, 0, 255))
    pygame.display.flip()

def update_paths():
    global yellow_path, blue_path
    yellow_path = find_best_path((yellow_player.rect.x // 18, yellow_player.rect.y // 18), end_pos, walls.copy(), key_pos, doors.copy())
    blue_path = find_best_path((blue_player.rect.x // 18, blue_player.rect.y // 18), end_pos, walls.copy(), key_pos, doors.copy())

# Main loop
running = True
while running:
    clock.tick(5)

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    yellow_pos = (yellow_player.rect.x // 18, yellow_player.rect.y // 18)
    blue_pos = (blue_player.rect.x // 18, blue_player.rect.y // 18)

    if (yellow_pos == key_pos or blue_pos == key_pos):
        for door_pos in doors:
            doors[door_pos] = True
            walls.discard(door_pos)
        update_paths()

    if yellow_path:
        next_pos_yellow = yellow_path.pop(0)
        yellow_player.set_position(next_pos_yellow[0] * 18, next_pos_yellow[1] * 18)

    if blue_path:
        next_pos_blue = blue_path.pop(0)
        blue_player.set_position(next_pos_blue[0] * 18, next_pos_blue[1] * 18)

    render_game()

pygame.quit()

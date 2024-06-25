import pygame
from collections import deque
import heapq

# Initialize pygame
pygame.init()

# Screen settings
pygame.display.set_caption("Decentralized Planning: BFS and A*")
screen = pygame.display.set_mode((360, 378))
clock = pygame.time.Clock()

# Define Player class
class Player:
    def __init__(self, color, start_pos, walls, doors):
        self.rect = pygame.Rect(start_pos[0], start_pos[1], 16, 16)
        self.color = color
        self.path = []
        self.start_pos = (start_pos[0] // 18, start_pos[1] // 18)
        self.end_pos = None
        self.walls = walls
        self.doors = doors

    def set_position(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def bfs(self, start, end, walls, doors):
        queue = deque([start])
        came_from = {}
        visited = set()
        visited.add(start)
        
        while queue:
            current = queue.popleft()
            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_pos = (current[0] + dx, current[1] + dy)
                if next_pos in walls or (next_pos in doors and not doors[next_pos]) or next_pos in visited or next_pos[0] < 0 or next_pos[0] >= 40 or next_pos[1] < 0 or next_pos[1] >= 20:
                    continue
                queue.append(next_pos)
                came_from[next_pos] = current
                visited.add(next_pos)
        return []

    def a_star(self, start, goal, walls, doors):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, goal)}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                tentative_g_score = g_score[current] + 1
                if neighbor in walls or (neighbor in doors and not doors[neighbor]) or neighbor[0] < 0 or neighbor[0] >= 40 or neighbor[1] < 0 or neighbor[1] >= 20:
                    continue
                
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []

    def plan_path(self):
        current_pos = (self.rect.x // 18, self.rect.y // 18)
        walls = self.walls.copy()
        doors = self.doors.copy()

        # Direct path to end
        path_to_end = self.bfs(current_pos, self.end_pos, walls, doors)

        # Path via key
        path_to_key = self.bfs(current_pos, key_pos, walls, doors)
        if path_to_key:
            simulated_doors = doors.copy()
            for door_pos in simulated_doors:
                simulated_doors[door_pos] = True
            walls.difference_update(simulated_doors.keys())
            path_from_key_to_end = self.bfs(key_pos, self.end_pos, walls, simulated_doors)
        else:
            path_from_key_to_end = []

        if path_to_key and path_from_key_to_end:
            combined_path = path_to_key + path_from_key_to_end[1:]
            if len(combined_path) < len(path_to_end):
                local_path = []
                for i in range(len(combined_path) - 1):
                    segment_path = self.a_star(combined_path[i], combined_path[i + 1], walls, simulated_doors)
                    local_path.extend(segment_path)
                self.path = local_path
                print(f"Planned path for agent from {current_pos} via key to {self.end_pos}: {self.path}")
                return

        local_path = []
        for i in range(len(path_to_end) - 1):
            segment_path = self.a_star(path_to_end[i], path_to_end[i + 1], walls, doors)
            local_path.extend(segment_path)
        self.path = local_path
        print(f"Planned path for agent from {current_pos} to {self.end_pos}: {self.path}")

# Define heuristic for A* algorithm
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Define the level
level = [
    "WWWWWWWWWWWWWWWWWWWW",
    "W   P        P     W",
    "WWWWW WWWW WWWWW W W",
    "W W W W      W W W W",
    "W W W WW WWW W W W W",
    "W W W      W W W W W",
    "W W WWWW WWW W W W W",
    "W W W      W W W W W",
    "W W W WWWW W WDW W W",
    "W W W      W W W W W",
    "W WWW WWWWWW W W W W",
    "W      W         W W",
    "W WWWW W WWW WWW W W",
    "W W    W W W W W W W",
    "W W WWWW W W   W W W",
    "W W      W W W W WVW",
    "W WWWWWWWW WWW W W W",
    "W W            W W W",
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
yellow_player = Player((255, 200, 0), (start_pos_yellow[0] * 18, start_pos_yellow[1] * 18), walls, doors)
blue_player = Player((0, 0, 255), (start_pos_blue[0] * 18, start_pos_blue[1] * 18), walls, doors)

agents = [yellow_player, blue_player]

for agent in agents:
    agent.start_pos = (agent.rect.x // 18, agent.rect.y // 18)
    agent.end_pos = end_pos
    agent.plan_path()

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
    pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(key_pos[0] * 18, key_pos[1] * 18, 16, 16))
    for agent in agents:
        pygame.draw.rect(screen, agent.color, agent.rect)
        draw_path(agent.path, agent.color)
    pygame.display.flip()

# Main loop
running = True
door_opened = False
while running:
    clock.tick(5)

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    for agent in agents:
        pos = (agent.rect.x // 18, agent.rect.y // 18)
        if pos == key_pos and not door_opened:
            for door_pos in doors:
                doors[door_pos] = True
                walls.discard(door_pos)
            for agent in agents:
                agent.plan_path()
            door_opened = True

        if agent.path:
            next_pos = agent.path.pop(0)
            agent.set_position(next_pos[0] * 18, next_pos[1] * 18)

    render_game()

pygame.quit()

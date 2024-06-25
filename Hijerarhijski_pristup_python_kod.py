import pygame
from collections import deque
import heapq
import random

# Initialize pygame
pygame.init()

# Screen settings
pygame.display.set_caption("Hierarchical Planning: DHPA*")
screen = pygame.display.set_mode((720, 378))
clock = pygame.time.Clock()

# Define Player class
class Player:
    def __init__(self, color, start_pos):
        self.rect = pygame.Rect(start_pos[0], start_pos[1], 16, 16)
        self.color = color
        self.path = []
        self.start_pos = (start_pos[0] // 18, start_pos[1] // 18)
        self.end_pos = None

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

# Cluster class for hierarchical pathfinding
class Cluster:
    def __init__(self, cells, position):
        self.cells = cells
        self.position = position
        self.edges = []
        self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        self.cache = {}

# DHPA* algorithm components
def create_clusters(map_data, cluster_size, walls):
    clusters = []
    map_width = len(map_data[0])
    map_height = len(map_data)
    visited = set()
    
    def bfs(start):
        queue = deque([start])
        cluster_cells = []
        while queue:
            x, y = queue.popleft()
            if (x, y) in visited or (x, y) in walls or x < 0 or x >= map_width or y < 0 or y >= map_height:
                continue
            visited.add((x, y))
            cluster_cells.append((x, y))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor not in visited and neighbor not in walls:
                    queue.append(neighbor)
        return cluster_cells

    for y in range(map_height):
        for x in range(map_width):
            if (x, y) not in visited and (x, y) not in walls:
                cells = bfs((x, y))
                if cells:
                    cluster = Cluster(cells, (x // cluster_size, y // cluster_size))
                    clusters.append(cluster)
    
    return clusters

def connect_clusters(clusters):
    for i, cluster in enumerate(clusters):
        for j, other_cluster in enumerate(clusters):
            if i != j and are_neighbors(cluster, other_cluster):
                cluster.edges.append(other_cluster)

def are_neighbors(cluster1, cluster2):
    return any(abs(cell1[0] - cell2[0]) <= 1 and abs(cell1[1] - cell2[1]) <= 1 for cell1 in cluster1.cells for cell2 in cluster2.cells)

def precompute_paths(clusters, walls):
    for cluster in clusters:
        for node in cluster.cells:
            cache_paths = dijkstra(node, cluster.cells, walls)
            cluster.cache[node] = cache_paths

def dijkstra(start, nodes, walls):
    distances = {node: float('inf') for node in nodes}
    distances[start] = 0
    priority_queue = [(0, start)]
    came_from = {}

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distances[current_node]:
            continue

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current_node[0] + dx, current_node[1] + dy)
            if neighbor in nodes and neighbor not in walls:
                distance = current_distance + 1  # All edges have a distance of 1
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    came_from[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))

    return distances, came_from

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def abstract_pathfinding(start_cluster, end_cluster):
    open_set = []
    heapq.heappush(open_set, (0, start_cluster))
    came_from = {}
    g_score = {start_cluster: 0}
    f_score = {start_cluster: heuristic(start_cluster.position, end_cluster.position)}

    while open_set:
        _, current_cluster = heapq.heappop(open_set)

        if current_cluster == end_cluster:
            path = []
            while current_cluster in came_from:
                path.append(current_cluster)
                current_cluster = came_from[current_cluster]
            path.reverse()
            return path

        for neighbor in current_cluster.edges:
            tentative_g_score = g_score[current_cluster] + 1
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current_cluster
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor.position, end_cluster.position)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

def detailed_pathfinding(start, end, clusters, walls, doors):
    start_cluster = find_cluster(start, clusters)
    end_cluster = find_cluster(end, clusters)
    if start_cluster == end_cluster:
        return a_star(start, end, walls, doors)

    abstract_path = abstract_pathfinding(start_cluster, end_cluster)
    if not abstract_path:
        return []

    path = []
    current_position = start
    for cluster in abstract_path:
        if current_position == end:
            break
        path_segment = a_star(current_position, end, walls, doors)
        if not path_segment:
            return []
        path.extend(path_segment)
        current_position = path_segment[-1]
    return path

def find_cluster(pos, clusters):
    for cluster in clusters:
        if pos in cluster.cells:
            return cluster
    return None

def find_shortest_path(start, end, key_pos, doors, walls, clusters):
    # Direct path
    direct_path = detailed_pathfinding(start, end, clusters, walls, doors)
    
    # Path via key
    path_to_key = detailed_pathfinding(start, key_pos, clusters, walls, doors)
    if path_to_key:
        # Temporarily open doors
        doors_opened = []
        for door_pos in doors:
            if not doors[door_pos]:
                doors[door_pos] = True
                walls.discard(door_pos)
                doors_opened.append(door_pos)

        path_from_key_to_end = detailed_pathfinding(key_pos, end, clusters, walls, doors)

        # Close the doors again
        for door_pos in doors_opened:
            doors[door_pos] = False
            walls.add(door_pos)

        if path_from_key_to_end:
            path_via_key = path_to_key + path_from_key_to_end
        else:
            path_via_key = []
    else:
        path_via_key = []

    # Choose the shorter path
    if path_via_key and (not direct_path or len(path_via_key) < len(direct_path)):
        return path_via_key
    else:
        return direct_path

# A* algorithm implementation
def a_star(start, end, walls, doors):
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_pos = (current[0] + dx, current[1] + dy)
            if next_pos in walls or (next_pos in doors and not doors[next_pos]) or next_pos[0] < 0 or next_pos[0] >= 40 or next_pos[1] < 0 or next_pos[1] >= 20:
                continue

            tentative_g_score = g_score[current] + 1
            if next_pos not in g_score or tentative_g_score < g_score[next_pos]:
                came_from[next_pos] = current
                g_score[next_pos] = tentative_g_score
                f_score[next_pos] = tentative_g_score + heuristic(next_pos, end)
                heapq.heappush(open_set, (f_score[next_pos], next_pos))
    return []

# Central planner class definition
class CentralPlanner:
    def __init__(self, clusters, walls, doors):
        self.clusters = clusters
        self.walls = walls
        self.doors = doors
        self.agents = []

    def update_walls(self, walls):
        self.walls = walls

    def update_doors(self, doors):
        self.doors = doors

    def register_agent(self, agent):
        self.agents.append(agent)

    def plan_paths(self, key_pos):
        for agent in self.agents:
            agent.path = find_shortest_path((agent.rect.x // 18, agent.rect.y // 18), agent.end_pos, key_pos, self.doors, self.walls, self.clusters)
            print(f"Agent {agent.color} path: {agent.path}")

# Define the level
level = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W   P        P     WW   P        P     W",
    "WWWWW WWWW WWWWW W WWWWWW WWWW WWWWW W W",
    "W W W W      W W W WW W W W      W W W W",
    "W W W WW WWW W W W WW W W WW WWW W W W W",
    "W W W      W W W W WW W W      W W W W W",
    "W W WWWW WWW W W W WW W WWWW WWW W W W W",
    "W W W      W WDW W WW W W      W WDW W W",
    "W W W WWWW W W W W WW W W WWWW W W W W W",
    "W W W      W W W W WW W W      W W W W W",
    "W WWW WWWWWW W W W WW WWW WWWWWW W W W W",
    "W      W         W WW      W         W W",
    "W WWWW W WWW WWW W WW WWWW W WWW WWW W W",
    "W W    W W W W W W WW W    W W W W W W W",
    "W W WWWW W W   W W WW W WWWW W W   W W W",
    "W W      W W W W WVWW W      W W W W WVW",
    "W WWWWWWWW WWW W W WW WWWWWWWW WWW W W W",
    "W W            W W WW W            W W W",
    "WVWW WWWWWWWWWWWVW WWVWW WWWWWWWWWWWVW W",
    "W             E    WW             E    W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
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
        if x // 18 >= 20:
            break
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

walls2 = set()
doors2 = {}
start_pos_yellow2 = None
start_pos_blue2 = None
end_pos2 = None
key_pos2 = None
x = y = 0
for row in level:
    for col in row[20:]:
        if x // 18 >= 20:
            break
        if col == "W":
            walls2.add((x // 18 + 20, y // 18)) 
        elif col == "P":
            if not start_pos_yellow2:
                start_pos_yellow2 = (x // 18 + 20, y // 18) 
            else:
                start_pos_blue2 = (x // 18 + 20, y // 18) 
        elif col == "E":
            end_pos2 = (x // 18 + 20, y // 18) 
        elif col == "D":
            key_pos2 = (x // 18 + 20, y // 18)
        elif col == "V":
            doors2[(x // 18 + 20, y // 18)] = False
        x += 18
    y += 18
    x = 0

# Set initial positions for yellow and blue squares
yellow_player1 = Player((255, 200, 0), (start_pos_yellow[0] * 18, start_pos_yellow[1] * 18))
blue_player1 = Player((0, 0, 255), (start_pos_blue[0] * 18, start_pos_blue[1] * 18))
yellow_player2 = Player((255, 200, 0), (start_pos_yellow2[0] * 18, start_pos_yellow2[1] * 18))
blue_player2 = Player((0, 0, 255), (start_pos_blue2[0] * 18, start_pos_blue2[1] * 18))

# Initialize central planners
clusters_map1 = create_clusters(level, 4, walls)
clusters_map2 = create_clusters(level, 4, walls2)

connect_clusters(clusters_map1)
connect_clusters(clusters_map2)

precompute_paths(clusters_map1, walls)
precompute_paths(clusters_map2, walls2)

central_planner1 = CentralPlanner(clusters_map1, walls, doors)
central_planner2 = CentralPlanner(clusters_map2, walls2, doors2)

agents_map1 = [yellow_player1, blue_player1]
agents_map2 = [yellow_player2, blue_player2]

for agent in agents_map1:
    agent.start_pos = (agent.rect.x // 18, agent.rect.y // 18)
    agent.end_pos = end_pos
    central_planner1.register_agent(agent)

for agent in agents_map2:
    agent.start_pos = (agent.rect.x // 18, agent.rect.y // 18)
    agent.end_pos = end_pos2
    central_planner2.register_agent(agent)

# Central planners plan paths for all agents
central_planner1.plan_paths(key_pos)
central_planner2.plan_paths(key_pos2)

# Drawing functions
def draw_path(path, color):
    for i in range(len(path) - 1):
        pygame.draw.line(screen, color, (path[i][0] * 18 + 8, path[i][1] * 18 + 8), (path[i + 1][0] * 18 + 8, path[i + 1][1] * 18 + 8), 3)

def render_game():
    screen.fill((0, 0, 0))
    for wall in walls.union(walls2):
        pygame.draw.rect(screen, (0, 128, 64), pygame.Rect(wall[0] * 18, wall[1] * 18, 16, 16))
    for door_pos, is_open in {**doors, **doors2}.items():
        if not is_open:
            pygame.draw.rect(screen, (128, 0, 0), pygame.Rect(door_pos[0] * 18, door_pos[1] * 18, 16, 16))
    for pos in [end_pos, end_pos2]:
        pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(pos[0] * 18, pos[1] * 18, 16, 16))
    for pos in [key_pos, key_pos2]:
        pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(pos[0] * 18, pos[1] * 18, 16, 16))  # Drawing the key as green
    for agent in agents_map1 + agents_map2:
        pygame.draw.rect(screen, agent.color, agent.rect)
        draw_path(agent.path, agent.color)
    # Draw clusters
    for cluster in clusters_map1 + clusters_map2:
        for cell in cluster.cells:
            pygame.draw.rect(screen, cluster.color, pygame.Rect(cell[0] * 18, cell[1] * 18, 16, 16), 1)
    pygame.display.flip()

# Main loop
running = True
door_opened_map1 = False
door_opened_map2 = False

while running:
    clock.tick(5)

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    for agent in agents_map1 + agents_map2:
        pos = (agent.rect.x // 18, agent.rect.y // 18)

        # Check for key positions and open doors if not already opened
        if pos == key_pos and not door_opened_map1:
            for door_pos in doors:
                doors[door_pos] = True
                walls.discard(door_pos)
            central_planner1.update_doors(doors)
            central_planner1.update_walls(walls)
            for agent in agents_map1:
                agent.start_pos = (agent.rect.x // 18, agent.rect.y // 18)
            central_planner1.plan_paths(key_pos)
            door_opened_map1 = True

        if pos == key_pos2 and not door_opened_map2:
            for door_pos in doors2:
                doors2[door_pos] = True
                walls2.discard(door_pos)
            central_planner2.update_doors(doors2)
            central_planner2.update_walls(walls2)
            for agent in agents_map2:
                agent.start_pos = (agent.rect.x // 18, agent.rect.y // 18)
            central_planner2.plan_paths(key_pos2)
            door_opened_map2 = True

        # Move along the path if it exists
        if agent.path:
            next_pos = agent.path.pop(0)
            agent.set_position(next_pos[0] * 18, next_pos[1] * 18)

    render_game()

pygame.quit()

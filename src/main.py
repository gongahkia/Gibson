import json
import random
import sys
import pygame
import numpy as np
from enum import Enum
from OpenGL.GL import *
from OpenGL.GLU import *
from noise import pnoise3
from pygame.locals import *

class CellType(Enum):
    EMPTY = 0
    VERTICAL = 1    # Load-bearing walls
    HORIZONTAL = 2  # Floor platforms
    BRIDGE = 3      # Structural connections
    FACADE = 4      # Non-load-bearing walls
    STAIR = 5       # Vertical circulation

class MegaStructureGenerator:
    def __init__(self, size=30, layers=15):
        self.size = size
        self.layers = layers
        self.grid = np.full((size, size, layers), CellType.EMPTY, dtype=object)
        self.connections = []
        self.rooms = []
        self.support_map = np.zeros((size, size, layers), dtype=bool)

    def generate_kowloon_style(self):

        # Phase 1: Structural skeleton
        self._create_vertical_cores()
        self._generate_floor_slabs()
        
        # Phase 2: Spatial organization
        self._create_room_clusters()
        self._connect_vertical_cores()
        
        # Phase 3: Structural validation
        self._ensure_structural_integrity()
        self._add_support_pillars()
        
        # Phase 4: Organic growth
        self._add_secondary_structures()
        self._create_sky_bridges()

    def _create_vertical_cores(self):
        # Create primary load-bearing cores with staggered heights
        core_spacing = random.randint(4, 6)
        for x in range(0, self.size, core_spacing):
            for z in range(0, self.size, core_spacing):
                if random.random() < 0.8:
                    height = min(random.randint(8, self.layers-2), self.layers)
                    self._build_vertical_core(x, z, height)

    def _build_vertical_core(self, x, z, height):
        # Create core with random tapering
        base_width = random.randint(2, 3)
        for y in range(height):
            current_width = max(1, base_width - int(y/4))
            for dx in range(-current_width, current_width+1):
                for dz in range(-current_width, current_width+1):
                    nx, nz = x+dx, z+dz
                    if 0 <= nx < self.size and 0 <= nz < self.size:
                        self.grid[nx][nz][y] = CellType.VERTICAL
                        self.support_map[nx][nz][y] = True

    def _generate_floor_slabs(self):
        # Create interconnected floor slabs with organic shapes
        for y in range(self.layers):
            noise_scale = 0.15
            floor_thickness = random.randint(1, 2)
            
            for x in range(self.size):
                for z in range(self.size):
                    if self.grid[x][z][y] == CellType.VERTICAL:
                        # Generate floor slabs around vertical cores
                        if random.random() < 0.7:
                            self._expand_floor(x, y, z, floor_thickness, noise_scale)

    def _expand_floor(self, x, y, z, thickness, noise_scale):
        # Cellular automata approach for floor generation
        queue = [(x, z)]
        visited = set()
        
        while queue:
            cx, cz = queue.pop(0)
            if (cx, cz) in visited:
                continue
                
            visited.add((cx, cz))
            
            # Check structural support
            if y > 0 and not self.support_map[cx][cz][y-1]:
                continue
                
            noise_val = pnoise3(cx*noise_scale, y*0.2, cz*noise_scale)
            if noise_val > -0.2:
                for dy in range(thickness):
                    if y+dy < self.layers:
                        self.grid[cx][cz][y+dy] = CellType.HORIZONTAL
                        self.support_map[cx][cz][y+dy] = True
                
                # Expand to neighbors
                for dx, dz in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nx, nz = cx+dx, cz+dz
                    if 0 <= nx < self.size and 0 <= nz < self.size:
                        queue.append((nx, nz))

    def _create_room_clusters(self):
        # Define functional spaces with different sizes
        room_types = [
            {'size': (3,5), 'height': 2, 'type': CellType.HORIZONTAL},  # Residential
            {'size': (5,8), 'height': 3, 'type': CellType.HORIZONTAL},  # Commercial
            {'size': (2,4), 'height': 1, 'type': CellType.VERTICAL}     # Circulation
        ]
        
        for _ in range(int(self.size**2 / 20)):
            room = random.choice(room_types)
            x = random.randint(0, self.size-1)
            z = random.randint(0, self.size-1)
            y = random.randint(0, self.layers-1)
            
            if self.grid[x][z][y] == CellType.HORIZONTAL:
                self._carve_room(x, y, z, room)

    def _carve_room(self, x, y, z, room):
        # Create defined spaces with structural validation
        width, depth = random.randint(*room['size']), random.randint(*room['size'])
        height = room['height']
        
        for dx in range(width):
            for dz in range(depth):
                for dy in range(height):
                    nx = x + dx
                    nz = z + dz
                    ny = y + dy
                    
                    if 0 <= nx < self.size and 0 <= nz < self.size and ny < self.layers:
                        if dy == 0:  # Floor
                            self.grid[nx][nz][ny] = CellType.HORIZONTAL
                        else:        # Walls
                            if dx in [0, width-1] or dz in [0, depth-1]:
                                self.grid[nx][nz][ny] = CellType.FACADE
                                
                        self.support_map[nx][nz][ny] = True

    def _ensure_structural_integrity(self):
        # Gravity simulation and support validation
        for y in range(1, self.layers):
            for x in range(self.size):
                for z in range(self.size):
                    if self.grid[x][z][y] in [CellType.HORIZONTAL, CellType.FACADE]:
                        if not self._has_support(x, y, z):
                            # Remove unsupported elements
                            self.grid[x][z][y] = CellType.EMPTY

    def _has_support(self, x, y, z):
        # Check vertical support or adjacent horizontal connections
        if self.support_map[x][z][y-1]:
            return True
            
        # Check for bridging support
        for dx, dz in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, nz = x+dx, z+dz
            if 0 <= nx < self.size and 0 <= nz < self.size:
                if self.grid[nx][nz][y] in [CellType.HORIZONTAL, CellType.BRIDGE]:
                    return True
        return False

    def _create_sky_bridges(self):
        # Connect towers with proper bridging structures
        for y in range(3, self.layers, 4):
            cores = [(x, z) for x in range(self.size) 
                    for z in range(self.size) 
                    if self.grid[x][z][y] == CellType.VERTICAL]
            
            if len(cores) > 1:
                start = random.choice(cores)
                end = random.choice([c for c in cores if c != start])
                self._build_bridge(start, end, y)

    def _add_secondary_structures(self):
        for _ in range(int(self.size * self.layers * 0.05)):  # Add 5% of total volume as secondary structures
            x = random.randint(0, self.size-1)
            z = random.randint(0, self.size-1)
            y = random.randint(1, self.layers-1)
            
            if self.grid[x][z][y] == CellType.EMPTY and self._has_support(x, y, z):
                structure_type = random.choice([CellType.HORIZONTAL, CellType.FACADE])
                self.grid[x][z][y] = structure_type
                
                # Add some vertical extension
                for dy in range(1, random.randint(1, 3)):
                    if y + dy < self.layers and self.grid[x][z][y+dy] == CellType.EMPTY:
                        self.grid[x][z][y+dy] = structure_type


    def _add_support_pillars(self):
        for x in range(self.size):
            for z in range(self.size):
                for y in range(1, self.layers):
                    if self.grid[x][z][y] == CellType.HORIZONTAL and not self._has_support(x, y, z):
                        # Add a vertical support pillar below the unsupported horizontal element
                        for py in range(y-1, -1, -1):
                            if self.grid[x][z][py] == CellType.EMPTY:
                                self.grid[x][z][py] = CellType.VERTICAL
                                self.support_map[x][z][py] = True
                            else:
                                break  # Stop if we hit a non-empty cell

    def _connect_vertical_cores(self):
        # Find all vertical cores
        cores = [(x, z) for x in range(self.size) for z in range(self.size) 
                if any(self.grid[x][z][y] == CellType.VERTICAL for y in range(self.layers))]
        
        # Connect cores with horizontal bridges at various heights
        for y in range(2, self.layers, 3):  # Start at layer 2, every 3 layers
            for i in range(len(cores)):
                for j in range(i+1, len(cores)):
                    if random.random() < 0.3:  # 30% chance to connect any two cores
                        start = cores[i]
                        end = cores[j]
                        self._build_bridge(start, end, y)

        # Add some vertical connections (stairs or elevators)
        for x, z in cores:
            for y in range(1, self.layers-1):
                if self.grid[x][z][y] == CellType.VERTICAL:
                    if random.random() < 0.2:  # 20% chance to add vertical connection
                        self.grid[x][z][y] = CellType.STAIR

    def _build_bridge(self, start, end, y):
        # 3D Bresenham's line algorithm for bridge connections
        x1, z1 = start
        x2, z2 = end
        dx = abs(x2 - x1)
        dz = abs(z2 - z1)
        
        sx = 1 if x2 > x1 else -1
        sz = 1 if z2 > z1 else -1
        err = dx - dz
        
        while True:
            if self._is_valid_bridge_point(x1, z1, y):
                self.grid[x1][z1][y] = CellType.BRIDGE
                self.grid[x1][z1][y+1] = CellType.BRIDGE  # Add height
                
            if x1 == x2 and z1 == z2:
                break
                
            e2 = 2*err
            if e2 > -dz:
                err -= dz
                x1 += sx
            if e2 < dx:
                err += dx
                z1 += sz

    def _is_valid_bridge_point(self, x, z, y):
        # Check bridge foundation
        if y > 0 and self.grid[x][z][y-1] in [CellType.VERTICAL, CellType.BRIDGE]:
            return True
        return False

    def save_structure(self, filename):
        data = {
            'grid': [[[cell.value for cell in col] for col in layer] for layer in self.grid],
            'connections': self.connections,
            'rooms': self.rooms
        }
        with open(filename, 'w') as f:
            json.dump(data, f)

    def load_structure(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            self.grid = np.array([[[CellType(cell) for cell in col] for col in layer] 
                                for layer in data['grid']])
            self.connections = [tuple(map(tuple, c)) for c in data['connections']]
            self.rooms = data['rooms']

class IsometricVisualizer:
    def __init__(self, generator):
        self.generator = generator
        self.angle = 45
        self.zoom = 1.0
        self.init_pygame()
        self._init_font_system()
        self.debug_surface = pygame.Surface((200, 150), pygame.SRCALPHA).convert_alpha()

    def _init_font_system(self):
        pygame.font.init()
        try:
            self.font = pygame.font.Font(None, 24)
            test_surface = self.font.render("Test", True, (255, 255, 255))
            if test_surface.get_width() == 0:
                raise RuntimeError("Font rendering failed")
        except Exception as e:
            print(f"Font error: {e}")
            self.font = pygame.font.SysFont('Arial', 24)

    def init_pygame(self):
        pygame.init()
        self.display = (800, 600)
        self.screen = pygame.display.set_mode(self.display, DOUBLEBUF|OPENGL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.1, 0.1, 0.1, 1.0)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def draw_cube(self, position, cell_type):
        x, y, z = position
        glPushMatrix()
        glTranslate(x, y, z)
        
        colors = {
            CellType.EMPTY: (0.1, 0.1, 0.1),
            CellType.VERTICAL: (0.2, 0.6, 0.8),
            CellType.HORIZONTAL: (0.8, 0.4, 0.2),
            CellType.BRIDGE: (0.6, 0.8, 0.2),
            CellType.FACADE: (0.9, 0.9, 0.7),
            CellType.STAIR: (0.7, 0.3, 0.7)
        }
        
        glColor3fv(colors.get(cell_type, (1.0, 1.0, 1.0)))
        
        vertices = [
            (-0.4, -0.4, -0.4), ( 0.4, -0.4, -0.4), ( 0.4,  0.4, -0.4), (-0.4,  0.4, -0.4),
            (-0.4, -0.4,  0.4), ( 0.4, -0.4,  0.4), ( 0.4,  0.4,  0.4), (-0.4,  0.4,  0.4)
        ]
        
        faces = [
            (0, 1, 2, 3), (3, 2, 6, 7), (7, 6, 5, 4),
            (4, 5, 1, 0), (1, 5, 6, 2), (4, 0, 3, 7)
        ]
        
        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(1.0)
        
        glBegin(GL_LINES)
        for edge in [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        glPopMatrix()

    def render_debug_panel(self):
        self.debug_surface.fill((50, 50, 50, 180))
        y_offset = 10
        
        legend_items = [
            ("Vertical", (0.2, 0.6, 0.8)),
            ("Horizontal", (0.8, 0.4, 0.2)),
            ("Bridge", (0.6, 0.8, 0.2)),
            ("Facade", (0.9, 0.9, 0.7)),
            ("Stair", (0.7, 0.3, 0.7))
        ]
        
        for text, color in legend_items:
            pygame_color = [int(c * 255) for c in color]
            text_surface = self.font.render(text, True, (255, 255, 255))
            pygame.draw.rect(self.debug_surface, pygame_color, (10, y_offset, 20, 20))
            self.debug_surface.blit(text_surface, (40, y_offset))
            y_offset += 30
        
        angle_text = self.font.render(f"Angle: {self.angle}°", True, (255, 255, 255))
        self.debug_surface.blit(angle_text, (10, y_offset))
        y_offset += 30
        zoom_text = self.font.render(f"Zoom: {self.zoom:.2f}x", True, (255, 255, 255))
        self.debug_surface.blit(zoom_text, (10, y_offset))

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        distance = max(self.generator.size, self.generator.layers) * 1.5 / self.zoom
        cam_x = distance * np.cos(np.radians(self.angle))
        cam_z = distance * np.sin(np.radians(self.angle))
        cam_y = distance * 0.5
        
        center = (self.generator.size/2, self.generator.layers/2, self.generator.size/2)
        
        gluLookAt(cam_x, cam_y, cam_z, *center, 0, 1, 0)
        
        for x in range(self.generator.size):
            for z in range(self.generator.size):
                for y in range(self.generator.layers):
                    cell_type = self.generator.grid[x][z][y]
                    if cell_type != CellType.EMPTY:
                        self.draw_cube((x, y, z), cell_type)

        # Switch to 2D mode
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.render_debug_panel()
        
        tex_data = pygame.image.tostring(self.debug_surface, "RGBA", True)
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 200, 150, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

        glEnable(GL_TEXTURE_2D)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(self.display[0]-200, 0)
        glTexCoord2f(1, 1); glVertex2f(self.display[0], 0)
        glTexCoord2f(1, 0); glVertex2f(self.display[0], 150)
        glTexCoord2f(0, 0); glVertex2f(self.display[0]-200, 150)
        glEnd()
        glDisable(GL_TEXTURE_2D)

        glDeleteTextures([texture])

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.angle = (self.angle - 45) % 360
                    elif event.button == 3:
                        self.angle = (self.angle + 45) % 360
                    elif event.button == 4:  # Scroll up
                        self.zoom = min(self.zoom * 1.1, 3.0)
                    elif event.button == 5:  # Scroll down
                        self.zoom = max(self.zoom / 1.1, 0.5)

            self.render()
            clock.tick(30)

if __name__ == '__main__':

    print("Gibson: generating structure...")
    generator = MegaStructureGenerator()
    generator.generate_kowloon_style()
    generator.save_structure('kowloon_structure.json')

    print("Gibson: visualizing structure...")
    visualizer = IsometricVisualizer(generator)
    visualizer.run()
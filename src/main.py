import json
import random
import sys
import numpy as np
from enum import Enum
from noise import pnoise3
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class CellType(Enum):
    EMPTY = 0
    OCCUPIED = 1
    VERTICAL = 2
    HORIZONTAL = 3
    BRIDGE = 4

class MegaStructureGenerator:
    def __init__(self, size=30, layers=15):
        self.size = size
        self.layers = layers
        self.grid = np.full((size, size, layers), CellType.EMPTY, dtype=object)
        self.connections = []

    def generate_kowloon_style(self):
        # Create vertical cores
        for x in range(0, self.size, 5):
            for z in range(0, self.size, 5):
                if random.random() < 0.7:
                    self._create_vertical_shaft(x, z)
        
        # Add horizontal connections
        for y in range(self.layers):
            self._add_organic_connections(y)
            
        # Generate overhangs and bridges
        self._create_overhangs()

    def _create_vertical_shaft(self, x, z):
        height = random.randint(3, self.layers-1)
        for y in range(height):
            self.grid[x][z][y] = CellType.VERTICAL
            if y > 0:
                self.connections.append(((x, y-1, z), (x, y, z)))

    def _add_organic_connections(self, y):
        scale = 0.1
        for x in range(self.size):
            for z in range(self.size):
                if pnoise3(x*scale, y*scale, z*scale) > 0.5:
                    if self.grid[x][z][y] == CellType.VERTICAL:
                        self._expand_cluster(x, y, z)

    def _expand_cluster(self, x, y, z):
        cluster_radius = 3
        for dx in range(-cluster_radius, cluster_radius+1):
            for dz in range(-cluster_radius, cluster_radius+1):
                nx = x + dx
                nz = z + dz
                if 0 <= nx < self.size and 0 <= nz < self.size:
                    if random.random() < 0.7 and self.grid[nx][nz][y] == CellType.EMPTY:
                        self.grid[nx][nz][y] = CellType.HORIZONTAL
                        self.connections.append(((x, y, z), (nx, y, nz)))

    def _create_overhangs(self):
        for _ in range(self.size//2):
            x1, z1 = random.randint(0, self.size-1), random.randint(0, self.size-1)
            x2, z2 = random.randint(0, self.size-1), random.randint(0, self.size-1)
            y = random.randint(0, self.layers-2)
            self._connect_points((x1,y,z1), (x2,y,z2))

    def _connect_points(self, p1, p2):
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[2] - p1[2])
        dz = abs(p2[1] - p1[1])
        
        xs = 1 if p2[0] > p1[0] else -1
        ys = 1 if p2[2] > p1[2] else -1
        zs = 1 if p2[1] > p1[1] else -1

        current = list(p1)
        for _ in range(dx + dy + dz):
            last = list(current)
            err = dx + dy + dz
            if err - dx < dz:
                current[1] += zs
            if err - dy < dz:
                current[0] += xs
            if err - dz < dx:
                current[2] += ys
            self.grid[current[0]][current[2]][current[1]] = CellType.BRIDGE
            self.connections.append((tuple(last), tuple(current)))

    def save_structure(self, filename):
        data = {
            'grid': [[[cell.value for cell in col] for col in layer] for layer in self.grid],
            'connections': self.connections
        }
        with open(filename, 'w') as f:
            json.dump(data, f)

    def load_structure(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            self.grid = np.array([[[CellType(cell) for cell in col] for col in layer] for layer in data['grid']])
            self.connections = [tuple(map(tuple, c)) for c in data['connections']]

import pygame
import sys
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

class IsometricVisualizer:
        
    def __init__(self, generator):
        self.generator = generator
        self.angle = 45
        self._init_font_system()  
        self.debug_surface = pygame.Surface((200, 150))
        self.debug_surface.set_alpha(200)
        self.init_pygame()

    def _init_font_system(self):
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.debug_surface = pygame.Surface((200, 150))
        self.debug_surface.set_alpha(200)

    def init_pygame(self):
        pygame.init()
        self.display = (800, 600)
        self.screen = pygame.display.set_mode(self.display, DOUBLEBUF|OPENGL)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.1, 1.0)
        
        # Set up orthographic projection for isometric view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def draw_cube(self, position, cell_type):
        x, y, z = position
        glPushMatrix()
        glTranslate(x, y, z)
        
        # Color mapping for different cell types
        colors = {
            CellType.EMPTY: (0.1, 0.1, 0.1),      # Dark Gray (almost black)
            CellType.OCCUPIED: (0.8, 0.8, 0.8),   # Light Gray
            CellType.VERTICAL: (0.2, 0.6, 0.8),   # Light Blue
            CellType.HORIZONTAL: (0.8, 0.4, 0.2), # Orange
            CellType.BRIDGE: (0.6, 0.8, 0.2)      # Lime Green
        }
        
        # Set color based on cell type
        glColor3fv(colors.get(cell_type, (1.0, 1.0, 1.0)))  # Default to white if type not found
        
        # Define cube vertices
        vertices = [
            (-0.4, -0.4, -0.4), ( 0.4, -0.4, -0.4), ( 0.4,  0.4, -0.4), (-0.4,  0.4, -0.4),
            (-0.4, -0.4,  0.4), ( 0.4, -0.4,  0.4), ( 0.4,  0.4,  0.4), (-0.4,  0.4,  0.4)
        ]
        
        # Define cube faces
        faces = [
            (0, 1, 2, 3), (3, 2, 6, 7), (7, 6, 5, 4),
            (4, 5, 1, 0), (1, 5, 6, 2), (4, 0, 3, 7)
        ]
        
        # Draw filled cube
        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        # Draw wireframe outline
        glColor3f(0.0, 0.0, 0.0)  # Black color for wireframe
        glLineWidth(1.0)  # Set line width
        
        glBegin(GL_LINES)
        for edge in [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        glPopMatrix()

    def render_debug_panel(self):
        self.debug_surface.fill((50, 50, 50))
        y_offset = 10
        
        # Render color legend
        legend_items = [
            ("Vertical", (0.2, 0.6, 0.8)),
            ("Horizontal", (0.8, 0.4, 0.2)),
            ("Bridge", (0.6, 0.8, 0.2)),
            ("Occupied", (0.8, 0.8, 0.8))
        ]
        
        for text, color in legend_items:
            pygame_color = [int(c * 255) for c in color]
            text_surface = self.font.render(text, True, (255, 255, 255))
            pygame.draw.rect(self.debug_surface, pygame_color, (10, y_offset, 20, 20))
            self.debug_surface.blit(text_surface, (40, y_offset))
            y_offset += 30
        
        # Render current angle
        angle_text = f"Angle: {self.angle}°"
        angle_surface = self.font.render(angle_text, True, (255, 255, 255))
        self.debug_surface.blit(angle_surface, (10, y_offset))
        
        # Blit debug surface to main display
        self.screen.blit(self.debug_surface, (self.display[0] - 210, 10))

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Calculate the camera position
        distance = max(self.generator.size, self.generator.layers) * 1.5
        cam_x = distance * np.cos(np.radians(self.angle))
        cam_z = distance * np.sin(np.radians(self.angle))
        cam_y = distance * 0.5  # Adjust this value to change the camera height
        
        # Center of the structure
        center = (self.generator.size/2, self.generator.layers/2, self.generator.size/2)
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Set up the camera
        gluLookAt(
            cam_x, cam_y, cam_z,  # Camera position
            *center,              # Look at center
            0, 1, 0               # Up vector
        )
        
        # Draw all cubes
        for x in range(self.generator.size):
            for z in range(self.generator.size):
                for y in range(self.generator.layers):
                    cell_type = self.generator.grid[x][z][y]
                    if cell_type != CellType.EMPTY:
                        self.draw_cube((x, y, z), cell_type)

        # Switch to 2D rendering for debug panel
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Render the debug panel
        self.render_debug_panel()
        
        # Switch back to 3D rendering
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        pygame.display.flip()


    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.angle = (self.angle - 45) % 360
                    elif event.button == 3:  # Right click
                        self.angle = (self.angle + 45) % 360

            self.render()
            clock.tick(30)

if __name__ == '__main__':

    print("Gibson: generating structure...")
    generator = MegaStructureGenerator()
    generator.generate_kowloon_style()
    generator.save_structure('kowloon_structure.json')

    visualizer = IsometricVisualizer(generator)
    visualizer.run()
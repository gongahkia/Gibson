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

class IsometricVisualizer:
    def __init__(self, generator):
        self.generator = generator
        self.angle = 45
        self.init_pygame()  # Initialize Pygame first
        self._init_font_system()  # Then initialize fonts
        self.debug_surface = pygame.Surface((200, 150), pygame.SRCALPHA)

    def _init_font_system(self):
        self.font = pygame.font.Font(None, 24)

    def init_pygame(self):
        pygame.init()
        self.display = (800, 600)
        self.screen = pygame.display.set_mode(self.display, DOUBLEBUF|OPENGL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)  # Enable blending
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.1, 0.1, 0.1, 1.0)

    def render_debug_panel(self):
        self.debug_surface.fill((50, 50, 50, 200))  # RGBA color
        y_offset = 10
        
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
            
        angle_text = self.font.render(f"Angle: {self.angle}°", True, (255, 255, 255))
        self.debug_surface.blit(angle_text, (10, y_offset))

    def render(self):
        # 3D rendering
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera setup
        distance = max(self.generator.size, self.generator.layers) * 1.5
        cam_x = distance * np.cos(np.radians(self.angle))
        cam_z = distance * np.sin(np.radians(self.angle))
        center = (self.generator.size/2, self.generator.layers/2, self.generator.size/2)
        
        gluLookAt(cam_x, distance*0.5, cam_z, *center, 0, 1, 0)
        
        # Draw cubes
        for x in range(self.generator.size):
            for z in range(self.generator.size):
                for y in range(self.generator.layers):
                    if self.generator.grid[x][z][y] != CellType.EMPTY:
                        self.draw_cube((x, y, z), self.generator.grid[x][z][y])

        # 2D debug overlay
        glDisable(GL_DEPTH_TEST)  # Disable depth test for overlay
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Convert pygame surface to OpenGL texture
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        tex_data = pygame.image.tostring(self.debug_surface, "RGBA", True)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 200, 150, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        
        # Draw textured quad
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(self.display[0]-200, 0)
        glTexCoord2f(0, 1); glVertex2f(self.display[0]-200, 150)
        glTexCoord2f(1, 1); glVertex2f(self.display[0], 150)
        glTexCoord2f(1, 0); glVertex2f(self.display[0], 0)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glDeleteTextures([texture])

        # Restore 3D state
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)
        
        pygame.display.flip()

if __name__ == '__main__':

    print("Gibson: generating structure...")
    generator = MegaStructureGenerator()
    generator.generate_kowloon_style()
    generator.save_structure('kowloon_structure.json')

    visualizer = IsometricVisualizer(generator)
    visualizer.run()
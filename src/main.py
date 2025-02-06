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

class OpenGLVisualizer:
    def __init__(self, generator):
        self.generator = generator
        self.rot_x = 30
        self.rot_y = 45
        self.pos_x = 0
        self.pos_y = 0
        self.pos_z = -30
        self.init_pygame()

    def init_pygame(self):
        pygame.init()
        self.display = (1280, 720)
        pygame.display.set_mode(self.display, DOUBLEBUF|OPENGL)
        gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 100.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
        glEnable(GL_LIGHT0)
        glMaterialfv(GL_FRONT, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))

    def draw_cube(self, position, cell_type):
        x, y, z = position
        glPushMatrix()
        glTranslatef(x, y, z)
        
        colors = {
            CellType.VERTICAL: (0.5, 0.5, 0.5),
            CellType.HORIZONTAL: (0.2, 0.2, 1.0),
            CellType.BRIDGE: (1.0, 0.5, 0.0),
            CellType.OCCUPIED: (0.8, 0.8, 0.8)
        }
        glColor3fv(colors.get(cell_type, (1.0, 1.0, 1.0)))
        
        glutSolidCube(0.8)
        glPopMatrix()

    def draw_connection(self, start, end):
        glBegin(GL_LINES)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3fv(start)
        glVertex3fv(end)
        glEnd()

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(
            self.pos_x, self.pos_y, self.pos_z,
            self.generator.size/2, self.generator.layers/2, self.generator.size/2,
            0, 1, 0
        )
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        # Draw all cells
        for x in range(self.generator.size):
            for z in range(self.generator.size):
                for y in range(self.generator.layers):
                    cell = self.generator.grid[x][z][y]
                    if cell != CellType.EMPTY:
                        self.draw_cube((x, y, z), cell)

        # Draw connections
        for connection in self.generator.connections:
            start = (connection[0][0], connection[0][1], connection[0][2])
            end = (connection[1][0], connection[1][1], connection[1][2])
            self.draw_connection(start, end)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    # Camera controls
                    if event.key == pygame.K_w: self.pos_z += 1
                    if event.key == pygame.K_s: self.pos_z -= 1
                    if event.key == pygame.K_a: self.pos_x -= 1
                    if event.key == pygame.K_d: self.pos_x += 1
                    if event.key == pygame.K_q: self.pos_y += 1
                    if event.key == pygame.K_e: self.pos_y -= 1
                    if event.key == pygame.K_LEFT: self.rot_y -= 5
                    if event.key == pygame.K_RIGHT: self.rot_y += 5
                    if event.key == pygame.K_UP: self.rot_x -= 5
                    if event.key == pygame.K_DOWN: self.rot_x += 5

            self.render()
            pygame.display.flip()
            clock.tick(30)

if __name__ == '__main__':

    # print("Gibson: generating structure...")
    # generator = MegaStructureGenerator()
    # generator.generate_kowloon_style()
    # generator.save_structure('kowloon_structure.json')
    
    print("Gibson: starting visualization...")
    visualizer = OpenGLVisualizer(generator)
    visualizer.run()
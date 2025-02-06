# main.py
import json
import random
import numpy as np
from enum import Enum
from noise import pnoise3
from ursina import *

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

class StructureVisualizer(Entity):
    def __init__(self, generator):
        super().__init__()
        self.generator = generator
        self._setup_camera()
        self._build_mesh()
    
    def _setup_camera(self):
        self.editor_camera = EditorCamera(
            position=(20, 40, -50),
            rotation_x=30,
            fov=90
        )
        DirectionalLight().look_at(Vec3(1,-1,1))

    def _build_mesh(self):
        color_map = {
            CellType.VERTICAL: color.gray,
            CellType.HORIZONTAL: color.blue,
            CellType.BRIDGE: color.orange
        }

        for x in range(self.generator.size):
            for z in range(self.generator.size):
                for y in range(self.generator.layers):
                    cell = self.generator.grid[x][z][y]
                    if cell != CellType.EMPTY:
                        Entity(
                            parent=self,
                            model='cube',
                            position=(x,y,z),
                            color=color_map.get(cell, color.white),
                            texture='white_cube'
                        )

        for connection in self.generator.connections:
            Line(
                parent=self,
                points=[connection[0], connection[1]],
                thickness=0.3,
                color=color.red
            )

if __name__ == '__main__':

    print("Gibson: generating structure...")
    generator = MegaStructureGenerator()
    generator.generate_kowloon_style()
    generator.save_structure('kowloon_structure.json')
    
    print("Gibson: visualizing structure...")
    app = Ursina()
    visualizer = StructureVisualizer(generator)
    app.run()
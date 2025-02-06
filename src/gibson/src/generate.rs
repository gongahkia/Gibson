use noise::{Worley, NoiseFn};
use rand::Rng;
use nalgebra::Vector3;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Megastructure {
    pub grid: Vec<Vec<Vec<Cell>>>,
    pub connections: Vec<(Vector3<usize>, Vector3<usize>)>
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Cell {
    Occupied { room_type: RoomType },
    VerticalPassage,
    HorizontalLink,
    Empty
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RoomType {
    Residential,
    Industrial,
    Utility,
    Commercial
}

pub fn generate_megastructure(width: usize, depth: usize, height: usize) -> Megastructure {

    let mut grid = vec![vec![vec![Cell::Empty; height]; depth]; width];
    let mut connections = Vec::new();
    
    let worley = Worley::new().set_frequency(0.05);
    let mut rng = rand::thread_rng();
    
    for x in (0..width).step_by(10) {
        for z in (0..depth).step_by(10) {
            let y_start = rng.gen_range(0..height/2);
            let y_end = rng.gen_range((height/2)..height);
            
            for y in y_start..y_end {
                grid[x][z][y] = Cell::VerticalPassage;
            }
        }
    }

    for y in 0..height {
        for x in 0..width {
            for z in 0..depth {
                if let Cell::VerticalPassage = grid[x][z][y] {
                    for dx in -1..=1 {
                        for dz in -1..=1 {
                            let nx = x as isize + dx;
                            let nz = z as isize + dz;
                            
                            if nx >= 0 && nz >= 0 && nx < width as isize && nz < depth as isize {
                                let cell = &mut grid[nx as usize][nz as usize][y];
                                if matches!(cell, Cell::Empty) && worley.get([x as f64, z as f64, y as f64]) > 0.5 {
                                    *cell = Cell::HorizontalLink;
                                    connections.push((
                                        Vector3::new(x, y, z),
                                        Vector3::new(nx as usize, y, nz as usize)
                                    ));
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    Megastructure { grid, connections }

}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_generation() {
        let structure = generate_megastructure(50, 50, 20);
        assert!(!structure.grid.is_empty());
        assert!(!structure.connections.is_empty());
    }
}
mod generate;
mod serialize;
mod visualize;

use bevy::prelude::*;
use generate::Megastructure;

fn main() {
    let structure = generate::generate_megastructure(100, 100, 50);
    serialize::save_to_file(&structure, "assets/structure.json")
        .expect("Failed to save structure");
    visualize::visualization_app();
}
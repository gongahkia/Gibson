use std::fs;
use std::path::Path;
use serde::Serialize;
use super::generate::Megastructure;

pub fn save_to_file(structure: &Megastructure, path: impl AsRef<Path>) -> Result<(), Box<dyn std::error::Error>> {
    let json = serde_json::to_string_pretty(structure)?;
    fs::write(path, json)?;
    Ok(())
}

pub fn load_from_file(path: impl AsRef<Path>) -> Result<Megastructure, Box<dyn std::error::Error>> {
    let data = fs::read_to_string(path)?;
    let structure = serde_json::from_str(&data)?;
    Ok(structure)
}
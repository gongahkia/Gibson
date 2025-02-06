use bevy::prelude::*;
use bevy::render::camera::Camera;
use super::generate::Megastructure;

pub fn visualization_app() {

    App::new()
        .add_plugins(DefaultPlugins)
        .add_systems(Startup, setup_scene)
        .add_systems(Update, camera_controls)
        .run();

}

fn setup_scene(

    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,

) {

    commands.spawn(Camera3dBundle {
        transform: Transform::from_xyz(-20.0, 20.0, -20.0)
            .looking_at(Vec3::ZERO, Vec3::Y),
        ..default()
    });
    
    commands.spawn(PointLightBundle {
        transform: Transform::from_xyz(4.0, 8.0, 4.0),
        ..default()
    });

}

fn camera_controls(

    time: Res<Time>,
    keyboard: Res<Input<KeyCode>>,
    mut query: Query<(&mut Transform, &mut Projection), With<Camera>>,
) {

    let speed = 10.0;
    let rotation_speed = 0.5;
    
    for (mut transform, projection) in query.iter_mut() {
        let mut direction = Vec3::ZERO;
        
        if keyboard.pressed(KeyCode::W) {
            direction += transform.forward();
        }
        if keyboard.pressed(KeyCode::S) {
            direction += transform.back();
        }
        if keyboard.pressed(KeyCode::A) {
            direction += transform.left();
        }
        if keyboard.pressed(KeyCode::D) {
            direction += transform.right();
        }
        
        transform.translation += direction * speed * time.delta_seconds();
        
        if keyboard.pressed(KeyCode::Q) {
            transform.rotate_y(rotation_speed * time.delta_seconds());
        }
        if keyboard.pressed(KeyCode::E) {
            transform.rotate_y(-rotation_speed * time.delta_seconds());
        }
    }

}
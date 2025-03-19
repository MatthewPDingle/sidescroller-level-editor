def world_to_screen(world_x, world_y, camera_x, camera_y):
    """Convert world coordinates to screen coordinates"""
    screen_x = world_x - camera_x
    screen_y = world_y - camera_y
    return screen_x, screen_y

def screen_to_world(screen_x, screen_y, camera_x, camera_y):
    """Convert screen coordinates to world coordinates"""
    world_x = screen_x + camera_x
    world_y = screen_y + camera_y
    return world_x, world_y

def world_to_grid(world_x, world_y, cell_size):
    """Convert world coordinates to grid coordinates"""
    grid_x = int(world_x // cell_size)
    grid_y = int(world_y // cell_size)
    return grid_x, grid_y

def grid_to_world(grid_x, grid_y, cell_size):
    """Convert grid coordinates to world coordinates"""
    world_x = grid_x * cell_size
    world_y = grid_y * cell_size
    return world_x, world_y
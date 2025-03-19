import pygame
from editor.config import Config
import math

class Grid:
    def __init__(self):
        self.cell_size = Config.DEFAULT_CELL_SIZE
        self.show_grid = True
    
    def render(self, surface, camera, level_height=None, level_width_pixels=None):
        """Render the grid overlay"""
        # Calculate visible grid area
        start_x = camera.x // self.cell_size * self.cell_size - camera.x
        end_x = Config.WINDOW_WIDTH
        
        # Get level dimensions in pixels
        level_width_pixels = level_width_pixels or Config.WINDOW_WIDTH
        
        # Calculate visible height (limited to foreground height)
        if level_height is None:
            end_y = Config.WINDOW_HEIGHT
        else:
            end_y = min(Config.WINDOW_HEIGHT, Config.UI_PANEL_HEIGHT + level_height)
        
        # Create a transparent surface for the grid
        grid_surface = pygame.Surface(
            (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT),
            pygame.SRCALPHA
        )
        
        # Draw vertical lines
        for x in range(int(start_x), int(end_x + self.cell_size), self.cell_size):
            # Calculate world X position of this grid line
            world_x = x + camera.x
            
            # Only draw grid lines within level bounds
            if world_x <= level_width_pixels:
                pygame.draw.line(
                    grid_surface,
                    Config.GRID_COLOR,
                    (x, Config.UI_PANEL_HEIGHT),
                    (x, end_y)
                )
        
        # Draw horizontal lines
        # Start from UI panel height and don't exceed foreground height
        for y in range(Config.UI_PANEL_HEIGHT, end_y, self.cell_size):
            # Limit horizontal lines to level width
            level_width_screen = level_width_pixels - camera.x
            max_x = min(Config.WINDOW_WIDTH, max(0, level_width_screen))
            
            pygame.draw.line(
                grid_surface,
                Config.GRID_COLOR,
                (0, y),
                (max_x, y)
            )
        
        # Draw the grid surface
        surface.blit(grid_surface, (0, 0))
    
    def set_cell_size(self, size):
        """Set the grid cell size"""
        if size >= 8 and size <= 64:  # Enforce reasonable limits
            self.cell_size = size
    
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid = not self.show_grid
    
    def screen_to_grid(self, screen_x, screen_y, camera):
        """Convert screen coordinates to grid coordinates"""
        world_x = screen_x + camera.x
        world_y = screen_y - Config.UI_PANEL_HEIGHT
        grid_x = int(world_x // self.cell_size)
        grid_y = int(world_y // self.cell_size)
        return grid_x, grid_y
    
    def grid_to_screen(self, grid_x, grid_y, camera):
        """Convert grid coordinates to screen coordinates"""
        world_x = grid_x * self.cell_size
        world_y = grid_y * self.cell_size
        screen_x = world_x - camera.x
        screen_y = world_y + Config.UI_PANEL_HEIGHT
        return screen_x, screen_y
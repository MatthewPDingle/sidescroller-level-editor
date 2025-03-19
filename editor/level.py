import pygame
from editor.config import Config

class Level:
    def __init__(self):
        # Level dimensions
        self.cell_size = Config.DEFAULT_CELL_SIZE
        self.width = Config.DEFAULT_LEVEL_WIDTH
        self.height = Config.DEFAULT_LEVEL_HEIGHT
        
        # Calculate pixel dimensions
        self.width_pixels = self.width * self.cell_size
        self.height_pixels = self.height * self.cell_size
        
        # Level elements
        self.platforms = []
        self.ground_blocks = []
        self.enemies = []
        
        # Asset placeholders
        self.background = None
        self.foreground = None
        self.platform_image = None
        self.enemy_images = {}
        
        # Paths to background and foreground images
        self.bg_path = None
        self.fg_path = None
    
    def resize(self, width, height):
        """Resize the level"""
        self.width = max(1, width)
        self.height = max(1, height)
        self.width_pixels = self.width * self.cell_size
        self.height_pixels = self.height * self.cell_size
    
    def set_cell_size(self, size):
        """Update cell size and recalculate dimensions"""
        self.cell_size = size
        self.width_pixels = self.width * self.cell_size
        self.height_pixels = self.height * self.cell_size
    
    def add_platform(self, x, y, width, height):
        """Add a platform to the level"""
        platform = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }
        self.platforms.append(platform)
    
    def add_ground(self, x, y, width=1):
        """Add a ground block to the level"""
        # Check if we can merge with an adjacent ground block
        for i, ground in enumerate(self.ground_blocks):
            if ground['y'] == y:  # Same row
                # Check if adjacent to the right
                if ground['x'] + ground['width'] == x:
                    self.ground_blocks[i]['width'] += width
                    return
                # Check if adjacent to the left
                elif x + width == ground['x']:
                    self.ground_blocks[i]['x'] = x
                    self.ground_blocks[i]['width'] += width
                    return
        
        # If no merge happened, add a new ground block
        ground = {
            'x': x,
            'y': y,
            'width': width
        }
        self.ground_blocks.append(ground)
    
    def add_enemy(self, x, y, enemy_type="armadillo"):
        """Add an enemy to the level"""
        enemy = {
            'x': x,
            'y': y,
            'type': enemy_type
        }
        self.enemies.append(enemy)
    
    def delete_at(self, grid_x, grid_y):
        """Delete any elements at the given grid position"""
        # Check and delete platforms
        platforms_to_remove = []
        for i, platform in enumerate(self.platforms):
            if (platform['x'] <= grid_x < platform['x'] + platform['width'] and
                platform['y'] <= grid_y < platform['y'] + platform['height']):
                platforms_to_remove.append(i)
        
        # Remove platforms (in reverse order to avoid index issues)
        for i in sorted(platforms_to_remove, reverse=True):
            self.platforms.pop(i)
        
        # Check and delete ground blocks
        grounds_to_remove = []
        for i, ground in enumerate(self.ground_blocks):
            if (ground['x'] <= grid_x < ground['x'] + ground['width'] and
                ground['y'] == grid_y):
                # Split the ground block if deleting from middle
                if ground['x'] < grid_x and grid_x < ground['x'] + ground['width'] - 1:
                    # Create new block for right side
                    right_width = ground['x'] + ground['width'] - grid_x - 1
                    if right_width > 0:
                        self.ground_blocks.append({
                            'x': grid_x + 1,
                            'y': ground['y'],
                            'width': right_width
                        })
                    
                    # Resize the original to exclude the deleted cell
                    self.ground_blocks[i]['width'] = grid_x - ground['x']
                    
                    # Skip the removal if we've handled it by resizing
                    if self.ground_blocks[i]['width'] > 0:
                        continue
                
                grounds_to_remove.append(i)
        
        # Remove ground blocks (in reverse order)
        for i in sorted(grounds_to_remove, reverse=True):
            self.ground_blocks.pop(i)
        
        # Check and delete enemies
        enemies_to_remove = []
        for i, enemy in enumerate(self.enemies):
            if enemy['x'] == grid_x and enemy['y'] == grid_y:
                enemies_to_remove.append(i)
        
        # Remove enemies (in reverse order)
        for i in sorted(enemies_to_remove, reverse=True):
            self.enemies.pop(i)
        
        return bool(platforms_to_remove or grounds_to_remove or enemies_to_remove)
    
    def clear(self):
        """Clear all level elements"""
        self.platforms = []
        self.ground_blocks = []
        self.enemies = []
    
    def to_dict(self):
        """Convert level data to a dictionary"""
        # Create level dictionary following the design spec structure
        level_data = {
            'dimensions': {
                'width': self.width,
                'height': self.height,
                'cell_size': self.cell_size,
                'width_pixels': self.width_pixels,
                'height_pixels': self.height_pixels
            },
            'platforms': self.platforms,
            'ground_blocks': self.ground_blocks,
            'enemies': self.enemies,
            'assets': {
                'background': self.bg_path if hasattr(self, 'bg_path') else None,
                'foreground': self.fg_path if hasattr(self, 'fg_path') else None,
                'platform_image': 'resources/graphics/platform.png',
                'enemy_types': list(self.enemy_images.keys()) if hasattr(self, 'enemy_images') else []
            },
            'metadata': {
                'created': pygame.time.get_ticks(),
                'editor_version': '1.0'
            }
        }
        return level_data
    
    def from_dict(self, data):
        """Load level data from a dictionary"""
        if 'dimensions' in data:
            dim = data['dimensions']
            self.width = dim.get('width', Config.DEFAULT_LEVEL_WIDTH)
            self.height = dim.get('height', Config.DEFAULT_LEVEL_HEIGHT)
            self.cell_size = dim.get('cell_size', Config.DEFAULT_CELL_SIZE)
            self.width_pixels = self.width * self.cell_size
            self.height_pixels = self.height * self.cell_size
        
        self.platforms = data.get('platforms', [])
        self.ground_blocks = data.get('ground_blocks', [])
        self.enemies = data.get('enemies', [])
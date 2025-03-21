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
        
        # Parallax scroll rates
        self.fg_scroll_rate = 1.0  # Foreground is always 1.0
        self.bg_scroll_rate = 0.2  # Default background scroll rate
    
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
    
    def add_enemy(self, x, y, enemy_type="armadillo_warrior"):
        """Add an enemy to the level"""
        enemy = {
            'x': x,
            'y': y,
            'type': enemy_type,
            'direction': 'south',  # Default direction
            'animation_frame': 3   # 4th frame (0-indexed) from 3rd row
        }
        self.enemies.append(enemy)
        
        # Make sure to load the enemy image if it's not already loaded
        if enemy_type not in self.enemy_images:
            try:
                from editor.utils.assets import load_sprite_sheet
                enemy_path = f"resources/graphics/characters/{enemy_type}_ss.png"
                
                # First, get the actual dimensions of the spritesheet
                sheet = pygame.image.load(enemy_path).convert_alpha()
                sheet_width = sheet.get_width()
                sheet_height = sheet.get_height()
                
                # Calculate the true frame size based on a 4x4 grid in the sprite sheet
                # This accounts for character sprites larger than 32x32
                sprite_width = sheet_width // 4
                sprite_height = sheet_height // 4
                
                print(f"[DEBUG] Loading {enemy_type} sprite sheet: {sheet_width}x{sheet_height}, frame size: {sprite_width}x{sprite_height}")
                
                # Load the sprite sheet with the correct frame size
                sprite_sheet = load_sprite_sheet(enemy_path, sprite_width, sprite_height)
                
                # Standard setup for these sprite sheets - 4x4 grid with 16 frames
                frames_per_row = 4
                frame_index = 2 * frames_per_row + 3  # 3rd row (index 2) * frames per row + 4th frame (index 3)
                
                if len(sprite_sheet) > frame_index:
                    self.enemy_images[enemy_type] = sprite_sheet[frame_index]
                else:
                    # Fallback to first frame if out of bounds
                    self.enemy_images[enemy_type] = sprite_sheet[0]
                    print(f"[DEBUG] Using fallback frame for {enemy_type}. Sheet has {len(sprite_sheet)} frames.")
            except Exception as e:
                print(f"[ERROR] Could not load enemy image for {enemy_type}: {e}")
                # Create a placeholder
                placeholder = pygame.Surface((32, 32))
                placeholder.fill((255, 0, 255))  # Magenta for missing textures
                self.enemy_images[enemy_type] = placeholder
    
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
        # Function to convert absolute paths to relative paths
        def make_relative_path(path):
            if not path:
                return None
                
            # Convert backslashes to forward slashes for consistency
            path = path.replace("\\", "/")
            
            # Extract the relative path starting from "resources"
            if "resources" in path:
                # Find the index of "resources" in the path
                resources_index = path.find("resources")
                if resources_index != -1:
                    return path[resources_index:]
            
            # If we can't find "resources" in the path, return the original path
            return path
            
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
                'background': make_relative_path(self.bg_path) if hasattr(self, 'bg_path') else None,
                'foreground': make_relative_path(self.fg_path) if hasattr(self, 'fg_path') else None,
                'platform_image': 'resources/graphics/platform.png',
                'enemy_types': list(self.enemy_images.keys()) if hasattr(self, 'enemy_images') else []
            },
            'parallax': {
                'fg_scroll_rate': getattr(self, 'fg_scroll_rate', 1.0),
                'bg_scroll_rate': getattr(self, 'bg_scroll_rate', 0.2),
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
        
        # Load parallax scroll rates
        if 'parallax' in data:
            parallax = data['parallax']
            self.fg_scroll_rate = parallax.get('fg_scroll_rate', 1.0)
            self.bg_scroll_rate = parallax.get('bg_scroll_rate', 0.2)
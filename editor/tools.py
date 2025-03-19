import pygame
from editor.config import Config

class Tool:
    def __init__(self, level, grid):
        self.level = level
        self.grid = grid
        self.preview = None
    
    def handle_event(self, event, camera):
        """Handle input events for the tool"""
        pass
    
    def render_preview(self, surface, camera):
        """Render a preview of the tool's action"""
        pass

class PlatformTool(Tool):
    def __init__(self, level, grid):
        super().__init__(level, grid)
        self.start_pos = None
        self.dragging = False
    
    def handle_event(self, event, camera):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Convert mouse position to grid coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Skip if mouse is in UI area
            if mouse_y < Config.UI_PANEL_HEIGHT:
                return
                
            grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
            
            # Ensure within level bounds
            if grid_x >= self.level.width or grid_y >= self.level.height:
                return
            
            # Start platform placement
            self.start_pos = (grid_x, grid_y)
            self.dragging = True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging and self.start_pos:
                # Convert mouse position to grid coordinates
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Skip if mouse is in UI area (use last valid position instead)
                if mouse_y < Config.UI_PANEL_HEIGHT:
                    # Use edge of screen or last valid position
                    mouse_y = Config.UI_PANEL_HEIGHT
                
                end_x, end_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
                
                # Constrain to level bounds
                end_x = max(0, min(end_x, self.level.width - 1))
                end_y = max(0, min(end_y, self.level.height - 1))
                
                # Ensure start_x <= end_x and start_y <= end_y
                start_x, start_y = self.start_pos
                if start_x > end_x:
                    start_x, end_x = end_x, start_x
                if start_y > end_y:
                    start_y, end_y = end_y, start_y
                
                # Add platform with proper dimensions
                width = end_x - start_x + 1
                height = end_y - start_y + 1
                if width > 0 and height > 0:
                    self.level.add_platform(start_x, start_y, width, height)
                
                # Reset state
                self.dragging = False
                self.start_pos = None
                self.preview = None
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Update preview
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Skip if mouse is in UI area (use edge of panel)
            if mouse_y < Config.UI_PANEL_HEIGHT:
                mouse_y = Config.UI_PANEL_HEIGHT
                
            end_x, end_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
            
            # Constrain to level bounds
            end_x = max(0, min(end_x, self.level.width - 1))
            end_y = max(0, min(end_y, self.level.height - 1))
            
            # Ensure start_x <= end_x and start_y <= end_y
            start_x, start_y = self.start_pos
            if start_x > end_x:
                start_x, end_x = end_x, start_x
            if start_y > end_y:
                start_y, end_y = end_y, start_y
            
            # Create preview rectangle
            width = end_x - start_x + 1
            height = end_y - start_y + 1
            self.preview = (start_x, start_y, width, height)
    
    def render_preview(self, surface, camera):
        if self.preview and self.dragging:
            x, y, width, height = self.preview
            screen_x, screen_y = self.grid.grid_to_screen(x, y, camera)
            width_px = width * self.grid.cell_size
            height_px = height * self.grid.cell_size
            
            # Create a transparent surface for the preview
            preview_surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
            preview_surface.fill((150, 75, 0, 128))  # Semi-transparent brown
            
            # Draw the preview
            surface.blit(preview_surface, (screen_x, screen_y))

class GroundTool(Tool):
    def __init__(self, level, grid):
        super().__init__(level, grid)
        self.last_pos = None
    
    def handle_event(self, event, camera):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Convert mouse position to grid coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Skip if mouse is in UI area
            if mouse_y < Config.UI_PANEL_HEIGHT:
                return
                
            grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
            
            # Ensure within level bounds
            if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
                return
            
            # Add ground block
            self.level.add_ground(grid_x, grid_y)
            self.last_pos = (grid_x, grid_y)
        
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            # Convert mouse position to grid coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Skip if mouse is in UI area
            if mouse_y < Config.UI_PANEL_HEIGHT:
                return
                
            grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
            
            # Ensure within level bounds
            if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
                return
            
            # Check if we've moved to a new cell
            if self.last_pos != (grid_x, grid_y):
                # Add ground block
                self.level.add_ground(grid_x, grid_y)
                self.last_pos = (grid_x, grid_y)
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.last_pos = None
    
    def render_preview(self, surface, camera):
        # Get current mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Skip if mouse is in UI area
        if mouse_y < Config.UI_PANEL_HEIGHT:
            return
            
        grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
        
        # Skip if outside level bounds
        if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
            return
            
        screen_x, screen_y = self.grid.grid_to_screen(grid_x, grid_y, camera)
        
        # Create a transparent surface for the preview
        preview_surface = pygame.Surface((self.grid.cell_size, self.grid.cell_size), pygame.SRCALPHA)
        preview_surface.fill((70, 40, 0, 128))  # Semi-transparent brown
        
        # Draw the preview
        surface.blit(preview_surface, (screen_x, screen_y))

class EnemyTool(Tool):
    def __init__(self, level, grid):
        super().__init__(level, grid)
        self.enemy_type = "armadillo"  # Default enemy type
    
    def handle_event(self, event, camera):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Convert mouse position to grid coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Skip if mouse is in UI area
            if mouse_y < Config.UI_PANEL_HEIGHT:
                return
                
            grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
            
            # Ensure within level bounds
            if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
                return
            
            # Add enemy
            self.level.add_enemy(grid_x, grid_y, self.enemy_type)
    
    def set_enemy_type(self, enemy_type):
        """Set the type of enemy to place"""
        self.enemy_type = enemy_type
    
    def render_preview(self, surface, camera):
        # Get current mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Skip if mouse is in UI area
        if mouse_y < Config.UI_PANEL_HEIGHT:
            return
            
        grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
        
        # Skip if outside level bounds
        if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
            return
            
        screen_x, screen_y = self.grid.grid_to_screen(grid_x, grid_y, camera)
        
        # Draw the enemy preview
        if self.enemy_type in self.level.enemy_images:
            sprite = self.level.enemy_images[self.enemy_type]
            # Bottom-center alignment
            sprite_x = screen_x - sprite.get_width() // 2 + self.grid.cell_size // 2
            sprite_y = screen_y + self.grid.cell_size - sprite.get_height()
            
            # Draw with transparency
            preview_sprite = sprite.copy()
            preview_sprite.set_alpha(128)
            surface.blit(preview_sprite, (sprite_x, sprite_y))
        else:
            # Fallback preview
            preview_surface = pygame.Surface((self.grid.cell_size, self.grid.cell_size), pygame.SRCALPHA)
            preview_surface.fill((255, 0, 0, 128))  # Semi-transparent red
            surface.blit(preview_surface, (screen_x, screen_y))

class DeleteTool(Tool):
    def __init__(self, level, grid):
        super().__init__(level, grid)
    
    def handle_event(self, event, camera):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Convert mouse position to grid coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Skip if mouse is in UI area
            if mouse_y < Config.UI_PANEL_HEIGHT:
                return
                
            grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
            
            # Ensure within level bounds
            if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
                return
            
            # Delete elements at this position
            self.level.delete_at(grid_x, grid_y)
        
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            # Convert mouse position to grid coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Skip if mouse is in UI area
            if mouse_y < Config.UI_PANEL_HEIGHT:
                return
                
            grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
            
            # Ensure within level bounds
            if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
                return
            
            # Delete elements at this position
            self.level.delete_at(grid_x, grid_y)
    
    def render_preview(self, surface, camera):
        # Get current mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Skip if mouse is in UI area
        if mouse_y < Config.UI_PANEL_HEIGHT:
            return
            
        grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
        
        # Skip if outside level bounds
        if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
            return
            
        screen_x, screen_y = self.grid.grid_to_screen(grid_x, grid_y, camera)
        
        # Draw a red X as delete preview
        size = self.grid.cell_size
        pygame.draw.line(surface, (255, 0, 0, 128), (screen_x, screen_y), (screen_x + size, screen_y + size), 2)
        pygame.draw.line(surface, (255, 0, 0, 128), (screen_x + size, screen_y), (screen_x, screen_y + size), 2)

class ToolManager:
    def __init__(self, level, grid):
        self.level = level
        self.grid = grid
        
        # Create tools
        self.platform_tool = PlatformTool(level, grid)
        self.ground_tool = GroundTool(level, grid)
        self.enemy_tool = EnemyTool(level, grid)
        self.delete_tool = DeleteTool(level, grid)
        
        # Set default tool
        self.current_tool = self.platform_tool
    
    def set_tool(self, tool_name):
        """Set the current tool"""
        if tool_name == "platform":
            self.current_tool = self.platform_tool
        elif tool_name == "ground":
            self.current_tool = self.ground_tool
        elif tool_name == "enemy":
            self.current_tool = self.enemy_tool
        elif tool_name == "delete":
            self.current_tool = self.delete_tool
    
    def handle_event(self, event, camera):
        """Pass events to the current tool"""
        self.current_tool.handle_event(event, camera)
    
    def render_preview(self, surface, camera):
        """Render the current tool's preview"""
        self.current_tool.render_preview(surface, camera)
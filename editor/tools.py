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
        self.enemy_type = "armadillo_warrior"  # Default enemy type
        self.character_selector = None  # Will be set by ToolManager
    
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
        # Save current clip area and remove any clipping to ensure the preview
        # can extend beyond grid boundaries
        original_clip = surface.get_clip()
        surface.set_clip(None)
        
        # Get current mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Skip if mouse is in UI area
        if mouse_y < Config.UI_PANEL_HEIGHT:
            surface.set_clip(original_clip)
            return
            
        grid_x, grid_y = self.grid.screen_to_grid(mouse_x, mouse_y, camera)
        
        # Skip if outside level bounds
        if grid_x >= self.level.width or grid_y >= self.level.height or grid_x < 0 or grid_y < 0:
            surface.set_clip(original_clip)
            return
            
        screen_x, screen_y = self.grid.grid_to_screen(grid_x, grid_y, camera)
        
        # Draw the enemy preview
        if self.enemy_type in self.level.enemy_images:
            sprite = self.level.enemy_images[self.enemy_type]
            
            # Position sprite so bottom-center aligns with grid cell position
            adjusted_x = screen_x + (self.grid.cell_size // 2) - (sprite.get_width() // 2)
            adjusted_y = screen_y + self.grid.cell_size - sprite.get_height()
            
            # Draw with transparency (entire sprite, regardless of grid boundaries)
            preview_sprite = sprite.copy()
            preview_sprite.set_alpha(128)
            
            # Add a visual indicator at the grid cell position
            marker = pygame.Surface((6, 6))
            marker.fill((255, 255, 0))  # Yellow marker
            
            # Display the sprite and marker
            surface.blit(preview_sprite, (adjusted_x, adjusted_y))
            surface.blit(marker, (screen_x + self.grid.cell_size//2 - 3, screen_y + self.grid.cell_size - 3))
            
            # Draw a small outline around the grid cell for clarity
            pygame.draw.rect(surface, (255, 255, 0), 
                           (screen_x, screen_y, self.grid.cell_size, self.grid.cell_size), 1)
        else:
            # Fallback preview
            preview_surface = pygame.Surface((self.grid.cell_size, self.grid.cell_size), pygame.SRCALPHA)
            preview_surface.fill((255, 0, 0, 128))  # Semi-transparent red
            surface.blit(preview_surface, (screen_x, screen_y))
        
        # Restore original clip area
        surface.set_clip(original_clip)

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

class CharacterSelector:
    """A UI component for selecting character types"""
    def __init__(self, level):
        self.level = level
        self.characters = []
        self.selected_index = 0
        self.visible = False
        self.rect = pygame.Rect(0, 0, 200, 300)  # Default size and position
        self.scroll_offset = 0
        self.max_visible = 6
        
        # Load character list
        from editor.utils.assets import scan_character_spritesheets
        self.characters = scan_character_spritesheets()
        
        # Load preview images
        self.load_preview_images()
        
        # Default to first character if available
        if self.characters:
            self.selected_character = self.characters[0]
        else:
            self.selected_character = {"name": "armadillo_warrior", "path": ""}
    
    def load_preview_images(self):
        """Load preview images for all characters"""
        for char in self.characters:
            try:
                # Load the sprite sheet for preview
                sheet = pygame.image.load(char["path"]).convert_alpha()
                sheet_width = sheet.get_width()
                sheet_height = sheet.get_height()
                
                # Calculate the true frame size based on a 4x4 grid in the sprite sheet
                sprite_width = sheet_width // 4
                sprite_height = sheet_height // 4
                
                # Get the 4th frame from the 3rd row (south-facing, standing position)
                frames_per_row = 4
                frame_index = 2 * frames_per_row + 3  # 3rd row (index 2) * frames per row + 4th frame (index 3)
                
                frame_x = (frame_index % 4) * sprite_width
                frame_y = (frame_index // 4) * sprite_height
                
                # Extract the correct frame
                frame = sheet.subsurface((frame_x, frame_y, sprite_width, sprite_height))
                
                # Scale down to 25% of original size for the menu preview
                scaled_width = sprite_width // 4
                scaled_height = sprite_height // 4
                char["preview"] = pygame.transform.smoothscale(frame, (scaled_width, scaled_height))
                
                print(f"[DEBUG] Character preview for {char['name']}: original {sprite_width}x{sprite_height}, scaled {scaled_width}x{scaled_height}")
            except Exception as e:
                print(f"[ERROR] Could not load preview for {char['name']}: {e}")
                # Create a placeholder
                placeholder = pygame.Surface((32, 32))
                placeholder.fill((255, 0, 255))  # Magenta
                char["preview"] = placeholder
    
    def toggle_visibility(self):
        """Toggle the visibility of the character selector"""
        self.visible = not self.visible
    
    def get_selected_character(self):
        """Get currently selected character"""
        if self.characters and self.selected_index < len(self.characters):
            return self.characters[self.selected_index]["name"]
        return "armadillo_warrior"  # Default fallback
    
    def handle_event(self, event, tool):
        """Handle events for the character selector"""
        if not self.visible:
            # Check if the character hotkey was pressed to show selector
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                self.toggle_visibility()
                # Position selector near mouse
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.rect.x = min(mouse_x, pygame.display.get_surface().get_width() - self.rect.width)
                self.rect.y = min(mouse_y, pygame.display.get_surface().get_height() - self.rect.height)
                return True
            return False
        
        # When visible, handle interactions
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.visible = False
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # If clicked outside selector, hide it
            if not self.rect.collidepoint(mouse_pos):
                self.visible = False
                return True
            
            # Check for character selection
            for i in range(min(self.max_visible, len(self.characters) - self.scroll_offset)):
                idx = i + self.scroll_offset
                item_rect = pygame.Rect(
                    self.rect.x + 10, 
                    self.rect.y + 40 + i * 40,
                    self.rect.width - 20,
                    36
                )
                
                if item_rect.collidepoint(mouse_pos):
                    self.selected_index = idx
                    tool.set_enemy_type(self.characters[idx]["name"])
                    self.visible = False  # Auto-hide after selection
                    return True
            
            # Handle scrolling buttons
            up_btn_rect = pygame.Rect(self.rect.x + self.rect.width - 40, self.rect.y + 10, 30, 20)
            down_btn_rect = pygame.Rect(self.rect.x + self.rect.width - 40, 
                                       self.rect.y + self.rect.height - 30, 30, 20)
            
            if up_btn_rect.collidepoint(mouse_pos) and self.scroll_offset > 0:
                self.scroll_offset -= 1
                return True
            elif down_btn_rect.collidepoint(mouse_pos) and \
                 self.scroll_offset < len(self.characters) - self.max_visible:
                self.scroll_offset += 1
                return True
        
        elif event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                if event.y > 0 and self.scroll_offset > 0:  # Scroll up
                    self.scroll_offset -= 1
                    return True
                elif event.y < 0 and self.scroll_offset < len(self.characters) - self.max_visible:  # Scroll down
                    self.scroll_offset += 1
                    return True
        
        return True
    
    def render(self, surface):
        """Render the character selector if visible"""
        if not self.visible or not self.characters:
            return
        
        # Draw the selector panel
        panel_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (50, 50, 50, 230), 
                         (0, 0, self.rect.width, self.rect.height))
        pygame.draw.rect(panel_surface, (150, 150, 150, 200), 
                         (0, 0, self.rect.width, self.rect.height), 2)
        
        # Draw title
        font_title = pygame.font.SysFont(None, 24)
        title_text = font_title.render("Select Character", True, (255, 255, 255))
        panel_surface.blit(title_text, (self.rect.width // 2 - title_text.get_width() // 2, 10))
        
        # Draw character options
        font = pygame.font.SysFont(None, 20)
        for i in range(min(self.max_visible, len(self.characters) - self.scroll_offset)):
            idx = i + self.scroll_offset
            char = self.characters[idx]
            
            # Draw item background (highlight if selected)
            item_rect = pygame.Rect(10, 40 + i * 40, self.rect.width - 20, 36)
            if idx == self.selected_index:
                pygame.draw.rect(panel_surface, (80, 120, 200, 200), item_rect)
            else:
                pygame.draw.rect(panel_surface, (60, 60, 60, 200), item_rect)
            pygame.draw.rect(panel_surface, (180, 180, 180, 150), item_rect, 1)
            
            # Draw character preview image
            if "preview" in char:
                # Center the preview vertically and leave a small margin from the left
                preview_image = char["preview"]
                preview_left_margin = 10
                
                # Calculate placement to center vertically in the item
                preview_y = item_rect.centery - preview_image.get_height() // 2
                preview_rect = preview_image.get_rect(topleft=(item_rect.left + preview_left_margin, preview_y))
                panel_surface.blit(preview_image, preview_rect)
                
                # Adjust text position based on the preview size
                text_left_margin = preview_left_margin + preview_image.get_width() + 10
            else:
                # No preview image, use default margin
                text_left_margin = 45
            
            # Draw character name with adjusted position
            text = font.render(char["display_name"], True, (255, 255, 255))
            text_rect = text.get_rect(midleft=(item_rect.left + text_left_margin, item_rect.centery))
            panel_surface.blit(text, text_rect)
        
        # Draw scroll indicators if needed
        if self.scroll_offset > 0:
            # Up arrow
            up_btn_rect = pygame.Rect(self.rect.width - 40, 10, 30, 20)
            pygame.draw.rect(panel_surface, (80, 80, 80, 200), up_btn_rect)
            pygame.draw.rect(panel_surface, (180, 180, 180, 150), up_btn_rect, 1)
            pygame.draw.polygon(panel_surface, (255, 255, 255),
                              [(up_btn_rect.centerx, up_btn_rect.top + 5),
                               (up_btn_rect.centerx - 8, up_btn_rect.bottom - 5),
                               (up_btn_rect.centerx + 8, up_btn_rect.bottom - 5)])
        
        if self.scroll_offset < len(self.characters) - self.max_visible:
            # Down arrow
            down_btn_rect = pygame.Rect(self.rect.width - 40, self.rect.height - 30, 30, 20)
            pygame.draw.rect(panel_surface, (80, 80, 80, 200), down_btn_rect)
            pygame.draw.rect(panel_surface, (180, 180, 180, 150), down_btn_rect, 1)
            pygame.draw.polygon(panel_surface, (255, 255, 255),
                              [(down_btn_rect.centerx, down_btn_rect.bottom - 5),
                               (down_btn_rect.centerx - 8, down_btn_rect.top + 5),
                               (down_btn_rect.centerx + 8, down_btn_rect.top + 5)])
        
        # Draw instructions
        help_text = font.render("Press ESC to close", True, (200, 200, 200))
        help_rect = help_text.get_rect(centerx=self.rect.width // 2, bottom=self.rect.height - 8)
        panel_surface.blit(help_text, help_rect)
        
        # Draw the panel
        surface.blit(panel_surface, (self.rect.x, self.rect.y))

class ToolManager:
    def __init__(self, level, grid):
        self.level = level
        self.grid = grid
        
        # Create tools
        self.platform_tool = PlatformTool(level, grid)
        self.ground_tool = GroundTool(level, grid)
        self.enemy_tool = EnemyTool(level, grid)
        self.delete_tool = DeleteTool(level, grid)
        
        # Create character selector
        self.character_selector = CharacterSelector(level)
        self.enemy_tool.character_selector = self.character_selector
        
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
        # First check if character selector needs to handle the event
        if isinstance(self.current_tool, EnemyTool):
            if self.character_selector.visible:
                if self.character_selector.handle_event(event, self.current_tool):
                    return True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                # Toggle character selector
                self.character_selector.handle_event(event, self.current_tool)
                return True
                
        # Then pass to the current tool
        self.current_tool.handle_event(event, camera)
    
    def render_preview(self, surface, camera):
        """Render the current tool's preview"""
        self.current_tool.render_preview(surface, camera)
        
        # Render character selector if visible
        if isinstance(self.current_tool, EnemyTool) and self.character_selector.visible:
            self.character_selector.render(surface)
#!/usr/bin/env python3
import pygame
import sys
import os
from pygame.locals import *  # Import all pygame constants

# Initialize pygame
pygame.init()

# Define application states for the state machine
class AppState:
    WELCOME_SCREEN = "welcome_screen"  # Main menu
    LEVEL_EDITOR = "level_editor"      # Level editing mode
    EXITING = "exiting"                # Application is closing

# Global application state - accessible from anywhere
current_app_state = AppState.WELCOME_SCREEN
state_change_requested = None  # Used to request a state change

# Import after pygame is initialized
from editor.config import Config
from editor.grid import Grid
from editor.camera import Camera
from editor.level import Level
from editor.tools import ToolManager
from editor.ui import UIManager, ModalDialog, SaveDialog
# Import the new LoadLevelDialog for loading levels
from editor.ui import LoadLevelDialog

from editor.file_manager import FileManager

class LevelEditor:
    # Class instance for reference
    instance = None
    
    def __init__(self):
        # IMPORTANT: Set as class instance before creating any subsystems
        LevelEditor.instance = self
        print(f"[LOG] LevelEditor instance set: {self}")
        
        # Set up display
        self.screen = pygame.display.set_mode(
            (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("Sidescroller Level Editor")
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        
        # Initialize subsystems
        self.grid = Grid()
        self.level = Level()
        self.camera = Camera(self.level)
        self.tool_manager = ToolManager(self.level, self.grid)
        self.ui_manager = UIManager(self.tool_manager, self.level, self.grid, self.camera)
        self.file_manager = FileManager(self.level)
        
        # Level editor state
        self.has_loaded_level = False
        self.should_show_new_level_dialog = False
        
        # Main loop flag
        self.running = True
        
        # Font for welcome screen
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 32)
    
    
    def load_assets(self, bg_path=None, fg_path=None):
        """Load assets for the level editor
        
        Args:
            bg_path: Path to background image (optional)
            fg_path: Path to foreground image (optional)
        """
        # Store background and foreground paths
        if bg_path:
            self.level.bg_path = bg_path
        else:
            bg_path = os.path.join("resources", "graphics", "background_2048_512.png")
            
        if fg_path:
            self.level.fg_path = fg_path
        else:
            fg_path = os.path.join("resources", "graphics", "foreground_2048_512.png")
        
        # Load background image
        if os.path.exists(bg_path):
            self.level.background = pygame.image.load(bg_path).convert_alpha()
            self.level.bg_path = bg_path
        else:
            print(f"Warning: Could not load background image from {bg_path}")
            # Create a placeholder background
            self.level.background = pygame.Surface((2048, 512))
            self.level.background.fill((100, 150, 200))
            self.level.bg_path = None
        
        # Load foreground image
        if os.path.exists(fg_path):
            self.level.foreground = pygame.image.load(fg_path).convert_alpha()
            self.level.fg_path = fg_path
            
            # Adjust level height based on foreground height
            fg_height = self.level.foreground.get_height()
            self.level.height = fg_height // self.level.cell_size
            self.level.height_pixels = fg_height
        else:
            print(f"Warning: Could not load foreground image from {fg_path}")
            # Create a placeholder foreground
            self.level.foreground = pygame.Surface((2048, 512))
            self.level.foreground.fill((50, 100, 50, 128))
            self.level.fg_path = None
        
        # Only adjust level width based on foreground width for new levels
        # If loading an existing level, use the saved width from the level file
        if self.level.foreground:
            fg_width = self.level.foreground.get_width()
            
            if not self.has_loaded_level:
                old_width = self.level.width
                self.level.width = fg_width // self.level.cell_size
                self.level.width_pixels = fg_width
                print(f"[DEBUG] Adjusting level width from {old_width} to {self.level.width} cells (new level)")
            else:
                print(f"[DEBUG] Preserving level width at {self.level.width} cells (loaded level)")
        
        # Load platform image
        platform_path = os.path.join("resources", "graphics", "platform.png")
        if os.path.exists(platform_path):
            self.level.platform_image = pygame.image.load(platform_path).convert_alpha()
        else:
            print(f"Warning: Could not load platform image from {platform_path}")
            # Create a placeholder platform
            self.level.platform_image = pygame.Surface((32, 32))
            self.level.platform_image.fill((150, 75, 0))
        
        # Load enemy sprites
        # For now, just create placeholder sprites
        self.level.enemy_images = {}
        
        armadillo_path = os.path.join("resources", "graphics", "armadillo_warrior_ss.png")
        if os.path.exists(armadillo_path):
            self.level.enemy_images["armadillo"] = self.load_sprite_sheet(armadillo_path, 32, 32)[0]
        
        scientist_path = os.path.join("resources", "graphics", "scientist_ss.png")
        if os.path.exists(scientist_path):
            self.level.enemy_images["scientist"] = self.load_sprite_sheet(scientist_path, 32, 32)[0]
            
        # Set has_loaded_level flag
        if self.level.background and self.level.foreground:
            self.has_loaded_level = True
            self.show_new_level_dialog = False

    def load_sprite_sheet(self, path, width, height):
        if os.path.exists(path):
            sheet = pygame.image.load(path).convert_alpha()
            # For now, just return the first frame
            return [sheet.subsurface((0, 0, width, height))]
        else:
            print(f"Warning: Could not load sprite sheet from {path}")
            # Create a placeholder sprite
            sprite = pygame.Surface((width, height))
            sprite.fill((255, 0, 255))
            return [sprite]
    
    def handle_editor_events(self):
        global current_app_state, state_change_requested

        # Check for state change request BEFORE processing any events
        if state_change_requested:
            print(f"[STATE] Change requested before event processing: {state_change_requested}")
            return

        for event in pygame.event.get():
            # Check for application exit
            if event.type == pygame.QUIT:
                state_change_requested = AppState.EXITING
                return

            # TEST HOTKEY: 'w' key to force welcome screen
            if event.type == pygame.KEYDOWN and event.key == pygame.K_w:
                print("[HOTKEY] 'w' key pressed - forcing transition to welcome screen")
                current_app_state = AppState.WELCOME_SCREEN
                self.ui_manager.active_dialog = None  # Clear any active dialogs
                return

            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h),
                    pygame.RESIZABLE
                )
                Config.WINDOW_WIDTH = event.w
                Config.WINDOW_HEIGHT = event.h

            # Special handling for our custom state change event
            if event.type == USEREVENT:
                print("[STATE] Received custom state change event in handle_editor_events")
                print(f"[STATE] Event dict: {event.__dict__}")
                print(f"[STATE] Current state_change_requested value: {state_change_requested}")

                # Direct unconditional transition back to welcome screen
                current_app_state = AppState.WELCOME_SCREEN
                state_change_requested = None

                if hasattr(self, 'ui_manager') and self.ui_manager:
                    self.ui_manager.active_dialog = None

                print("[STATE] Exiting event loop to return to main loop")
                return

            # Pass events to UI manager first
            result = self.ui_manager.handle_event(event)
            if state_change_requested:
                print(f"[STATE] Change requested during event handling: {state_change_requested}")
                return

            # Pass events to other subsystems if not handled by UI
            if not result:
                self.tool_manager.handle_event(event, self.camera)
                self.camera.handle_event(event)

            if state_change_requested:
                print(f"[STATE] Change requested after event processing: {state_change_requested}")
                return

    
    # Keeping old method for compatibility, but it's no longer the primary event handler
    def handle_events(self):
        """Legacy event handler - redirects to state machine based handlers"""
        print("[WARNING] Using legacy handle_events method - this should be updated to use state machine")

        for event in pygame.event.get():
            global global_welcome_requested
            if global_welcome_requested:
                print("[LOG] Global welcome request detected during event processing")
                global_welcome_requested = False
                self.show_welcome_screen = True
                return
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h),
                    pygame.RESIZABLE
                )
                Config.WINDOW_WIDTH = event.w
                Config.WINDOW_HEIGHT = event.h
            
            result = self.ui_manager.handle_event(event)
            print(f"[DEBUG] UI event handled with result: {result}")
            
            if global_welcome_requested:
                print("[LOG] Global welcome request detected after UI event")
                global_welcome_requested = False
                self.show_welcome_screen = True
                return
            
            if self.exit_requested:
                print("[LOG] Exit requested from UI event")
                self.exit_requested = False
                self.show_welcome_screen = True
                return
            
            if self.show_welcome_screen:
                print("[LOG] UI event triggered return to welcome screen")
                return
                
            self.tool_manager.handle_event(event, self.camera)
            self.camera.handle_event(event)
    
    def update(self):
        self.camera.update()
        self.ui_manager.update()
    
    def render(self):
        self.screen.fill((30, 30, 30))
        
        if self.has_loaded_level:
            self.render_background()
            self.render_foreground()
            self.render_level_elements()
        
        if self.grid.show_grid and self.has_loaded_level:
            fg_height = self.level.foreground.get_height() if self.level.foreground else None
            self.grid.render(self.screen, self.camera, fg_height, self.level.width_pixels)
        
        self.ui_manager.render(self.screen)
        
        if self.has_loaded_level:
            self.tool_manager.render_preview(self.screen, self.camera)
            self.render_mouse_position()
        
        pygame.display.flip()
    
    def render_background(self):
        if not self.level.background:
            return
        
        # Use custom bg_scroll_rate if available, otherwise fallback to default 0.25
        parallax_factor = getattr(self.level, 'bg_scroll_rate', 0.25)
        
        original_clip = self.screen.get_clip()
        
        level_end_x = self.level.width_pixels - self.camera.x
        
        if level_end_x > 0:
            clip_rect = pygame.Rect(
                0, 
                Config.UI_PANEL_HEIGHT,
                min(level_end_x, Config.WINDOW_WIDTH),
                Config.WINDOW_HEIGHT - Config.UI_PANEL_HEIGHT
            )
            self.screen.set_clip(clip_rect)
            
            bg_x = -self.camera.x * parallax_factor
            bg_width = self.level.background.get_width()
            
            tiles_needed = (Config.WINDOW_WIDTH // bg_width) + 2
            
            for i in range(tiles_needed):
                pos_x = (bg_x % bg_width) + (i * bg_width)
                if pos_x < Config.WINDOW_WIDTH and pos_x + bg_width > 0:
                    self.screen.blit(self.level.background, (pos_x, Config.UI_PANEL_HEIGHT))
        
        self.screen.set_clip(original_clip)
    
    def render_foreground(self):
        if not self.level.foreground:
            return
        
        original_clip = self.screen.get_clip()
        
        level_end_x = self.level.width_pixels - self.camera.x
        
        if level_end_x > 0:
            clip_rect = pygame.Rect(
                0, 
                Config.UI_PANEL_HEIGHT,
                min(level_end_x, Config.WINDOW_WIDTH),
                Config.WINDOW_HEIGHT - Config.UI_PANEL_HEIGHT
            )
            self.screen.set_clip(clip_rect)
            
            # Use custom fg_scroll_rate if available, otherwise fallback to default 1.0
            parallax_factor = getattr(self.level, 'fg_scroll_rate', 1.0)
            
            fg_x = -self.camera.x * parallax_factor
            fg_width = self.level.foreground.get_width()
            
            tiles_needed = (Config.WINDOW_WIDTH // fg_width) + 2
            
            for i in range(tiles_needed):
                pos_x = (fg_x % fg_width) + (i * fg_width)
                
                if pos_x < Config.WINDOW_WIDTH and pos_x + fg_width > 0:
                    self.screen.blit(self.level.foreground, (pos_x, Config.UI_PANEL_HEIGHT))
        
        self.screen.set_clip(original_clip)
    
    def render_level_elements(self):
        # Render platforms
        for platform in self.level.platforms:
            screen_x = platform['x'] * self.grid.cell_size - self.camera.x
            screen_y = platform['y'] * self.grid.cell_size + Config.UI_PANEL_HEIGHT
            width = platform['width'] * self.grid.cell_size
            height = platform['height'] * self.grid.cell_size
            
            if screen_x + width > 0 and screen_x < Config.WINDOW_WIDTH:
                pygame.draw.rect(
                    self.screen,
                    (150, 75, 0),
                    (screen_x, screen_y, width, height)
                )
        
        # Render ground blocks
        for ground in self.level.ground_blocks:
            screen_x = ground['x'] * self.grid.cell_size - self.camera.x
            screen_y = ground['y'] * self.grid.cell_size + Config.UI_PANEL_HEIGHT
            width = ground['width'] * self.grid.cell_size
            
            if screen_x + width > 0 and screen_x < Config.WINDOW_WIDTH:
                pygame.draw.rect(
                    self.screen,
                    (70, 40, 0),
                    (screen_x, screen_y, width, self.grid.cell_size)
                )
        
        # Render enemies
        for enemy in self.level.enemies:
            screen_x = enemy['x'] * self.grid.cell_size - self.camera.x
            screen_y = enemy['y'] * self.grid.cell_size + Config.UI_PANEL_HEIGHT
            
            if (screen_x + self.grid.cell_size > 0 and 
                screen_x < Config.WINDOW_WIDTH):
                
                enemy_type = enemy.get('type', 'armadillo')
                if enemy_type in self.level.enemy_images:
                    sprite = self.level.enemy_images[enemy_type]
                    sprite_x = screen_x - sprite.get_width() // 2 + self.grid.cell_size // 2
                    sprite_y = screen_y + self.grid.cell_size - sprite.get_height()
                    self.screen.blit(sprite, (sprite_x, sprite_y))
                else:
                    pygame.draw.rect(
                        self.screen,
                        (255, 0, 0),
                        (screen_x, screen_y, self.grid.cell_size, self.grid.cell_size)
                    )
    
    def render_mouse_position(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_y < Config.UI_PANEL_HEIGHT:
            return
            
        world_x = mouse_x + self.camera.x
        world_y = mouse_y - Config.UI_PANEL_HEIGHT
        
        grid_x = int(world_x // self.grid.cell_size)
        grid_y = int(world_y // self.grid.cell_size)
        
        if grid_x < 0 or grid_y < 0 or grid_x >= self.level.width or grid_y >= self.level.height:
            return
        
        font = pygame.font.SysFont(None, 24)
        text = f"Pixel: ({world_x}, {world_y}) | Cell: ({grid_x}, {grid_y})"
        text_surface = font.render(text, True, Config.UI_FG_COLOR)
        
        text_rect = text_surface.get_rect()
        text_rect.right = Config.WINDOW_WIDTH - 10
        text_rect.y = 10
        self.screen.blit(text_surface, text_rect)
        
    def show_new_level_dialog(self):
        """Show the new level creation dialog"""
        # Create a dialog surface
        dialog_width = 650  # Increased width for scroll rate dropdown
        dialog_height = 450  # Reduced height since we removed instructions
        dialog_x = (Config.WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (Config.WINDOW_HEIGHT - dialog_height) // 2
        
        dialog_surface = pygame.Surface((dialog_width, dialog_height))
        
        # Font
        font = pygame.font.SysFont(None, 24)
        title_font = pygame.font.SysFont(None, 32)
        
        # Form fields
        fg_path = None
        bg_path = None
        cell_size = 32  # Default cell size
        level_width = Config.DEFAULT_LEVEL_WIDTH
        level_height = Config.DEFAULT_LEVEL_HEIGHT
        
        # Scroll rates
        fg_scroll_rate = 1.0  # Fixed at 1.0
        bg_scroll_rate = 0.2  # Default 0.2
        
        # Background scroll rate dropdown options
        bg_rate_options = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        bg_dropdown_open = False
        
        # Form state
        active_field = None
        
        # Preview surfaces
        fg_preview = None
        bg_preview = None
        
        # Dialog state
        dialog_running = True
        
        # Input field rects - 1/2 as wide for foreground, swapped fg/bg positions
        fg_field_rect = pygame.Rect(180, 80, 125, 30)
        bg_field_rect = pygame.Rect(180, 130, 125, 30)
        
        # Scroll rate input rects - 30% less wide, moved further right
        fg_rate_rect = pygame.Rect(480, 80, 56, 30)
        bg_rate_rect = pygame.Rect(480, 130, 56, 30)
        bg_dropdown_button_rect = pygame.Rect(516, 130, 20, 30)
        
        # Dropdown options rects - properly positioned below bg_rate_rect
        bg_dropdown_rects = []
        for i in range(len(bg_rate_options)):
            bg_dropdown_rects.append(pygame.Rect(480, 160 + i*30, 56, 30))
        
        # Other input field rects
        cell_size_rect = pygame.Rect(180, 190, 100, 30)
        level_width_rect = pygame.Rect(180, 240, 100, 30)
        level_height_rect = pygame.Rect(180, 290, 100, 30)
        
        # Button rects - 20% less wide
        fg_browse_rect = pygame.Rect(315, 80, 80, 30)
        bg_browse_rect = pygame.Rect(315, 130, 80, 30)
        
        # Position at 1/4 and 3/4 width for clear separation - moved down
        cancel_rect = pygame.Rect(dialog_width // 4 - 50, 370, 100, 40)
        create_rect = pygame.Rect((dialog_width * 3) // 4 - 50, 370, 100, 40)
        
        while dialog_running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Handle window resize
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (event.w, event.h),
                        pygame.RESIZABLE
                    )
                    Config.WINDOW_WIDTH = event.w
                    Config.WINDOW_HEIGHT = event.h
                    
                    # Update dialog position
                    dialog_x = (Config.WINDOW_WIDTH - dialog_width) // 2
                    dialog_y = (Config.WINDOW_HEIGHT - dialog_height) // 2
                
                # Handle mouse clicks
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = event.pos
                        
                        # Adjust for dialog position
                        mouse_x = mouse_pos[0] - dialog_x
                        mouse_y = mouse_pos[1] - dialog_y
                        
                        # Handle dropdown first (before other UI elements)
                        dropdown_clicked = False
                        
                        # Check if dropdown button or the rate field is clicked
                        if bg_dropdown_button_rect.collidepoint(mouse_x, mouse_y) or bg_rate_rect.collidepoint(mouse_x, mouse_y):
                            dropdown_clicked = True
                            bg_dropdown_open = not bg_dropdown_open
                            print(f"[DEBUG] Dropdown toggled: {bg_dropdown_open}")
                        
                        # Check if one of the dropdown options is clicked
                        option_clicked = False
                        if bg_dropdown_open:
                            for i, rect in enumerate(bg_dropdown_rects):
                                if rect.collidepoint(mouse_x, mouse_y):
                                    option_clicked = True
                                    dropdown_clicked = True
                                    old_rate = bg_scroll_rate
                                    bg_scroll_rate = bg_rate_options[i]
                                    print(f"[DEBUG] Rate changed: {old_rate} -> {bg_scroll_rate}")
                                    bg_dropdown_open = False
                                    break
                                    
                        # Only continue with other UI if the dropdown wasn't interacted with
                        if dropdown_clicked:
                            continue
                        
                        # Check field clicks
                        if cell_size_rect.collidepoint(mouse_x, mouse_y):
                            active_field = "cell_size"
                            bg_dropdown_open = False
                        elif level_width_rect.collidepoint(mouse_x, mouse_y):
                            active_field = "level_width"
                            bg_dropdown_open = False
                        elif level_height_rect.collidepoint(mouse_x, mouse_y):
                            active_field = "level_height"
                            bg_dropdown_open = False
                        elif bg_browse_rect.collidepoint(mouse_x, mouse_y):
                            # Browse for background image
                            bg_dropdown_open = False
                            bg_file = self.browse_for_image_file("Select Background Image")
                            if bg_file:
                                bg_path = bg_file
                                # Load preview
                                try:
                                    bg_img = pygame.image.load(bg_path).convert_alpha()
                                    img_w, img_h = bg_img.get_size()
                                    # Auto-adjust cell size based on image height
                                    suggested_cell = img_h // 16
                                    if suggested_cell > 0:
                                        cell_size = suggested_cell
                                    # Create small preview
                                    scale = min(30 / img_w, 30 / img_h)
                                    preview_w = int(img_w * scale)
                                    preview_h = int(img_h * scale)
                                    bg_preview = pygame.transform.smoothscale(bg_img, (preview_w, preview_h))
                                except Exception as e:
                                    print(f"Error loading background preview: {e}")
                        elif fg_browse_rect.collidepoint(mouse_x, mouse_y):
                            # Browse for foreground image
                            bg_dropdown_open = False
                            fg_file = self.browse_for_image_file("Select Foreground Image")
                            if fg_file:
                                fg_path = fg_file
                                # Load preview
                                try:
                                    fg_img = pygame.image.load(fg_path).convert_alpha()
                                    img_w, img_h = fg_img.get_size()
                                    # Auto-adjust cell size based on foreground height
                                    suggested_cell = img_h // 16
                                    if suggested_cell > 0:
                                        cell_size = suggested_cell
                                    # Auto-adjust level dimensions based on image
                                    level_width = img_w // cell_size
                                    level_height = img_h // cell_size
                                    # Create small preview
                                    scale = min(30 / img_w, 30 / img_h)
                                    preview_w = int(img_w * scale)
                                    preview_h = int(img_h * scale)
                                    fg_preview = pygame.transform.smoothscale(fg_img, (preview_w, preview_h))
                                except Exception as e:
                                    print(f"Error loading foreground preview: {e}")
                        elif cancel_rect.collidepoint(mouse_x, mouse_y):
                            # Cancel creating new level
                            return False
                        elif create_rect.collidepoint(mouse_x, mouse_y):
                            # Create the new level
                            if fg_path:
                                try:
                                    # Load foreground image
                                    self.level.foreground = pygame.image.load(fg_path).convert_alpha()
                                    self.level.fg_path = fg_path
                                    
                                    # Use any entered values without validation
                                    # Ensure cell_size is at least 1 to avoid division by zero
                                    if cell_size <= 0:
                                        cell_size = 1
                                    
                                    # If width or height is 0, set a minimal value
                                    if level_width <= 0:
                                        level_width = 1
                                    if level_height <= 0:
                                        level_height = 1
                                        
                                    # Set level dimensions
                                    self.level.cell_size = cell_size
                                    self.grid.cell_size = cell_size
                                    
                                    # Update level dimensions
                                    fg_width = self.level.foreground.get_width()
                                    fg_height = self.level.foreground.get_height()
                                    self.level.width = level_width
                                    self.level.height = level_height
                                    self.level.width_pixels = level_width * cell_size
                                    self.level.height_pixels = fg_height
                                    
                                    # Load background image (if provided)
                                    if bg_path:
                                        self.level.background = pygame.image.load(bg_path).convert_alpha()
                                        self.level.bg_path = bg_path
                                    else:
                                        # Create placeholder background
                                        self.level.background = pygame.Surface((fg_width, fg_height))
                                        self.level.background.fill((100, 150, 200))  # Sky blue
                                    
                                    # Store scroll rates
                                    self.level.fg_scroll_rate = fg_scroll_rate
                                    self.level.bg_scroll_rate = bg_scroll_rate
                                    
                                    # Reset loaded level flag since we're creating a new level
                                    self.has_loaded_level = False
                                    
                                    dialog_running = False
                                    return True
                                except Exception as e:
                                    print(f"Error creating level: {e}")
                            else:
                                # Need foreground image at minimum
                                # Display error message
                                pass
                        else:
                            # If not clicking on any input field, clear active field
                            active_field = None
                            
                            # Close dropdown only if clicking outside dropdown area AND not on dropdown toggle
                            dropdown_area = False
                            
                            # Check if click is in dropdown area
                            if bg_dropdown_open:
                                # Check if click is in any dropdown option
                                for rect in bg_dropdown_rects:
                                    if rect.collidepoint(mouse_x, mouse_y):
                                        dropdown_area = True
                                        break
                            
                            # Close dropdown if clicking elsewhere (not on dropdown, not on rate rect, not on button)
                            if (bg_dropdown_open and not dropdown_area and 
                                not bg_rate_rect.collidepoint(mouse_x, mouse_y) and 
                                not bg_dropdown_button_rect.collidepoint(mouse_x, mouse_y)):
                                bg_dropdown_open = False
                                print("[DEBUG] Dropdown closed by clicking elsewhere")
                
                # Handle key presses for text fields
                elif event.type == pygame.KEYDOWN:
                    if active_field:
                        # Store the current values as strings for better editing
                        field_values = {
                            "cell_size": str(cell_size) if cell_size > 0 else "",
                            "level_width": str(level_width) if level_width > 0 else "",
                            "level_height": str(level_height) if level_height > 0 else "",
                        }
                        
                        # Handle backspace key
                        if event.key == pygame.K_BACKSPACE:
                            # Remove last character
                            current_value = field_values[active_field]
                            new_value = current_value[:-1] if current_value else ""
                            
                            # Update the appropriate field without validation
                            if active_field == "cell_size":
                                cell_size = int(new_value) if new_value else 0
                            elif active_field == "level_width":
                                level_width = int(new_value) if new_value else 0
                            elif active_field == "level_height":
                                level_height = int(new_value) if new_value else 0
                        
                        # Handle numeric input for fields
                        elif event.key >= pygame.K_0 and event.key <= pygame.K_9:
                            digit = event.key - pygame.K_0
                            current_value = field_values[active_field]
                            
                            # Add the digit to the current value without validation
                            new_value = current_value + str(digit)
                            
                            if active_field == "cell_size":
                                cell_size = int(new_value)
                            elif active_field == "level_width":
                                level_width = int(new_value)
                            elif active_field == "level_height":
                                level_height = int(new_value)
                        
                        # Handle Enter key to move to next field
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_TAB:
                            if active_field == "cell_size":
                                active_field = "level_width"
                            elif active_field == "level_width":
                                active_field = "level_height"
                            elif active_field == "level_height":
                                active_field = None
                        
                        # Handle escape key to cancel text entry
                        elif event.key == pygame.K_ESCAPE:
                            active_field = None
                            bg_dropdown_open = False
            
            # Clear dialog
            dialog_surface.fill((50, 50, 50))
            
            # Draw title
            title_surf = title_font.render("Create New Level", True, (255, 255, 255))
            title_rect = title_surf.get_rect(centerx=dialog_width//2, y=20)
            dialog_surface.blit(title_surf, title_rect)
            
            # Draw labels with input instructions - swapped foreground/background order
            fg_label = font.render("Foreground Image:", True, (200, 200, 200))
            dialog_surface.blit(fg_label, (20, 85))
            
            bg_label = font.render("Background Image:", True, (200, 200, 200))
            dialog_surface.blit(bg_label, (20, 135))
            
            # Draw scroll rate labels - shorter text
            fg_rate_label = font.render("Rate:", True, (200, 200, 200))
            dialog_surface.blit(fg_rate_label, (410, 85))
            
            bg_rate_label = font.render("Rate:", True, (200, 200, 200))
            dialog_surface.blit(bg_rate_label, (410, 135))
            
            cell_label = font.render("Cell Size (px):", True, (200, 200, 200))
            dialog_surface.blit(cell_label, (20, 195))
            
            width_label = font.render("Level Width (cells):", True, (200, 200, 200))
            dialog_surface.blit(width_label, (20, 245))
            
            height_label = font.render("Level Height (cells):", True, (200, 200, 200))
            dialog_surface.blit(height_label, (20, 295))
            
            # Get cursor flash time (toggle every 500ms)
            cursor_visible = (pygame.time.get_ticks() % 1000) < 500
            
            # Draw image input fields - swapped order
            pygame.draw.rect(dialog_surface, (30, 30, 30), fg_field_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), fg_field_rect, 1)
            fg_text = font.render(os.path.basename(fg_path) if fg_path else "No file selected", True, (255, 255, 255))
            fg_text_rect = fg_text.get_rect(midleft=(fg_field_rect.left + 5, fg_field_rect.centery))
            dialog_surface.blit(fg_text, fg_text_rect)
            
            pygame.draw.rect(dialog_surface, (30, 30, 30), bg_field_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), bg_field_rect, 1)
            bg_text = font.render(os.path.basename(bg_path) if bg_path else "No file selected", True, (255, 255, 255))
            bg_text_rect = bg_text.get_rect(midleft=(bg_field_rect.left + 5, bg_field_rect.centery))
            dialog_surface.blit(bg_text, bg_text_rect)
            
            # Draw scroll rate fields
            # Foreground rate - non-editable
            pygame.draw.rect(dialog_surface, (60, 60, 60), fg_rate_rect)  # Darker to indicate non-editable
            pygame.draw.rect(dialog_surface, (120, 120, 120), fg_rate_rect, 1)
            fg_rate_text = font.render(str(fg_scroll_rate), True, (200, 200, 200))
            fg_rate_text_rect = fg_rate_text.get_rect(center=fg_rate_rect.center)
            dialog_surface.blit(fg_rate_text, fg_rate_text_rect)
            
            # Background rate - dropdown box
            pygame.draw.rect(dialog_surface, (30, 30, 30), bg_rate_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), bg_rate_rect, 1)
            bg_rate_text = font.render(str(bg_scroll_rate), True, (255, 255, 255))
            bg_rate_text_rect = bg_rate_text.get_rect(midleft=(bg_rate_rect.left + 5, bg_rate_rect.centery))
            dialog_surface.blit(bg_rate_text, bg_rate_text_rect)
            
            # Draw dropdown button
            pygame.draw.rect(dialog_surface, (50, 50, 50), bg_dropdown_button_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), bg_dropdown_button_rect, 1)
            
            # Draw dropdown arrow
            pygame.draw.polygon(
                dialog_surface,
                (200, 200, 200),
                [
                    (bg_dropdown_button_rect.centerx, bg_dropdown_button_rect.centery + 5),
                    (bg_dropdown_button_rect.centerx - 5, bg_dropdown_button_rect.centery - 3),
                    (bg_dropdown_button_rect.centerx + 5, bg_dropdown_button_rect.centery - 3)
                ]
            )
            
            # Draw dropdown options if open
            if bg_dropdown_open:
                # Draw dropdown box with border
                dropdown_height = len(bg_rate_options) * 30
                dropdown_bg_rect = pygame.Rect(480, 160, 56, dropdown_height)
                pygame.draw.rect(dialog_surface, (60, 60, 70), dropdown_bg_rect)
                pygame.draw.rect(dialog_surface, (180, 180, 180), dropdown_bg_rect, 2)
                
                # Draw each option
                for i, rect in enumerate(bg_dropdown_rects):
                    value = bg_rate_options[i]
                    # Highlight currently selected value
                    bg_color = (80, 120, 180) if value == bg_scroll_rate else (50, 50, 60)
                    pygame.draw.rect(dialog_surface, bg_color, rect)
                    pygame.draw.rect(dialog_surface, (150, 150, 150), rect, 1)
                    
                    option_text = font.render(str(value), True, (255, 255, 255))
                    option_text_rect = option_text.get_rect(center=rect.center)
                    dialog_surface.blit(option_text, option_text_rect)
            
            # Draw the remaining numeric input fields
            # Cell Size field
            active_color = (40, 80, 120) if active_field == "cell_size" else (30, 30, 30)
            pygame.draw.rect(dialog_surface, active_color, cell_size_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), cell_size_rect, 1)
            
            # Show text and cursor for cell size
            cell_text = font.render(str(cell_size), True, (255, 255, 255))
            cell_text_rect = cell_text.get_rect(midleft=(cell_size_rect.left + 5, cell_size_rect.centery))
            dialog_surface.blit(cell_text, cell_text_rect)
            
            # Draw cursor for cell size if active
            if active_field == "cell_size" and cursor_visible:
                cursor_x = cell_text_rect.right + 2
                pygame.draw.line(
                    dialog_surface,
                    (255, 255, 255),
                    (cursor_x, cell_text_rect.top + 2),
                    (cursor_x, cell_text_rect.bottom - 2),
                    2
                )
            
            # Level Width field
            active_color = (40, 80, 120) if active_field == "level_width" else (30, 30, 30)
            pygame.draw.rect(dialog_surface, active_color, level_width_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), level_width_rect, 1)
            
            # Show text and cursor for level width
            width_text = font.render(str(level_width), True, (255, 255, 255))
            width_text_rect = width_text.get_rect(midleft=(level_width_rect.left + 5, level_width_rect.centery))
            dialog_surface.blit(width_text, width_text_rect)
            
            # Draw cursor for level width if active
            if active_field == "level_width" and cursor_visible:
                cursor_x = width_text_rect.right + 2
                pygame.draw.line(
                    dialog_surface,
                    (255, 255, 255),
                    (cursor_x, width_text_rect.top + 2),
                    (cursor_x, width_text_rect.bottom - 2),
                    2
                )
            
            # Level Height field
            active_color = (40, 80, 120) if active_field == "level_height" else (30, 30, 30)
            pygame.draw.rect(dialog_surface, active_color, level_height_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), level_height_rect, 1)
            
            # Show text and cursor for level height
            height_text = font.render(str(level_height), True, (255, 255, 255))
            height_text_rect = height_text.get_rect(midleft=(level_height_rect.left + 5, level_height_rect.centery))
            dialog_surface.blit(height_text, height_text_rect)
            
            # Draw cursor for level height if active
            if active_field == "level_height" and cursor_visible:
                cursor_x = height_text_rect.right + 2
                pygame.draw.line(
                    dialog_surface,
                    (255, 255, 255),
                    (cursor_x, height_text_rect.top + 2),
                    (cursor_x, height_text_rect.bottom - 2),
                    2
                )
            
            # Draw browse buttons - 20% less wide, simpler text
            pygame.draw.rect(dialog_surface, (80, 100, 120), fg_browse_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), fg_browse_rect, 1)
            fg_browse_text = font.render("Browse", True, (255, 255, 255))
            fg_browse_text_rect = fg_browse_text.get_rect(center=fg_browse_rect.center)
            dialog_surface.blit(fg_browse_text, fg_browse_text_rect)
            
            pygame.draw.rect(dialog_surface, (80, 100, 120), bg_browse_rect)
            pygame.draw.rect(dialog_surface, (150, 150, 150), bg_browse_rect, 1)
            bg_browse_text = font.render("Browse", True, (255, 255, 255))
            bg_browse_text_rect = bg_browse_text.get_rect(center=bg_browse_rect.center)
            dialog_surface.blit(bg_browse_text, bg_browse_text_rect)
            
            # Draw previews if available
            if fg_preview:
                dialog_surface.blit(fg_preview, (fg_field_rect.right + 10, fg_field_rect.centery - fg_preview.get_height() // 2))
            
            if bg_preview:
                dialog_surface.blit(bg_preview, (bg_field_rect.right + 10, bg_field_rect.centery - bg_preview.get_height() // 2))
            
            # Draw bottom buttons
            pygame.draw.rect(dialog_surface, (150, 50, 50), cancel_rect)
            pygame.draw.rect(dialog_surface, (200, 200, 200), cancel_rect, 1)
            cancel_text = font.render("Cancel", True, (255, 255, 255))
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            dialog_surface.blit(cancel_text, cancel_text_rect)
            
            # Create button (enabled only if foreground image is selected)
            create_color = (50, 150, 50) if fg_path else (100, 100, 100)
            pygame.draw.rect(dialog_surface, create_color, create_rect)
            pygame.draw.rect(dialog_surface, (200, 200, 200), create_rect, 1)
            create_text = font.render("Create", True, (255, 255, 255))
            create_text_rect = create_text.get_rect(center=create_rect.center)
            dialog_surface.blit(create_text, create_text_rect)
            
            # Display the dialog
            self.screen.blit(dialog_surface, (dialog_x, dialog_y))
            pygame.display.flip()
        
        return False
    
    def browse_for_image_file(self, title="Select Image"):
        """Show a UI to browse for an image file"""
        # Start in the resources/graphics directory
        current_dir = os.path.abspath(os.path.join("resources", "graphics"))
        if not os.path.exists(current_dir):
            current_dir = os.path.abspath(".")
        
        # Create a file dialog surface
        dialog_width = 600
        dialog_height = 400
        dialog_x = (Config.WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (Config.WINDOW_HEIGHT - dialog_height) // 2
        
        dialog_surface = pygame.Surface((dialog_width, dialog_height))
        
        # Font
        font = pygame.font.SysFont(None, 24)
        title_font = pygame.font.SysFont(None, 32)
        
        # Display state
        current_path = current_dir
        current_files = []
        selected_file = None
        
        # Initial file listing
        try:
            current_files = []
            for item in os.listdir(current_path):
                full_path = os.path.join(current_path, item)
                if os.path.isdir(full_path):
                    # Add trailing slash to directories
                    current_files.append((item + "/", full_path))
                elif item.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    current_files.append((item, full_path))
        except Exception as e:
            print(f"Error listing directory {current_path}: {e}")
        
        # Dialog state
        dialog_running = True
        scroll_offset = 0
        max_items = 10  # Maximum number of items to show at once
        
        # Button dimensions
        button_height = 30
        
        # Preview
        preview_surface = None
        preview_rect = pygame.Rect(
            dialog_width - 150,
            80,
            120,
            120
        )
        
        while dialog_running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Handle window resize
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (event.w, event.h),
                        pygame.RESIZABLE
                    )
                    Config.WINDOW_WIDTH = event.w
                    Config.WINDOW_HEIGHT = event.h
                    
                    # Update dialog position
                    dialog_x = (Config.WINDOW_WIDTH - dialog_width) // 2
                    dialog_y = (Config.WINDOW_HEIGHT - dialog_height) // 2
                
                # Handle mouse wheel for scrolling
                elif event.type == pygame.MOUSEWHEEL:
                    if event.y > 0:  # Scroll up
                        scroll_offset = max(0, scroll_offset - 1)
                    elif event.y < 0:  # Scroll down
                        max_scroll = max(0, len(current_files) - max_items)
                        scroll_offset = min(max_scroll, scroll_offset + 1)
                
                # Handle mouse clicks
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = event.pos
                        
                        # Adjust for dialog position
                        mouse_x = mouse_pos[0] - dialog_x
                        mouse_y = mouse_pos[1] - dialog_y
                        
                        # Check if a file was clicked
                        file_area_y = 80
                        file_area_width = dialog_width - 180 if preview_surface else dialog_width - 40
                        
                        for i in range(min(max_items, len(current_files))):
                            idx = i + scroll_offset
                            if idx < len(current_files):
                                file_rect = pygame.Rect(
                                    20,
                                    file_area_y + i * (button_height + 5),
                                    file_area_width,
                                    button_height
                                )
                                
                                if file_rect.collidepoint(mouse_x, mouse_y):
                                    filename, filepath = current_files[idx]
                                    
                                    if filename.endswith("/"):  # Directory
                                        # Navigate to this directory
                                        current_path = filepath
                                        scroll_offset = 0
                                        preview_surface = None
                                        
                                        # Refresh file listing
                                        try:
                                            current_files = []
                                            for item in os.listdir(current_path):
                                                full_path = os.path.join(current_path, item)
                                                if os.path.isdir(full_path):
                                                    current_files.append((item + "/", full_path))
                                                elif item.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                                                    current_files.append((item, full_path))
                                            
                                            # Add parent directory
                                            parent_dir = os.path.dirname(current_path)
                                            if parent_dir != current_path:  # Make sure we're not at root
                                                current_files.insert(0, ("../", parent_dir))
                                        except Exception as e:
                                            print(f"Error listing directory {current_path}: {e}")
                                    
                                    else:  # File
                                        selected_file = filepath
                                        
                                        # Show preview
                                        try:
                                            image = pygame.image.load(filepath).convert_alpha()
                                            # Scale to fit preview area
                                            img_w, img_h = image.get_size()
                                            scale = min(120 / img_w, 120 / img_h)
                                            preview_w = int(img_w * scale)
                                            preview_h = int(img_h * scale)
                                            preview_surface = pygame.transform.smoothscale(image, (preview_w, preview_h))
                                        except Exception as e:
                                            print(f"Error loading preview: {e}")
                                            preview_surface = None
                                    
                                    break
                        
                        # Check if cancel button was clicked
                        cancel_rect = pygame.Rect(
                            dialog_width // 4 - 40,  # Left quarter minus half button width
                            dialog_height - 50,
                            80,
                            40
                        )
                        
                        if cancel_rect.collidepoint(mouse_x, mouse_y):
                            selected_file = None
                            dialog_running = False
                        
                        # Check if select button was clicked
                        select_rect = pygame.Rect(
                            (dialog_width * 3) // 4 - 40,  # Right quarter minus half button width
                            dialog_height - 50,
                            80,
                            40
                        )
                        
                        if select_rect.collidepoint(mouse_x, mouse_y) and selected_file:
                            dialog_running = False
            
            # Clear dialog
            dialog_surface.fill((50, 50, 50))
            
            # Draw title
            title_surf = title_font.render(title, True, (255, 255, 255))
            title_rect = title_surf.get_rect(centerx=dialog_width//2, y=20)
            dialog_surface.blit(title_surf, title_rect)
            
            # Draw current path
            path_text = font.render(
                f"Directory: {os.path.basename(current_path)}", 
                True, 
                (200, 200, 200)
            )
            dialog_surface.blit(path_text, (20, 50))
            
            # Calculate file area width based on whether preview is shown
            file_area_width = dialog_width - 180 if preview_surface else dialog_width - 40
            
            # Draw files
            file_area_y = 80
            for i in range(min(max_items, len(current_files))):
                idx = i + scroll_offset
                if idx < len(current_files):
                    filename, filepath = current_files[idx]
                    
                    # Draw file button
                    file_rect = pygame.Rect(
                        20,
                        file_area_y + i * (button_height + 5),
                        file_area_width,
                        button_height
                    )
                    
                    # Different color for directories vs files and highlight selected
                    if filename.endswith("/"):
                        bg_color = (80, 100, 120)  # Directories
                    elif filepath == selected_file:
                        bg_color = (100, 150, 100)  # Selected file
                    else:
                        bg_color = (80, 80, 80)  # Files
                        
                    pygame.draw.rect(dialog_surface, bg_color, file_rect)
                    pygame.draw.rect(dialog_surface, (150, 150, 150), file_rect, 1)
                    
                    # Draw file name
                    file_text = font.render(filename, True, (255, 255, 255))
                    file_text_rect = file_text.get_rect(
                        midleft=(file_rect.left + 10, file_rect.centery)
                    )
                    dialog_surface.blit(file_text, file_text_rect)
            
            # Draw preview if available
            if preview_surface:
                pygame.draw.rect(dialog_surface, (30, 30, 30), preview_rect)
                pygame.draw.rect(dialog_surface, (150, 150, 150), preview_rect, 1)
                
                # Center the preview
                preview_x = preview_rect.centerx - preview_surface.get_width() // 2
                preview_y = preview_rect.centery - preview_surface.get_height() // 2
                dialog_surface.blit(preview_surface, (preview_x, preview_y))
            
            # Draw scroll indicators if needed
            if scroll_offset > 0:
                pygame.draw.polygon(
                    dialog_surface,
                    (200, 200, 200),
                    [(dialog_width//2, 70), (dialog_width//2 - 10, 60), (dialog_width//2 + 10, 60)]
                )
            
            if scroll_offset < len(current_files) - max_items and len(current_files) > max_items:
                pygame.draw.polygon(
                    dialog_surface,
                    (200, 200, 200),
                    [
                        (dialog_width//2, file_area_y + max_items * (button_height + 5) + 10),
                        (dialog_width//2 - 10, file_area_y + max_items * (button_height + 5)),
                        (dialog_width//2 + 10, file_area_y + max_items * (button_height + 5))
                    ]
                )
            
            # Draw cancel button
            cancel_rect = pygame.Rect(
                dialog_width // 4 - 40,  # Left quarter minus half button width
                dialog_height - 50,
                80,
                40
            )
            pygame.draw.rect(dialog_surface, (150, 50, 50), cancel_rect)
            pygame.draw.rect(dialog_surface, (200, 200, 200), cancel_rect, 1)
            
            cancel_text = font.render("Cancel", True, (255, 255, 255))
            cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
            dialog_surface.blit(cancel_text, cancel_text_rect)
            
            # Draw select button
            select_rect = pygame.Rect(
                (dialog_width * 3) // 4 - 40,  # Right quarter minus half button width
                dialog_height - 50,
                80,
                40
            )
            select_color = (50, 150, 50) if selected_file else (100, 100, 100)
            pygame.draw.rect(dialog_surface, select_color, select_rect)
            pygame.draw.rect(dialog_surface, (200, 200, 200), select_rect, 1)
            
            select_text = font.render("Select", True, (255, 255, 255))
            select_text_rect = select_text.get_rect(center=select_rect.center)
            dialog_surface.blit(select_text, select_text_rect)
            
            # Draw dialog to screen
            self.screen.blit(dialog_surface, (dialog_x, dialog_y))
            pygame.display.flip()
        
        # Return selected file
        return selected_file
    
    def render_welcome_screen(self):
        self.screen.fill((30, 30, 30))
        
        title_text = "Sidescroller Level Editor"
        title_surf = self.font_large.render(title_text, True, (255, 255, 255))
        title_rect = title_surf.get_rect(centerx=Config.WINDOW_WIDTH//2, y=100)
        self.screen.blit(title_surf, title_rect)
        
        instruction_text = "Choose an option to begin:"
        instruction_surf = self.font_medium.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surf.get_rect(centerx=Config.WINDOW_WIDTH//2, y=180)
        self.screen.blit(instruction_surf, instruction_rect)
        
        button_width = 200
        button_height = 50
        button_padding = 20
        
        new_btn_rect = pygame.Rect(
            Config.WINDOW_WIDTH//2 - button_width//2,
            250,
            button_width,
            button_height
        )
        
        load_btn_rect = pygame.Rect(
            Config.WINDOW_WIDTH//2 - button_width//2,
            250 + button_height + button_padding,
            button_width,
            button_height
        )
        
        exit_btn_rect = pygame.Rect(
            Config.WINDOW_WIDTH//2 - button_width//2,
            250 + (button_height + button_padding) * 2,
            button_width,
            button_height
        )
        
        pygame.draw.rect(self.screen, (50, 100, 200), new_btn_rect)
        pygame.draw.rect(self.screen, (50, 100, 50), load_btn_rect)
        pygame.draw.rect(self.screen, (150, 50, 50), exit_btn_rect)
        
        new_btn_text = self.font_medium.render("Create New Level", True, (255, 255, 255))
        new_btn_text_rect = new_btn_text.get_rect(center=new_btn_rect.center)
        self.screen.blit(new_btn_text, new_btn_text_rect)
        
        load_btn_text = self.font_medium.render("Load Level", True, (255, 255, 255))
        load_btn_text_rect = load_btn_text.get_rect(center=load_btn_rect.center)
        self.screen.blit(load_btn_text, load_btn_text_rect)
        
        exit_btn_text = self.font_medium.render("Exit", True, (255, 255, 255))
        exit_btn_text_rect = exit_btn_text.get_rect(center=exit_btn_rect.center)
        self.screen.blit(exit_btn_text, exit_btn_text_rect)
        
        # If there's an active dialog from UI manager, render it on top
        if self.ui_manager and self.ui_manager.active_dialog:
            self.ui_manager.active_dialog.render(self.screen)
        
        pygame.display.flip()
        
        self.welcome_buttons = {
            'new': new_btn_rect,
            'load': load_btn_rect,
            'exit': exit_btn_rect
        }
    
    def handle_welcome_events(self):
        global state_change_requested
        
        # If there is an active dialog (like a LoadLevelDialog), let it handle events
        if self.ui_manager.active_dialog:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    state_change_requested = AppState.EXITING
                    return
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    Config.WINDOW_WIDTH = event.w
                    Config.WINDOW_HEIGHT = event.h
                else:
                    self.ui_manager.handle_event(event)
            return
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state_change_requested = AppState.EXITING
                return
            
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                Config.WINDOW_WIDTH = event.w
                Config.WINDOW_HEIGHT = event.h
                self.render_welcome_screen()
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                
                if self.welcome_buttons['new'].collidepoint(mouse_pos):
                    try:
                        # Call the original function directly to avoid attribute problems
                        # This bypasses any instance attribute overriding
                        created = LevelEditor.show_new_level_dialog(self)
                        if created:
                            print("[STATE] New level created, transitioning to editor")
                            self.has_loaded_level = True
                            state_change_requested = AppState.LEVEL_EDITOR
                    except Exception as e:
                        print(f"[ERROR] Could not show new level dialog: {e}")
                        
                    return
                
                elif self.welcome_buttons['load'].collidepoint(mouse_pos):
                    # Use the new LoadLevelDialog instead of blocking load_level()
                    def on_load_dialog_closed(dialog_result, chosen_file=None):
                        if dialog_result and chosen_file:
                            # Use a try-except block to catch any loading issues
                            try:
                                loaded = FileManager(self.level).load_level(chosen_file)
                                if loaded:
                                    print("[STATE] Level loaded, transitioning to editor")
                                    self.has_loaded_level = True
                                    
                                    # Also load assets that might be referenced in the level
                                    try:
                                        if self.level.bg_path and os.path.exists(self.level.bg_path):
                                            self.level.background = pygame.image.load(self.level.bg_path).convert_alpha()
                                        if self.level.fg_path and os.path.exists(self.level.fg_path):
                                            self.level.foreground = pygame.image.load(self.level.fg_path).convert_alpha()
                                        
                                        # Set flag to indicate we're loading an existing level
                                        self.has_loaded_level = True
                                        
                                        # Make sure to trigger assets to load properly
                                        self.load_assets(self.level.bg_path, self.level.fg_path)
                                    except Exception as e:
                                        print(f"[ERROR] Loading level assets: {e}")
                                        # Continue anyway with default assets
                                        
                                    # IMPORTANT: First change state, then clear dialog
                                    # This ensures no events are processed between clearing dialog and changing state
                                    global state_change_requested
                                    state_change_requested = AppState.LEVEL_EDITOR
                                    
                                    # Give pygame events time to process before clearing dialog
                                    pygame.time.delay(50)
                                    
                                    # Now it's safe to clear the dialog
                                    self.ui_manager.active_dialog = None
                                else:
                                    print("[STATE] Load failed or cancelled")
                                    self.render_welcome_screen()
                            except Exception as e:
                                print(f"[ERROR] During level loading: {e}")
                                self.render_welcome_screen()
                    
                    self.ui_manager.active_dialog = LoadLevelDialog(self.level, on_load_dialog_closed)
                    return
                
                elif self.welcome_buttons['exit'].collidepoint(mouse_pos):
                    print("[STATE] Exit button clicked, exiting application")
                    state_change_requested = AppState.EXITING
                    self.running = False
                    return
    
    def run(self):
        global current_app_state, state_change_requested
        current_app_state = AppState.WELCOME_SCREEN
        
        print(f"[LOG] Starting application in state: {current_app_state}")
        
        loop_counter = 0
        
        while self.running:
            loop_counter += 1
                
            if state_change_requested is not None:
                new_state = state_change_requested
                print(f"[STATE] Changing state: {current_app_state} -> {new_state}")
                if current_app_state == AppState.LEVEL_EDITOR:
                    if hasattr(self, 'ui_manager') and self.ui_manager and self.ui_manager.active_dialog:
                        print("[LOG] Clearing active dialog during state transition")
                        self.ui_manager.active_dialog = None
                current_app_state = new_state
                state_change_requested = None
                print(f"[STATE] Now in state: {current_app_state}")
                continue
            
            if current_app_state == AppState.WELCOME_SCREEN:
                self.render_welcome_screen()
                self.handle_welcome_events()
                
                if state_change_requested:
                    print(f"[STATE] State change requested during welcome screen: {state_change_requested}")
                    continue
                
            elif current_app_state == AppState.LEVEL_EDITOR:
                self.handle_editor_events()
                if state_change_requested:
                    print(f"[STATE] State change requested after editor events: {state_change_requested}")
                    continue
                self.update()
                self.render()
                if state_change_requested:
                    print(f"[STATE] State change requested after editor rendering: {state_change_requested}")
                    continue
                
            elif current_app_state == AppState.EXITING:
                print("[STATE] Exiting application")
                self.running = False
                
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()
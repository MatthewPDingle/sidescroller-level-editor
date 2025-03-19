import os
import json
import pygame
import sys
from editor.config import Config

class FileManager:
    def __init__(self, level):
        self.level = level
        
        # Create levels directory if it doesn't exist
        if not os.path.exists(Config.LEVELS_DIR):
            os.makedirs(Config.LEVELS_DIR)
            
        self.temp_dir = os.path.join("resources", "temp")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def save_level(self, filename=None):
        """Save the level to a JSON file"""
        if filename is None:
            filename = "level1.json"
        
        if not filename.endswith(".json"):
            filename += ".json"
        
        if not os.path.exists(Config.LEVELS_DIR):
            try:
                os.makedirs(Config.LEVELS_DIR)
                print(f"Created levels directory: {Config.LEVELS_DIR}")
            except Exception as e:
                print(f"Error creating levels directory: {e}")
                return None
        
        filepath = os.path.join(Config.LEVELS_DIR, filename)
        
        try:
            level_data = self.level.to_dict()
            with open(filepath, 'w') as f:
                json.dump(level_data, f, indent=2)
            
            abs_path = os.path.abspath(filepath)
            print(f"=== LEVEL SAVED ===")
            print(f"Relative path: {filepath}")
            print(f"Absolute path: {abs_path}")
            print(f"==================")
            return filepath
        except Exception as e:
            print(f"Error saving level: {e}")
            return None
    
    def load_level(self, filename=None):
        """Load a level from a JSON file (no blocking loops).  
           'filename' should be the exact .json file name inside the levels directory.
        """
        if not os.path.exists(Config.LEVELS_DIR):
            try:
                os.makedirs(Config.LEVELS_DIR)
                print(f"Created directory: {Config.LEVELS_DIR}")
            except Exception as e:
                print(f"Error creating levels directory: {e}")
        
        if not filename:
            # If no filename given, do nothing
            print("No filename provided to load_level()")
            return False
        
        if not filename.endswith(".json"):
            filename += ".json"
        
        filepath = os.path.join(Config.LEVELS_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"Level file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                level_data = json.load(f)
            
            self.level.from_dict(level_data)
            
            # Check for asset paths in the assets section
            if 'assets' in level_data and level_data['assets']:
                assets = level_data['assets']
                
                # Load background
                if 'background' in assets and assets['background']:
                    self.level.bg_path = assets['background']
                    if os.path.exists(self.level.bg_path):
                        self.level.background = pygame.image.load(self.level.bg_path).convert_alpha()
                    else:
                        print(f"Warning: Background image not found at {self.level.bg_path}")
                
                # Load foreground
                if 'foreground' in assets and assets['foreground']:
                    self.level.fg_path = assets['foreground']
                    if os.path.exists(self.level.fg_path):
                        self.level.foreground = pygame.image.load(self.level.fg_path).convert_alpha()
                    else:
                        print(f"Warning: Foreground image not found at {self.level.fg_path}")
                
            # Backward compatibility for older format
            elif 'bg_path' in level_data:
                self.level.bg_path = level_data['bg_path']
                if os.path.exists(self.level.bg_path):
                    self.level.background = pygame.image.load(self.level.bg_path).convert_alpha()
            
            elif 'fg_path' in level_data:
                self.level.fg_path = level_data['fg_path']
                if os.path.exists(self.level.fg_path):
                    self.level.foreground = pygame.image.load(self.level.fg_path).convert_alpha()
            
            print(f"Level loaded from {filepath}")
            from main import LevelEditor
            editor = LevelEditor.instance
            if editor:
                editor.has_loaded_level = True
                
                # Print debug info about dimensions
                print(f"[DEBUG] Loaded level dimensions: {self.level.width}x{self.level.height} cells")
                print(f"[DEBUG] Pixel dimensions: {self.level.width_pixels}x{self.level.height_pixels} px")
            
            return True
        
        except Exception as e:
            print(f"Error loading level: {e}")
            return False
    
    def list_level_files(self):
        """Return a sorted list of all .json files in the levels directory."""
        if not os.path.exists(Config.LEVELS_DIR):
            return []
        files = []
        for item in os.listdir(Config.LEVELS_DIR):
            if item.lower().endswith(".json"):
                files.append(item)
        return sorted(files)
                
    def browse_for_level_file(self):
        """Show a UI to browse for a level file"""
        # Start in the levels directory
        current_dir = os.path.abspath(Config.LEVELS_DIR)
        
        # Make sure the levels directory exists
        if not os.path.exists(current_dir):
            try:
                os.makedirs(current_dir)
                print(f"Created levels directory: {current_dir}")
            except Exception as e:
                print(f"Error creating levels directory: {e}")
                return None
        
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
            # Check if parent directory exists to add a "go up" option
            parent_dir = os.path.dirname(current_path)
            if parent_dir != current_path:  # Make sure we're not at root
                current_files.append(("../", parent_dir))
                
            for item in os.listdir(current_path):
                full_path = os.path.join(current_path, item)
                if os.path.isdir(full_path):
                    # Add trailing slash to directories
                    current_files.append((item + "/", full_path))
                elif item.endswith(".json"):
                    current_files.append((item, full_path))
                    
        except Exception as e:
            print(f"Error listing directory {current_path}: {e}")
        
        # Dialog state
        dialog_running = True
        scroll_offset = 0
        max_items = 10  # Maximum number of items to show at once
        
        # Button dimensions
        button_height = 30
        
        while dialog_running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Handle window resize
                elif event.type == pygame.VIDEORESIZE:
                    from main import LevelEditor
                    editor = LevelEditor.instance
                    if editor:
                        editor.screen = pygame.display.set_mode(
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
                        file_area_y = 80  # Starting y position of file list
                        for i in range(min(max_items, len(current_files))):
                            idx = i + scroll_offset
                            if idx < len(current_files):
                                file_rect = pygame.Rect(
                                    20,
                                    file_area_y + i * (button_height + 5),
                                    dialog_width - 40,
                                    button_height
                                )
                                
                                if file_rect.collidepoint(mouse_x, mouse_y):
                                    filename, filepath = current_files[idx]
                                    
                                    if filename.endswith("/"):  # Directory
                                        # Navigate to this directory
                                        current_path = filepath
                                        scroll_offset = 0
                                        selected_file = None  # Clear selection when changing directory
                                        
                                        # Refresh file listing
                                        try:
                                            current_files = []
                                            # Always add parent directory first
                                            parent_dir = os.path.dirname(current_path)
                                            if parent_dir != current_path:  # Make sure we're not at root
                                                current_files.append(("../", parent_dir))
                                            
                                            for item in os.listdir(current_path):
                                                full_path = os.path.join(current_path, item)
                                                if os.path.isdir(full_path):
                                                    current_files.append((item + "/", full_path))
                                                elif item.endswith(".json"):
                                                    current_files.append((item, full_path))
                                        except Exception as e:
                                            print(f"Error listing directory {current_path}: {e}")
                                    
                                    else:  # File
                                        selected_file = filepath
                                        print(f"Selected file: {selected_file}")
                                        # Don't close dialog automatically, wait for Open button
                                    
                                    break
                        
                        # Check if cancel button was clicked - position at 1/4 of dialog width
                        cancel_rect = pygame.Rect(
                            dialog_width // 4 - 40,  # Left quarter minus half button width
                            dialog_height - 50,
                            80,
                            40
                        )
                        
                        if cancel_rect.collidepoint(mouse_x, mouse_y):
                            print("Cancel button clicked in file dialog")
                            selected_file = None
                            dialog_running = False
                            return None  # Return early to prevent freezing
                        
                        # Check if open button was clicked - position at 3/4 of dialog width
                        open_rect = pygame.Rect(
                            (dialog_width * 3) // 4 - 40,  # Right quarter minus half button width
                            dialog_height - 50,
                            80,
                            40
                        )
                        
                        if open_rect.collidepoint(mouse_x, mouse_y):
                            if selected_file:
                                print(f"Open button clicked with selected file: {selected_file}")
                                dialog_running = False
                                return selected_file  # Return early with the selected file
                            else:
                                print("Open button clicked but no file selected")
                                # Flash the button or show a hint
            
            # Clear dialog
            dialog_surface.fill((50, 50, 50))
            
            # Draw title
            title = title_font.render("Select Level File", True, (255, 255, 255))
            title_rect = title.get_rect(centerx=dialog_width//2, y=20)
            dialog_surface.blit(title, title_rect)
            
            # Draw current path
            path_text = font.render(
                f"Current Directory: {os.path.basename(current_path)}", 
                True, 
                (200, 200, 200)
            )
            dialog_surface.blit(path_text, (20, 50))
            
            # Display message if no files found (excluding the "../" parent directory entry)
            file_count = len([f for f in current_files if not f[0].startswith("../")])
            if file_count == 0:
                no_files_text = font.render("No level files found in this directory", True, (255, 150, 150))
                no_files_rect = no_files_text.get_rect(centerx=dialog_width//2, y=150)
                dialog_surface.blit(no_files_text, no_files_rect)
            
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
                        dialog_width - 40,
                        button_height
                    )
                    
                    # Different color for directories vs files
                    if filename.endswith("/"):
                        bg_color = (80, 100, 120)  # Directories
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
            
            # Draw cancel button - position at 1/4 of dialog width
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
            
            # Draw open button - position at 3/4 of dialog width
            open_rect = pygame.Rect(
                (dialog_width * 3) // 4 - 40,  # Right quarter minus half button width
                dialog_height - 50,
                80,
                40
            )
            open_color = (50, 150, 50) if selected_file else (100, 100, 100)
            pygame.draw.rect(dialog_surface, open_color, open_rect)
            pygame.draw.rect(dialog_surface, (200, 200, 200), open_rect, 1)
            
            open_text = font.render("Open", True, (255, 255, 255))
            open_text_rect = open_text.get_rect(center=open_rect.center)
            dialog_surface.blit(open_text, open_text_rect)
            
            # Draw dialog to screen
            from main import LevelEditor
            editor = LevelEditor.instance
            if editor:
                editor.screen.blit(dialog_surface, (dialog_x, dialog_y))
                pygame.display.flip()
        
        # Return selected file
        return selected_file
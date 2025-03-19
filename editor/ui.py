import pygame
import pygame.freetype
import os
import sys
from pygame.locals import *
from editor.config import Config
from editor.tools import PlatformTool, GroundTool, EnemyTool, DeleteTool
from editor.file_manager import FileManager

class ModalDialog:
    """A class to handle modal dialogs that work with the main event loop."""
    def __init__(self, title, message, width=400, height=200):
        self.title = title
        self.message = message
        self.width = width
        self.height = height
        self.active = True
        
        self.x = (Config.WINDOW_WIDTH - width) // 2
        self.y = (Config.WINDOW_HEIGHT - height) // 2
        
        self.surface = pygame.Surface((width, height))
        
        self.title_font = pygame.font.SysFont(None, 32)
        self.font = pygame.font.SysFont(None, 24)
        
        self.buttons = []
        self.callback = None
        self.result = None
    
    def add_button(self, text, result, color=(80, 80, 80), x=None, y=None, width=100, height=40):
        if x is None:
            num_buttons = len(self.buttons) + 1
            button_spacing = 20
            total_width = num_buttons * width + (num_buttons - 1) * button_spacing
            if total_width > self.width - 40:
                if num_buttons > 2:
                    width = (self.width - 40 - (num_buttons - 1) * button_spacing) // num_buttons
                total_width = num_buttons * width + (num_buttons - 1) * button_spacing
            start_x = (self.width - total_width) // 2
            x = start_x + (width + button_spacing) * len(self.buttons)
        
        if y is None:
            y = self.height - 60
        
        self.buttons.append({
            'rect': pygame.Rect(x, y, width, height),
            'text': text,
            'result': result,
            'color': color,
            'hover': False
        })
    
    def add_default_buttons(self):
        self.add_button("Cancel", False, color=(150, 50, 50))
        self.add_button("OK", True, color=(50, 150, 50))
    
    def set_callback(self, callback):
        self.callback = callback
    
    def check_events(self, event):
        if not self.active:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            mouse_x -= self.x
            mouse_y -= self.y
            for button in self.buttons:
                button['hover'] = button['rect'].collidepoint(mouse_x, mouse_y)
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            mouse_x -= self.x
            mouse_y -= self.y
            for button in self.buttons:
                if button['rect'].collidepoint(mouse_x, mouse_y):
                    self.result = button['result']
                    btn_text = button['text']
                    print(f"[LOG] Dialog button '{btn_text}' clicked with result: {self.result}")
                    
                    if self.callback:
                        try:
                            self.callback(self.result)
                        except Exception as e:
                            print(f"[ERROR] Exception in dialog callback: {e}")
                    self.active = False
                    return True
        
        return True
    
    def render(self, screen):
        if not self.active:
            return
        
        self.surface.fill((50, 50, 50))
        
        title_surf = self.title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(centerx=self.width//2, y=20)
        self.surface.blit(title_surf, title_rect)
        
        if isinstance(self.message, list):
            message_lines = self.message
        else:
            message_lines = [self.message]
        
        line_height = 30
        start_y = 70
        for i, line in enumerate(message_lines):
            msg_surf = self.font.render(line, True, (255, 255, 255))
            msg_rect = msg_surf.get_rect(centerx=self.width//2, y=start_y + i * line_height)
            self.surface.blit(msg_surf, msg_rect)
        
        for button in self.buttons:
            color = button['color']
            if button['hover']:
                color = tuple(min(c + 30, 255) for c in color)
            pygame.draw.rect(self.surface, color, button['rect'])
            pygame.draw.rect(self.surface, (200, 200, 200), button['rect'], 1)
            btn_text = self.font.render(button['text'], True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=button['rect'].center)
            self.surface.blit(btn_text, btn_text_rect)
        
        screen.blit(self.surface, (self.x, self.y))

class SaveDialog(ModalDialog):
    def __init__(self, callback):
        super().__init__("Save Level", "Enter a filename to save your level:", width=400, height=200)
        self.filename = "level1"
        self.active_field = True
        
        self.input_rect = pygame.Rect(
            self.width // 2 - 150,
            self.height // 2 - 20,
            300,
            40
        )
        
        self.add_button("Cancel", False, color=(80, 80, 80), 
                       x=self.width//4 - 50, y=self.height - 60)
        self.add_button("Save", True, color=(50, 150, 50), 
                       x=(self.width*3)//4 - 50, y=self.height - 60)
        
        self.set_callback(callback)
    
    def check_events(self, event):
        if not self.active:
            return False
        
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                mouse_x -= self.x
                mouse_y -= self.y
                if self.input_rect.collidepoint(mouse_x, mouse_y):
                    self.active_field = True
                    return True
                else:
                    self.active_field = False
                    for button in self.buttons:
                        if button['rect'].collidepoint(mouse_x, mouse_y) and button['text'] == "Save":
                            if self.filename.strip():
                                self.result = True
                                self.active = False
                                if self.callback:
                                    self.callback(self.result, self.filename)
                            return True
            
            return super().check_events(event)
        
        elif event.type == pygame.KEYDOWN and self.active_field:
            if event.key == pygame.K_BACKSPACE:
                self.filename = self.filename[:-1]
            elif event.key == pygame.K_RETURN:
                if self.filename.strip():
                    self.result = True
                    self.active = False
                    if self.callback:
                        self.callback(self.result, self.filename)
            elif event.key == pygame.K_ESCAPE:
                self.result = False
                self.active = False
                if self.callback:
                    self.callback(self.result)
            elif event.unicode:
                invalid_chars = '\\/:*?"<>|'
                if not any(c in invalid_chars for c in event.unicode):
                    self.filename += event.unicode
            
            return True
        
        return super().check_events(event)
    
    def render(self, screen):
        if not self.active:
            return
        
        self.surface.fill((50, 50, 50))
        
        title_surf = self.title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(centerx=self.width//2, y=20)
        self.surface.blit(title_surf, title_rect)
        
        msg_surf = self.font.render(self.message, True, (200, 200, 200))
        msg_rect = msg_surf.get_rect(centerx=self.width//2, y=60)
        self.surface.blit(msg_surf, msg_rect)
        
        cursor_visible = (pygame.time.get_ticks() % 1000) < 500
        
        active_color = (40, 80, 120) if self.active_field else (30, 30, 30)
        pygame.draw.rect(self.surface, active_color, self.input_rect)
        pygame.draw.rect(self.surface, (150, 150, 150), self.input_rect, 1)
        
        filename_text = self.font.render(self.filename, True, (255, 255, 255))
        filename_text_rect = filename_text.get_rect(midleft=(self.input_rect.left + 10, self.input_rect.centery))
        self.surface.blit(filename_text, filename_text_rect)
        
        if self.active_field and cursor_visible:
            cursor_x = filename_text_rect.right + 2
            pygame.draw.line(
                self.surface,
                (255, 255, 255),
                (cursor_x, self.input_rect.top + 5),
                (cursor_x, self.input_rect.bottom - 5),
                2
            )
        
        for button in self.buttons:
            color = button['color']
            if button['text'] == "Save" and not self.filename.strip():
                color = (80, 80, 80)
            elif button['hover']:
                color = tuple(min(c + 30, 255) for c in color)
            
            pygame.draw.rect(self.surface, color, button['rect'])
            pygame.draw.rect(self.surface, (200, 200, 200), button['rect'], 1)
            
            btn_text = self.font.render(button['text'], True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=button['rect'].center)
            self.surface.blit(btn_text, btn_text_rect)
        
        screen.blit(self.surface, (self.x, self.y))

class LoadLevelDialog(ModalDialog):
    """
    A modal dialog to let the user pick one of the .json files 
    from the levels directory.
    Callback is called with (True, chosen_filename) if they pick one,
    or (False, None) if they cancel.
    """
    def __init__(self, level, callback):
        super().__init__("Load Level", "", width=500, height=400)
        self.level = level
        self.set_callback(None)  # We'll manually handle the callback
        self._external_callback = callback
        
        self.file_manager = FileManager(self.level)
        self.file_list = self.file_manager.list_level_files()
        
        self.buttons = []
        self.file_buttons = []
        self.selected_file = None
        
        # We'll create a "Cancel" button at bottom
        self.cancel_rect = pygame.Rect(self.width//2 - 50, self.height - 50, 100, 40)
        
        # Scrolling support
        self.scroll_offset = 0
        self.max_items = 8
        self.button_height = 32
    
    def check_events(self, event):
        if not self.active:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            mouse_x -= self.x
            mouse_y -= self.y
            # Mark hover on file entries
            self._update_hover(mouse_x, mouse_y)
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            mouse_x -= self.x
            mouse_y -= self.y
            
            # Check if clicked a file entry
            file_area_y = 60
            for i in range(min(self.max_items, len(self.file_list) - self.scroll_offset)):
                idx = i + self.scroll_offset
                item_rect = pygame.Rect(20, file_area_y + i*(self.button_height+5),
                                        self.width - 40, self.button_height)
                if idx < len(self.file_list) and item_rect.collidepoint(mouse_x, mouse_y):
                    self.selected_file = self.file_list[idx]
                    return True
            
            # Check if clicked the cancel button
            if self.cancel_rect.collidepoint(mouse_x, mouse_y):
                self._close_dialog(False, None)
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (4,5):
            # Mouse wheel
            if event.button == 4:  # scroll up
                self.scroll_offset = max(0, self.scroll_offset - 1)
            else:  # scroll down
                max_scroll = max(0, len(self.file_list) - self.max_items)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
            return True
        
        elif event.type == pygame.KEYDOWN:
            # If user presses Enter and we have a selected file, do "OK"
            if event.key == pygame.K_RETURN and self.selected_file:
                self._close_dialog(True, self.selected_file)
                return True
            elif event.key == pygame.K_ESCAPE:
                self._close_dialog(False, None)
                return True
        
        return True
    
    def _close_dialog(self, ok_result, chosen_file):
        self.active = False
        if self._external_callback:
            try:
                self._external_callback(ok_result, chosen_file)
            except Exception as e:
                print(f"[ERROR] in LoadLevelDialog callback: {e}")
    
    def _update_hover(self, mx, my):
        # For file listing
        file_area_y = 60
        for i in range(min(self.max_items, len(self.file_list) - self.scroll_offset)):
            idx = i + self.scroll_offset
            item_rect = pygame.Rect(20, file_area_y + i*(self.button_height+5),
                                    self.width - 40, self.button_height)
            # We could highlight if hovered, but let's skip it for brevity
            pass
    
    def render(self, screen):
        if not self.active:
            return
        
        self.surface.fill((50, 50, 50))
        
        # Title
        title_surf = self.title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(centerx=self.width//2, y=10)
        self.surface.blit(title_surf, title_rect)
        
        # If empty
        if not self.file_list:
            msg = "No .json files found in /levels/ folder."
            msg_surf = self.font.render(msg, True, (255, 150, 150))
            msg_rect = msg_surf.get_rect(centerx=self.width//2, y=80)
            self.surface.blit(msg_surf, msg_rect)
        else:
            # Draw each file as a button
            file_area_y = 60
            for i in range(min(self.max_items, len(self.file_list) - self.scroll_offset)):
                idx = i + self.scroll_offset
                filename = self.file_list[idx]
                item_rect = pygame.Rect(20, file_area_y + i*(self.button_height+5),
                                        self.width - 40, self.button_height)
                
                bg_color = (80, 80, 80)
                if filename == self.selected_file:
                    bg_color = (60, 120, 60)
                
                pygame.draw.rect(self.surface, bg_color, item_rect)
                pygame.draw.rect(self.surface, (150, 150, 150), item_rect, 1)
                
                text_surf = self.font.render(filename, True, (255, 255, 255))
                text_rect = text_surf.get_rect(midleft=(item_rect.left + 10, item_rect.centery))
                self.surface.blit(text_surf, text_rect)
            
            # Scroll indicators if needed
            if self.scroll_offset > 0:
                pygame.draw.polygon(
                    self.surface,
                    (200, 200, 200),
                    [(self.width//2, 50), (self.width//2 - 10, 40), (self.width//2 + 10, 40)]
                )
            
            max_scroll = max(0, len(self.file_list) - self.max_items)
            if self.scroll_offset < max_scroll:
                bottom_tri_y = file_area_y + self.max_items*(self.button_height+5)
                pygame.draw.polygon(
                    self.surface,
                    (200, 200, 200),
                    [
                        (self.width//2, bottom_tri_y + 10),
                        (self.width//2 - 10, bottom_tri_y),
                        (self.width//2 + 10, bottom_tri_y)
                    ]
                )
            
            # Show instructions or selected file
            if self.selected_file:
                instr = f"Press Enter to load: {self.selected_file}"
            else:
                instr = "Click a file, then press Enter or scroll with mousewheel."
            instr_surf = self.font.render(instr, True, (200, 200, 200))
            instr_rect = instr_surf.get_rect(centerx=self.width//2, y=self.height - 90)
            self.surface.blit(instr_surf, instr_rect)
        
        # Cancel button
        pygame.draw.rect(self.surface, (120, 50, 50), self.cancel_rect)
        pygame.draw.rect(self.surface, (200, 200, 200), self.cancel_rect, 1)
        cancel_text = self.font.render("Cancel", True, (255, 255, 255))
        cancel_text_rect = cancel_text.get_rect(center=self.cancel_rect.center)
        self.surface.blit(cancel_text, cancel_text_rect)
        
        screen.blit(self.surface, (self.x, self.y))

class Button:
    def __init__(self, rect, text, callback, tooltip=None, icon=None):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.tooltip = tooltip if tooltip else ""
        self.icon = icon
        self.hovered = False
        self.active = False
    
    def render(self, surface):
        if self.active:
            bg_color = Config.UI_HIGHLIGHT_COLOR
        elif self.hovered:
            bg_color = tuple(min(c + 30, 255) for c in Config.UI_BG_COLOR)
        else:
            bg_color = Config.UI_BG_COLOR
        
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, Config.UI_FG_COLOR, self.rect, 1)
        
        if self.icon:
            icon_rect = self.icon.get_rect(center=self.rect.center)
            surface.blit(self.icon, icon_rect)
        else:
            font = pygame.font.SysFont(None, 24)
            text_surface = font.render(self.text, True, Config.UI_FG_COLOR)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
        
        if self.hovered and self.tooltip:
            tooltip_font = pygame.font.SysFont(None, 20)
            tooltip_surface = tooltip_font.render(self.tooltip, True, (255, 255, 255))
            tooltip_rect = tooltip_surface.get_rect()
            tooltip_rect.midtop = (self.rect.centerx, self.rect.bottom + 5)
            
            padding = 5
            tooltip_bg_rect = tooltip_rect.inflate(padding * 2, padding * 2)
            pygame.draw.rect(surface, (50, 50, 50, 200), tooltip_bg_rect)
            pygame.draw.rect(surface, (100, 100, 100), tooltip_bg_rect, 1)
            
            surface.blit(tooltip_surface, tooltip_rect)
    
    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
    
    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()
            return True
        return False

class UIManager:
    def __init__(self, tool_manager, level, grid, camera):
        self.tool_manager = tool_manager
        self.level = level
        self.grid = grid
        self.camera = camera
        
        self.active_dialog = None
        
        self.init_ui()
    
    def init_ui(self):
        self.buttons = []
        
        btn_size = Config.UI_BUTTON_SIZE
        btn_padding = Config.UI_BUTTON_PADDING
        
        platform_rect = pygame.Rect(btn_padding, btn_padding, btn_size, btn_size)
        platform_btn = Button(platform_rect, "P", lambda: self.tool_manager.set_tool("platform"), "Platform Tool (1)")
        platform_btn.active = True
        self.buttons.append(platform_btn)
        
        ground_rect = pygame.Rect(btn_padding*2 + btn_size, btn_padding, btn_size, btn_size)
        ground_btn = Button(ground_rect, "G", lambda: self.tool_manager.set_tool("ground"), "Ground Tool (2)")
        self.buttons.append(ground_btn)
        
        enemy_rect = pygame.Rect(btn_padding*3 + btn_size*2, btn_padding, btn_size, btn_size)
        enemy_btn = Button(enemy_rect, "E", lambda: self.tool_manager.set_tool("enemy"), "Enemy Tool (3)")
        self.buttons.append(enemy_btn)
        
        delete_rect = pygame.Rect(btn_padding*4 + btn_size*3, btn_padding, btn_size, btn_size)
        delete_btn = Button(delete_rect, "X", lambda: self.tool_manager.set_tool("delete"), "Delete Tool (4)")
        self.buttons.append(delete_btn)
        
        grid_rect = pygame.Rect(btn_padding*5 + btn_size*4, btn_padding, btn_size, btn_size)
        grid_btn = Button(grid_rect, "#", lambda: self.grid.toggle_grid(), "Toggle Grid (G)")
        self.buttons.append(grid_btn)
        
        reset_rect = pygame.Rect(btn_padding*6 + btn_size*5, btn_padding, btn_size, btn_size)
        reset_btn = Button(reset_rect, "R", lambda: self.camera.reset(), "Reset Camera (R)")
        self.buttons.append(reset_btn)
        
        exit_rect = pygame.Rect(btn_padding*7 + btn_size*6, btn_padding, btn_size*2, btn_size)
        exit_btn = Button(exit_rect, "Exit", self.return_to_welcome, "Return to Welcome Screen (Esc)")
        self.buttons.append(exit_btn)
        
        save_rect = pygame.Rect(btn_padding*8 + btn_size*8, btn_padding, btn_size*2, btn_size)
        save_btn = Button(save_rect, "Save", self.save_level, "Save Level (Ctrl+S)")
        self.buttons.append(save_btn)
    
    def update(self):
        for button in self.buttons:
            if button.text == "P":
                button.active = isinstance(self.tool_manager.current_tool, PlatformTool)
            elif button.text == "G":
                button.active = isinstance(self.tool_manager.current_tool, GroundTool)
            elif button.text == "E":
                button.active = isinstance(self.tool_manager.current_tool, EnemyTool)
            elif button.text == "X":
                button.active = isinstance(self.tool_manager.current_tool, DeleteTool)
            elif button.text == "#":
                button.active = self.grid.show_grid
    
    def handle_event(self, event):
        if self.active_dialog:
            try:
                consumed = self.active_dialog.check_events(event)
                if hasattr(self.active_dialog, 'active') and not self.active_dialog.active:
                    self.active_dialog = None
                return consumed
            except AttributeError:
                # If dialog was cleared while processing the event
                self.active_dialog = None
                return False
        
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.check_hover(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.check_click(event.pos):
                    return True
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.tool_manager.set_tool("platform")
                return True
            elif event.key == pygame.K_2:
                self.tool_manager.set_tool("ground")
                return True
            elif event.key == pygame.K_3:
                self.tool_manager.set_tool("enemy")
                return True
            elif event.key == pygame.K_4:
                self.tool_manager.set_tool("delete")
                return True
            elif event.key == pygame.K_g:
                self.grid.toggle_grid()
                return True
            elif event.key == pygame.K_r:
                self.camera.reset()
                return True
            elif event.key == pygame.K_ESCAPE:
                print("[LOG] ESC key detected, attempting direct welcome screen transition")
                self.execute_welcome_transition()
                self.return_to_welcome()
                return True
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.save_level()
                return True
            elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
                fm = FileManager(self.level)
                # Instead of blocking, open a LoadLevelDialog in the editor
                def on_load_dialog_closed(ok, fname):
                    if ok and fname:
                        fm.load_level(fname)
                self.active_dialog = LoadLevelDialog(self.level, on_load_dialog_closed)
                return True
    
    def save_level(self):
        def save_callback(result, filename=None):
            if result and filename:
                if not filename.lower().endswith('.json'):
                    filename += '.json'
                fm = FileManager(self.level)
                saved_path = fm.save_level(filename)
                if saved_path:
                    print(f"Level saved to {saved_path}")
                    success_dialog = ModalDialog("Save Successful", [f"{os.path.basename(saved_path)} saved"])
                    success_dialog.add_button("OK", True, color=(50, 120, 50),
                                              x=success_dialog.width//2 - 50,
                                              y=success_dialog.height - 60)
                    self.active_dialog = success_dialog
                else:
                    error_dialog = ModalDialog("Save Failed", ["Error saving level.", "Check console for details."])
                    error_dialog.add_button("OK", True, color=(150, 50, 50),
                                            x=error_dialog.width//2 - 50,
                                            y=error_dialog.height - 60)
                    self.active_dialog = error_dialog
        
        self.active_dialog = SaveDialog(save_callback)
    
    def execute_welcome_transition(self):
        print("[STATE] UI requesting transition to welcome screen")
        try:
            import main
            
            # IMPORTANT: First set the state change requested flag
            main.state_change_requested = main.AppState.WELCOME_SCREEN
            
            if hasattr(main.LevelEditor.instance, 'show_welcome_screen'):
                main.LevelEditor.instance.show_welcome_screen = True
                
            # Give pygame time to process events before posting a new one
            pygame.time.delay(50)
                
            # Create a special exit event to force state change
            # This is to handle the case where the user clicks "Exit/Continue"
            exit_event = pygame.event.Event(pygame.USEREVENT)
            pygame.event.post(exit_event)
            
            # AFTER posting the event, THEN it's safe to clear the dialog
            # This way we won't have a race condition where events try to access
            # the dialog after it's been cleared
            pygame.time.delay(50)
            self.active_dialog = None
                
            print("[STATE] Successfully requested welcome screen transition")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to request state transition: {e}")
            return False
        
    def return_to_welcome(self):
        def exit_callback(result):
            if result:
                # Use the more direct execute_welcome_transition method
                self.execute_welcome_transition()
        
        exit_dialog = ModalDialog(
            "Warning", 
            ["Returning to the welcome screen will", "discard any unsaved changes."]
        )
        
        dialog_width = exit_dialog.width
        exit_dialog.add_button("Cancel", False, color=(80, 80, 80), 
                              x=dialog_width//4 - 50, y=exit_dialog.height - 60)
        exit_dialog.add_button("Continue", True, color=(150, 50, 50), 
                              x=(dialog_width*3)//4 - 50, y=exit_dialog.height - 60)
        exit_dialog.set_callback(exit_callback)
        
        self.active_dialog = exit_dialog
    
    def show_warning_dialog_new(self):
        def new_level_callback(result):
            if result:
                from main import LevelEditor
                editor = LevelEditor.instance
                if editor:
                    editor.show_new_level_dialog()
        
        new_level_dialog = ModalDialog(
            "Warning", 
            ["Creating a new level will discard any", "unsaved changes to the current level."]
        )
        
        dialog_width = new_level_dialog.width
        new_level_dialog.add_button("Cancel", False, color=(80, 80, 80), 
                                   x=dialog_width//4 - 50, y=new_level_dialog.height - 60)
        new_level_dialog.add_button("Continue", True, color=(150, 50, 50), 
                                   x=(dialog_width*3)//4 - 50, y=new_level_dialog.height - 60)
        new_level_dialog.set_callback(new_level_callback)
        
        self.active_dialog = new_level_dialog
    
    def show_new_level_dialog(self):
        """Show a dialog to create a new level using pygame UI"""
        # Dialog states
        CHOOSING_BG = 0
        CHOOSING_FG = 1
        SETTING_CELL_SIZE = 2
        DONE = 3
        
        state = CHOOSING_BG
        cell_size = 32
        dialog_running = True
        
        # Available images
        graphics_dir = os.path.join("resources", "graphics")
        available_images = []
        
        # Make sure the graphics directory exists
        if not os.path.exists(graphics_dir):
            print(f"Warning: Graphics directory not found: {graphics_dir}")
            # Create it if it doesn't exist
            try:
                os.makedirs(graphics_dir)
                print(f"Created directory: {graphics_dir}")
            except:
                print(f"Error creating graphics directory")
        
        # Get available images
        try:
            for file in os.listdir(graphics_dir):
                if file.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    available_images.append(os.path.join(graphics_dir, file))
        except Exception as e:
            print(f"Error reading graphics directory: {e}")
        
        # Check if we have any images
        if not available_images:
            print("No image files found. Please add images to resources/graphics directory.")
            # Show error message
            return False
        
        # Sort by name
        available_images.sort()
        
        # Selected images
        bg_path = None
        fg_path = None
        
        # Dialog surface
        dialog_width = 600
        dialog_height = 400
        dialog_x = (Config.WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (Config.WINDOW_HEIGHT - dialog_height) // 2
        
        dialog_surface = pygame.Surface((dialog_width, dialog_height))
        button_height = 40
        
        # Font
        font = pygame.font.SysFont(None, 24)
        title_font = pygame.font.SysFont(None, 32)
        
        # Create buttons for images
        image_buttons = []
        for i, img_path in enumerate(available_images):
            btn_rect = pygame.Rect(
                50,
                80 + i * (button_height + 10),
                dialog_width - 100,
                button_height
            )
            
            # Just show the filename, not the full path
            btn_text = os.path.basename(img_path)
            
            image_buttons.append({
                'rect': btn_rect,
                'text': btn_text,
                'path': img_path,
                'hover': False
            })
        
        # Cell size buttons
        cell_sizes = [8, 16, 24, 32, 48, 64]
        cell_buttons = []
        for i, size in enumerate(cell_sizes):
            btn_rect = pygame.Rect(
                50 + i * 80,
                200,
                70,
                button_height
            )
            
            cell_buttons.append({
                'rect': btn_rect,
                'size': size,
                'hover': False,
                'selected': size == 32  # Default 32
            })
        
        # Main dialog loop
        clock = pygame.time.Clock()
        
        while dialog_running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Handle mouse motion for hover effects
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
                    
                    # Adjust mouse position for dialog position
                    mouse_x = mouse_pos[0] - dialog_x
                    mouse_y = mouse_pos[1] - dialog_y
                    
                    # Update hover state for image buttons
                    if state in [CHOOSING_BG, CHOOSING_FG]:
                        for btn in image_buttons:
                            btn['hover'] = btn['rect'].collidepoint(mouse_x, mouse_y)
                    
                    # Update hover state for cell size buttons
                    elif state == SETTING_CELL_SIZE:
                        for btn in cell_buttons:
                            btn['hover'] = btn['rect'].collidepoint(mouse_x, mouse_y)
                
                # Handle mouse clicks
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    
                    # Adjust mouse position for dialog position
                    mouse_x = mouse_pos[0] - dialog_x
                    mouse_y = mouse_pos[1] - dialog_y
                    
                    # Handle image button clicks
                    if state == CHOOSING_BG:
                        # Check for btn clicks
                        for btn in image_buttons:
                            if btn['rect'].collidepoint(mouse_x, mouse_y):
                                bg_path = btn['path']
                                state = CHOOSING_FG
                                break
                                
                        # Also check for cancel button
                        cancel_rect = pygame.Rect(
                            dialog_width // 2 - 50,
                            dialog_height - 50,
                            100,
                            40
                        )
                        if cancel_rect.collidepoint(mouse_x, mouse_y):
                            return False
                    
                    elif state == CHOOSING_FG:
                        # Check for btn clicks
                        for btn in image_buttons:
                            if btn['rect'].collidepoint(mouse_x, mouse_y):
                                fg_path = btn['path']
                                state = SETTING_CELL_SIZE
                                break
                                
                        # Also check for cancel button
                        cancel_rect = pygame.Rect(
                            dialog_width // 2 - 50,
                            dialog_height - 50,
                            100,
                            40
                        )
                        if cancel_rect.collidepoint(mouse_x, mouse_y):
                            return False
                    
                    # Handle cell size button clicks
                    elif state == SETTING_CELL_SIZE:
                        for btn in cell_buttons:
                            if btn['rect'].collidepoint(mouse_x, mouse_y):
                                cell_size = btn['size']
                                # Update selected state
                                for b in cell_buttons:
                                    b['selected'] = (b['size'] == cell_size)
                                
                        # Done button at the bottom
                        done_rect = pygame.Rect(
                            dialog_width // 2 - 50,
                            dialog_height - 70,
                            100,
                            40
                        )
                        
                        if done_rect.collidepoint(mouse_x, mouse_y):
                            state = DONE
                            dialog_running = False
            
            # Clear dialog surface
            dialog_surface.fill((50, 50, 50))
            
            # Draw dialog title
            title_text = ""
            if state == CHOOSING_BG:
                title_text = "Select Background Image"
            elif state == CHOOSING_FG:
                title_text = "Select Foreground Image"
            elif state == SETTING_CELL_SIZE:
                title_text = "Set Cell Size"
            
            title_surf = title_font.render(title_text, True, (255, 255, 255))
            title_rect = title_surf.get_rect(centerx=dialog_width//2, y=20)
            dialog_surface.blit(title_surf, title_rect)
            
            # Draw state-specific content
            if state in [CHOOSING_BG, CHOOSING_FG]:
                # Draw image buttons
                for btn in image_buttons:
                    # Draw button background
                    btn_color = (80, 80, 80)
                    if btn['hover']:
                        btn_color = (100, 100, 150)
                    
                    pygame.draw.rect(dialog_surface, btn_color, btn['rect'])
                    pygame.draw.rect(dialog_surface, (150, 150, 150), btn['rect'], 1)
                    
                    # Draw button text
                    text_surf = font.render(btn['text'], True, (255, 255, 255))
                    text_rect = text_surf.get_rect(
                        midleft=(btn['rect'].left + 10, btn['rect'].centery)
                    )
                    dialog_surface.blit(text_surf, text_rect)
                
                # Draw cancel button
                cancel_rect = pygame.Rect(
                    dialog_width // 2 - 50,
                    dialog_height - 50,
                    100,
                    40
                )
                pygame.draw.rect(dialog_surface, (150, 50, 50), cancel_rect)
                pygame.draw.rect(dialog_surface, (150, 150, 150), cancel_rect, 1)
                
                # Draw cancel button text
                cancel_text = font.render("Cancel", True, (255, 255, 255))
                cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
                dialog_surface.blit(cancel_text, cancel_text_rect)
            
            elif state == SETTING_CELL_SIZE:
                # Draw cell size buttons
                for btn in cell_buttons:
                    # Draw button background
                    btn_color = (80, 80, 80)
                    if btn['hover']:
                        btn_color = (100, 100, 150)
                    if btn['selected']:
                        btn_color = (50, 100, 200)
                    
                    pygame.draw.rect(dialog_surface, btn_color, btn['rect'])
                    pygame.draw.rect(dialog_surface, (150, 150, 150), btn['rect'], 1)
                    
                    # Draw button text
                    text_surf = font.render(str(btn['size']), True, (255, 255, 255))
                    text_rect = text_surf.get_rect(center=btn['rect'].center)
                    dialog_surface.blit(text_surf, text_rect)
                
                # Draw done button
                done_rect = pygame.Rect(
                    dialog_width // 2 - 50,
                    dialog_height - 70,
                    100,
                    40
                )
                pygame.draw.rect(dialog_surface, (50, 120, 50), done_rect)
                pygame.draw.rect(dialog_surface, (150, 150, 150), done_rect, 1)
                
                # Draw done button text
                done_text = font.render("Done", True, (255, 255, 255))
                done_text_rect = done_text.get_rect(center=done_rect.center)
                dialog_surface.blit(done_text, done_text_rect)
                
                # Show selected values
                if bg_path:
                    bg_text = font.render(f"Background: {os.path.basename(bg_path)}", True, (200, 200, 200))
                    dialog_surface.blit(bg_text, (50, 100))
                
                if fg_path:
                    fg_text = font.render(f"Foreground: {os.path.basename(fg_path)}", True, (200, 200, 200))
                    dialog_surface.blit(fg_text, (50, 130))
                
                cell_text = font.render(f"Cell Size: {cell_size}px", True, (200, 200, 200))
                dialog_surface.blit(cell_text, (50, 160))
            
            # Draw the dialog to the screen
            from main import LevelEditor
            editor = LevelEditor.instance
            if editor:
                editor.screen.blit(dialog_surface, (dialog_x, dialog_y))
                pygame.display.flip()
            
            # Cap framerate
            clock.tick(60)
        
        # If we have both images, proceed with level creation
        if bg_path and fg_path:
            # Update level settings
            self.level.set_cell_size(cell_size)
            self.grid.set_cell_size(cell_size)
            
            # Clear current level data
            self.level.clear()
            
            # Load the new assets
            from main import LevelEditor
            editor = LevelEditor.instance
            if editor:
                editor.load_assets(bg_path, fg_path)
                editor.has_loaded_level = True
            
            return True
            
        return False
    
    def render(self, surface):
        panel_rect = pygame.Rect(0, 0, Config.WINDOW_WIDTH, Config.UI_PANEL_HEIGHT)
        pygame.draw.rect(surface, Config.UI_BG_COLOR, panel_rect)
        pygame.draw.line(surface, Config.UI_FG_COLOR, (0, Config.UI_PANEL_HEIGHT), (Config.WINDOW_WIDTH, Config.UI_PANEL_HEIGHT))
        
        for button in self.buttons:
            button.render(surface)
        
        font = pygame.font.SysFont(None, 24)
        info_text = f"Level: {self.level.width}x{self.level.height} cells | Cell Size: {self.grid.cell_size}px"
        text_surface = font.render(info_text, True, Config.UI_FG_COLOR)
        text_rect = text_surface.get_rect(midright=(Config.WINDOW_WIDTH - 10, Config.UI_PANEL_HEIGHT - 12))
        surface.blit(text_surface, text_rect)
        
        if self.active_dialog:
            self.active_dialog.render(surface)
import pygame
from editor.config import Config

class Camera:
    def __init__(self, level):
        self.level = level
        self.x = 0
        self.y = 0
        self.drag_start = None
        self.dragging = False
    
    def update(self):
        """Update camera position"""
        # Enforce camera bounds
        max_x = max(0, self.level.width_pixels - Config.WINDOW_WIDTH)
        self.x = max(0, min(self.x, max_x))
    
    def handle_event(self, event):
        """Handle camera control events"""
        if event.type == pygame.KEYDOWN:
            # Camera navigation with arrow keys
            if event.key == pygame.K_LEFT:
                self.x -= 100
            elif event.key == pygame.K_RIGHT:
                self.x += 100
            
            # Reset camera position
            elif event.key == pygame.K_HOME:
                self.x = 0
                self.y = 0
        
        # Camera drag with middle mouse button
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button
                self.drag_start = event.pos
                self.dragging = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:  # Middle mouse button
                self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                dx = self.drag_start[0] - event.pos[0]
                self.x += dx
                self.drag_start = event.pos
    
    def reset(self):
        """Reset camera to origin"""
        self.x = 0
        self.y = 0
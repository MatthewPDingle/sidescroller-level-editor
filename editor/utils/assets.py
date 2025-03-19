import os
import pygame

def load_image(path, alpha=True):
    """Load an image from the given path"""
    try:
        if alpha:
            image = pygame.image.load(path).convert_alpha()
        else:
            image = pygame.image.load(path).convert()
        return image
    except pygame.error as e:
        print(f"Error loading image {path}: {e}")
        # Create a placeholder image
        placeholder = pygame.Surface((32, 32))
        placeholder.fill((255, 0, 255))  # Magenta for missing textures
        return placeholder

def load_sprite_sheet(path, sprite_width, sprite_height, alpha=True):
    """Load a sprite sheet and extract individual frames"""
    try:
        sheet = load_image(path, alpha)
        sheet_width, sheet_height = sheet.get_size()
        
        columns = sheet_width // sprite_width
        rows = sheet_height // sprite_height
        
        sprites = []
        for row in range(rows):
            for col in range(columns):
                x = col * sprite_width
                y = row * sprite_height
                sprite = sheet.subsurface((x, y, sprite_width, sprite_height))
                sprites.append(sprite)
        
        return sprites
    except Exception as e:
        print(f"Error loading sprite sheet {path}: {e}")
        # Create a placeholder sprite
        placeholder = pygame.Surface((sprite_width, sprite_height))
        placeholder.fill((255, 0, 255))  # Magenta for missing textures
        return [placeholder]
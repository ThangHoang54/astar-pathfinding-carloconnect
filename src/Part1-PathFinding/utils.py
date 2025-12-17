import pygame
import os
from settings import ROWS, COLS, GRID_SIZE

# Resets all pathfinding data and rover state while preserving map obstacles
def reset_path_data(grid, path_data, rover):
    """
    Args:
        grid (list[list[Node]]): The 2D grid of Node objects.
        path_data (dict): The dictionary containing path, explored, and frontier lists.
        rover (Survivor): The agent object to reset.

    Returns:
        None
    """
    path_data['smooth_path'] = []
    path_data['start'] = []
    path_data['explored'] = []
    path_data['frontier'] = []
    # Reset Node Costs
    for row in grid:
        for node in row:
            node.g_cost = float('inf')
            node.f_cost = float('inf')
            node.parent = None
    # Reset Rover Pathing
    rover.path = []
    rover.current_waypoint_index = 0
    rover.vel = pygame.math.Vector2(0, 0)

# Removes all walls and obstacles from the grid
def clear_grid(grid):
    """
    Args:
        grid (list[list[Node]]): The 2D grid of Node objects to clear.

    Returns:
        None
    """
    for row in grid:
        for node in row:
            node.is_wall = False

# Populates the grid with obstacles based on a 2D integer array
def load_map_from_array(grid, map_array):
    """
    Args:
        grid (list[list[Node]]): The target 2D grid of Node objects.
        map_array (list[list[int]]): 2D array where 1 represents a wall and 0 represents empty space.

    Returns:
        None
    """
    clear_grid(grid)
    for y, row_data in enumerate(map_array):
        for x, cell_value in enumerate(row_data):
            if 0 <= x < COLS and 0 <= y < ROWS:
                grid[y][x].is_wall = (cell_value == 1)

# Renders a rectangle with a specified transparency level
def draw_transparent_rect(screen, color, rect, alpha):
    """
    Args:
        screen (pygame.Surface): The target surface to draw on.
        color (tuple): The RGB color tuple (r, g, b).
        rect (tuple | pygame.Rect): The dimension tuple (x, y, width, height).
        alpha (int): The transparency level (0 is fully transparent, 255 is opaque).

    Returns:
        None
    """
    s = pygame.Surface((rect[2], rect[3]))  # the size of your rect
    s.set_alpha(alpha)                      # alpha level
    s.fill(color)                           # this fills the entire surface
    screen.blit(s, (rect[0], rect[1]))      # Draw

# Renders text with a background box and border for high contrast visibility
def draw_text(screen, text, x, y, font, text_color):
    """
    Args:
        screen (pygame.Surface): The target surface to draw on.
        text (str): The string content to display.
        x (int): The x-coordinate for the top-left corner.
        y (int): The y-coordinate for the top-left corner.
        font (pygame.font.Font): The font object used for rendering.
        text_color (tuple): The RGB color tuple for the text.

    Returns:
        None
    """
    surf = font.render(text, True, text_color)
    rect = surf.get_rect(topleft=(x, y))
    
    # Draw background box (slightly larger than text)
    bg_rect = rect.inflate(4, 2) 
    pygame.draw.rect(screen, (0, 0, 0), bg_rect, 1) # Black border

    screen.blit(surf, rect)

# Visualizes the G, H, and F costs on a specific node in the grid
def draw_node_costs(screen, node, font):
    """
    Args:
        screen (pygame.Surface): The target surface to draw on.
        node (Node): The grid node containing cost attributes (g_cost, h_cost, f_cost).
        font (pygame.font.Font): The font object used for rendering the numbers.

    Returns:
        None
    """
    if node.f_cost == float('inf'): return

    # Coordinates
    x = node.x * GRID_SIZE
    y = node.y * GRID_SIZE
    
    # 1. G-Cost (Top Left) - Distance from Start
    # color: Blue
    draw_text(screen, f"{node.g_cost:.1f}", x + 2, y + 2, font, (0, 0, 150))

    # 2. H-Cost (Top Right) - Distance to End
    # color: Red
    h_text = f"{node.h_cost:.1f}"
    h_surf = font.render(h_text, True, (150, 0, 0))
    # Calculate X position to align right
    h_x = x + GRID_SIZE - h_surf.get_width() - 4 
    draw_text(screen, h_text, h_x, y + 2, font, (150, 0, 0))

    # 3. F-Cost (Center) - Total Priority
    # color: Black
    f_text = f"{node.f_cost:.1f}"
    f_surf = font.render(f_text, True, (0, 0, 0))
    
    cx = x + (GRID_SIZE - f_surf.get_width()) // 2
    cy = y + (GRID_SIZE - f_surf.get_height()) // 2 + 8 # Slightly lower
    
    draw_text(screen, f_text, cx, cy, font, (0, 0, 0))

# Safely loads an image from disk and scales it to the specified size
def load_and_scale(filename, size):
    """
    Args:
        filename (str): Path to the image file.
        size (int): The target width/height to scale the image to.

    Returns:
        pygame.Surface | None: The scaled image surface, or None if the file is missing.
    """
    if os.path.exists(filename):
        img = pygame.image.load(filename)
        return pygame.transform.scale(img, (size, size))
    else:
        print(f"Warning: {filename} not found. Using shapes instead.")
        return None

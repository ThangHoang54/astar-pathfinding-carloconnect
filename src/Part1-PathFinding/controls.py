import pygame
from settings import *
from pathfinding import find_path
from maps import MAPS
from utils import clear_grid, reset_path_data, load_map_from_array

# Processes user input events (keyboard/mouse) and updates game state accordingly
def handle_input(events, grid, survivor, path_data, ui_data):
    """
    Args:
        events (list[pygame.event.Event]): List of pygame events captured this frame.
        grid (list[list[Node]]): The 2D grid of Node objects.
        survivor (Survivor): The player agent object.
        path_data (dict): Dictionary storing pathfinding state data.
        ui_data (dict): Dictionary storing UI messages and status.

    Returns:
        tuple: (bool, generator | None)
            - True if the game should continue running, False to quit.
            - A generator object for the pathfinding algorithm if initiated, otherwise None.
    """
    mx, my = pygame.mouse.get_pos()
    grid_x, grid_y = mx // GRID_SIZE, my // GRID_SIZE

    algo_to_start = None

    for event in events:
        if event.type == pygame.QUIT:
            return False, None

        # Keyboard
        if event.type == pygame.KEYDOWN:
            # Q: Quit
            if event.key == pygame.K_q:
                return False, None
            
            # C: Clear All (Walls + Path)
            if event.key == pygame.K_c:
                clear_grid(grid)
                reset_path_data(grid, path_data, survivor)
                path_data['start'] = None
                path_data['goal'] = None
                ui_data['error_message'] = "Map Cleared"
            
            # R: Reset Optimal Path
            if event.key == pygame.K_r:
                reset_path_data(grid, path_data, survivor)
                ui_data['error_message'] = "Path Reset"
            
            # U: Remove Obstacle
            if event.key == pygame.K_u:
                if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
                    grid[grid_y][grid_x].is_wall = False

            # 1-5: Generate Mazes
            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                level = event.key - pygame.K_0 # Convert key to int (1-5)

                if level in MAPS:
                    # name, map data, start x, start 2\y
                    map_name, map_data, sx, sy = MAPS[level]

                    reset_path_data(grid, path_data, survivor)
                    load_map_from_array(grid, map_data)
                    
                    # Set Survivor start position
                    survivor.pos.x = sx * GRID_SIZE + GRID_SIZE // 2
                    survivor.pos.y = sy * GRID_SIZE + GRID_SIZE // 2

                    path_data['start'] = None
                    path_data['goal'] = None
                    
                    ui_data['error_message'] = f"Map Loaded: {map_name}"

            # SPACE: Execute Pathfinding (Start Moving)
            if event.key == pygame.K_SPACE:
                # 1. Determine Start (Survivor position)
                start_x = int(survivor.pos.x // GRID_SIZE)
                start_y = int(survivor.pos.y // GRID_SIZE)
                
                # 2. Check Goal
                if not path_data['goal']:
                    ui_data['error_message'] = "NO CAMPFIRE SIGHTED!"
                    #  ui_data['error_timer'] = 90
                else:
                    start_node = grid[start_y][start_x]
                    target_node = path_data['goal']
                    path_data['start'] = start_node

                    algo_to_start = find_path(grid, start_node, target_node)
                    ui_data['error_message'] = "CALCULATING PATH..."


        # --- Mouse Interaction ---
        # Left Click: Add Tree
        if pygame.mouse.get_pressed()[0]: 
                if my < HEIGHT and 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
                    # Do not draw on top of agent or goal
                    is_rover = (int(survivor.pos.x // GRID_SIZE) == grid_x and int(survivor.pos.y // GRID_SIZE) == grid_y)
                    is_goal = (path_data['goal'] and path_data['goal'].x == grid_x and path_data['goal'].y == grid_y)
                    
                    if not is_rover and not is_goal:
                        grid[grid_y][grid_x].is_wall = True

        # Right Click: Set Target (Goal)
        elif pygame.mouse.get_pressed()[2]:
                if my < HEIGHT and 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
                    target_node = grid[grid_y][grid_x]
                    if not target_node.is_wall:
                        path_data['goal'] = target_node
                        ui_data['error_message'] = "CAMPFIRE SPOTTED"
                       
                    else:
                        ui_data['error_message'] = "CANNOT BUILD FIRE ON TREE"
                       
    return True, algo_to_start
import pygame
from settings import *
from entities.nodes import Node
from entities.entities import Survivor
from draw import render_game
from controls import handle_input
from utils import load_and_scale

# Main Loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH + SIDEBAR_WIDTH, HEIGHT + TOOLBAR_HEIGHT))
    pygame.display.set_caption("A* Pathfinding")
    clock = pygame.time.Clock()

    # Load assets
    assets = {
        'survivor': load_and_scale("img/friends.png", GRID_SIZE*0.5),
        'tree':  load_and_scale("img/tree.png", GRID_SIZE),
        'campfire':  load_and_scale("img/tent.png", GRID_SIZE)
    }

    grid = [[Node(x, y) for x in range(COLS)] for y in range(ROWS)]
    survivor = Survivor(GRID_SIZE/2, GRID_SIZE/2)
    
    # State Dictionaries (Shared between Control and Draw)
    path_data = {
        'smooth_path': [],
        'explored': [],
        'frontier': [],
        'start': None,
        'goal': None,
        'total_cost': 0.0
    }
    
    ui_data = {
        'error_message': "System Online - Awaiting Input",
    }

    # variable to hold the active search algorithm
    path_finder_algo = None

    running = True
    while running:
        # Handle Input
        events = pygame.event.get()

        running, new_algo = handle_input(events, grid, survivor, path_data, ui_data)

        if new_algo:
            path_finder_algo = new_algo # Start new search
            path_data['total_cost'] = 0.0

        if path_finder_algo:
            try:
                # Run one step of the algorithm
                path, visited, frontier = next(path_finder_algo)
                path_data['smooth_path'] = path
                path_data['explored'] = visited
                path_data['frontier'] = frontier
                
                # If we found a path, stop the animation
                if path:
                    survivor.set_path(path) # Start moving survivor
                    path_finder_algo = None
                    ui_data['error_message'] = "PATH FOUND - RETURNING CAMPFIRE"

                    path_data['total_cost'] = path[-1].g_cost
                    
            except StopIteration:
                # Finish algorithm
                path_finder_algo = None 
                
                # Check if we actually have a path
                if path_data['smooth_path']:
                    pass 
                else:
                    ui_data['error_message'] = "PATH BLOCKED - NO ROUTE"
                   
        # Update Physics
        survivor.update()

        # Draw Screen
        render_game(screen, grid, survivor, path_data, ui_data, assets)
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    # Call the main function to execute the program
    main()
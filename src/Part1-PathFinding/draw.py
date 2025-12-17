import pygame
from settings import *
from utils import draw_node_costs, draw_text, draw_transparent_rect

# Main loop to render the grid, game entities, bottom toolbar, and sidebar legend
def render_game(screen, grid, survivor, path_data, ui_data, assets):
    """
    Args:
        screen (pygame.Surface): The main display window surface.
        grid (list[list[Node]]): The 2D array of Node objects representing the map.
        survivor (Survivor): The player/agent object.
        path_data (dict): Contains lists of nodes for 'explored', 'frontier', 'smooth_path', 'start', and 'goal'.
        ui_data (dict): Contains UI state information.
        assets (dict): A dictionary of loaded pygame images (keys: 'tree', 'survivor', 'campfire').

    Returns:
        None
    """
    screen.fill(BG_COLOR)

    # Initialize font for costs
    cost_font = pygame.font.SysFont("Arial", 11, bold=True)

    # Draw Grid Lines
    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRID_LINE_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRID_LINE_COLOR, (0, y), (WIDTH, y))

    # Draw Trees
    for row in grid:
        for node in row:
            if node.is_wall:
                rect = (node.x * GRID_SIZE, node.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if assets['tree']:
                    screen.blit(assets['tree'], rect)
                else:
                    pygame.draw.rect(screen, WALL_COLOR, rect)

    # Draw Explored Nodes
    for node in path_data['explored']:
        if not node.is_wall and node != path_data['start'] and node != path_data['goal']: # Do not draw over walls
            rect = (node.x * GRID_SIZE, node.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            draw_transparent_rect(screen, EXPLORED_COLOR, rect, 100)
            pygame.draw.rect(screen, GRID_LINE_COLOR , rect, 1)
            # Display Costs
            draw_node_costs(screen, node, cost_font)

    # Draw Frontier Nodes
    for node in path_data['frontier']:
        if not node.is_wall and node != path_data['goal']:
            rect = (node.x * GRID_SIZE, node.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            draw_transparent_rect(screen, FRONTIER_COLOR, rect, 180)
            pygame.draw.rect(screen, GRID_LINE_COLOR, rect, 1)
            # Display Costs
            draw_node_costs(screen, node, cost_font)
        
    # Draw Optimal Path
    for node in path_data['smooth_path']:
        if node != path_data['start'] and node != path_data['goal']:
            rect = (node.x * GRID_SIZE, node.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            draw_transparent_rect(screen, PATH_COLOR, rect, 200)
            pygame.draw.rect(screen, GRID_LINE_COLOR, rect, 2)
            # Display Costs
            draw_node_costs(screen, node, cost_font)

    # Draw Start Node
    if path_data['start']:
        n = path_data['start']
        rect = (n.x * GRID_SIZE, n.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        # Draw start position
        draw_transparent_rect(screen, SURVIVOR_COLOR, rect, 120)
        pygame.draw.rect(screen, GRID_LINE_COLOR, rect, 1)
        
    # Draw Target Node
    if path_data['goal']:
        n = path_data['goal']
        rect = (n.x * GRID_SIZE, n.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        # Draw target (campfire)
        draw_transparent_rect(screen, CAMPFIRE_COLOR, rect, 50)
        if assets['campfire']:
            screen.blit(assets['campfire'], rect)
        else:
            pygame.draw.rect(screen, CAMPFIRE_COLOR, rect)
            
    # Draw Survivor Agent
    survivor.draw(screen, assets['survivor'])

    # Draw Bottom UI Panel
    # ==========================
    ui_rect = pygame.Rect(0, HEIGHT, WIDTH, TOOLBAR_HEIGHT)
    pygame.draw.rect(screen, UI_BG, ui_rect)
    pygame.draw.line(screen, UI_BORDER, (0, HEIGHT), (WIDTH, HEIGHT), 3)

    # Fonts
    font_main = pygame.font.SysFont("Courier New", 14, bold=True)
    font_sub = pygame.font.SysFont("Courier New", 12, bold=False)
    font_legend = pygame.font.SysFont("Arial", 10, bold=True)

    # Calculate the vertical center of the toolbar
    mid_y = HEIGHT + (TOOLBAR_HEIGHT // 2)
    row_offset = 12  
    # Vertical Separator Lines
    sep_top = HEIGHT + 10
    sep_bot = HEIGHT + TOOLBAR_HEIGHT - 10
    
    # Left Side: Controls
    sep_x1 = 460
    pygame.draw.line(screen, UI_BORDER, (sep_x1, sep_top), (sep_x1, sep_bot), 2)

    # Row 1: Primary Actions
    row1_surf = font_main.render("L-CLICK: PLANT | R-CLICK: GOAL | SPACE: START", True, TEXT_COLOR)
    screen.blit(row1_surf, (15, mid_y - row_offset - row1_surf.get_height()//2))

    # Row 2: Secondary Actions (Dimmer color)
    dim_color = (180, 160, 140)
    row2_text = "C: CLEAR | R: RESET | 1-5: MAP GEN | U: UNDO TREE"
    row2_surf = font_sub.render(row2_text, True, dim_color)
    screen.blit(row2_surf, (15, mid_y + row_offset - row2_surf.get_height()//2))

    # Center: Visual Legend for Costs
    sep_x2 = 720
    pygame.draw.line(screen, UI_BORDER, (sep_x2, sep_top), (sep_x2, sep_bot), 2)
    
    # Label "Cost Metrics"
    label_surf = font_sub.render("NODE METRICS:", True, (180, 160, 140))
    screen.blit(label_surf, (sep_x1 + 15, mid_y - 8)) # Slightly centered

    # Draw a Sample "Node" Box
    sample_size = 40
    sample_x = sep_x1 + 120
    sample_y = mid_y - (sample_size // 2)

    sample_rect = pygame.Rect(sample_x, sample_y, sample_size, sample_size)
    # Draw sample node background
    pygame.draw.rect(screen, (200, 190, 150), sample_rect) 
    pygame.draw.rect(screen, UI_BORDER, sample_rect, 2)

    # Draw Sample Metrics inside the box
    # G (Top Left - Blue)
    screen.blit(font_legend.render("G", True, (0, 0, 150)), (sample_x + 3, sample_y + 2))
    # H (Top Right - Red)
    h_surf = font_legend.render("H", True, (150, 0, 0))
    screen.blit(h_surf, (sample_x + sample_size - h_surf.get_width() - 3, sample_y + 2))
    # F (Center - Black)
    f_surf = font_legend.render("F", True, (0, 0, 0))
    screen.blit(f_surf, (sample_x + (sample_size//2) - (f_surf.get_width()//2), sample_y + (sample_size//2)))

    # Explanations next to the box
    screen.blit(font_legend.render("G: Dist. from Start", True, (100, 100, 255)), (sample_x + 50, sample_y))
    screen.blit(font_legend.render("H: Dist. to End", True, (255, 100, 100)), (sample_x + 50, sample_y + 12))
    screen.blit(font_legend.render("F: Total Cost", True, (200, 200, 200)), (sample_x + 50, sample_y + 24))

    # Right Side: Status and Logs Info
    if path_data['smooth_path']:
        total = path_data['smooth_path'][-1].g_cost
        cost_msg = f"PATH COST: {total:.2f}"
        cost_surf = font_main.render(cost_msg, True, PATH_COLOR)
        # Right align
        screen.blit(cost_surf, (WIDTH - cost_surf.get_width() - 20, mid_y - row_offset - cost_surf.get_height()//2))
    
    # Status Message
    msg = ui_data['error_message']
    if msg:
        status_color = TEXT_WARN if "Blocked" in msg or "Lost" in msg else (100, 255, 100)
        status_surf = font_main.render(msg, True, status_color)
        
        screen.blit(status_surf, (WIDTH - status_surf.get_width() - 20, mid_y + row_offset - status_surf.get_height()//2))
    else:
        # Default Idle State
        idle_surf = font_sub.render("AWAITING COMMAND...", True, (100, 100, 100))
        screen.blit(idle_surf, (WIDTH - idle_surf.get_width() - 20, mid_y + row_offset - idle_surf.get_height()//2))

    # Draw Right Sidebar
    # =====================
    # Sidebar covers full height
    sidebar_rect = pygame.Rect(WIDTH, 0, SIDEBAR_WIDTH, HEIGHT + TOOLBAR_HEIGHT)
    pygame.draw.rect(screen, UI_BG, sidebar_rect)
    pygame.draw.line(screen, UI_BORDER, (WIDTH, 0), (WIDTH, HEIGHT + TOOLBAR_HEIGHT), 3)

    # Sidebar Header
    item_font = pygame.font.SysFont("Courier New", 14, bold=True)
    
    # Legend Items
    legend_items = [
        ("SURVIVOR (AGENT)", SURVIVOR_COLOR, assets['survivor']),
        ("CAMPFIRE (GOAL)", CAMPFIRE_COLOR, assets['campfire']),
        ("TREE (OBSTACLE)", LEAF_COLOR, assets['tree']),
        ("OPTIMAL PATH", PATH_COLOR, None),
        ("EXPLORED NODE", EXPLORED_COLOR, None),
        ("FRONTIER NODE", FRONTIER_COLOR, None),
        ("START NODE", SURVIVOR_COLOR, None)
    ]

    start_y = 70
    gap_y = 50
    icon_size = 30

    for i, (text, color, asset) in enumerate(legend_items):
        current_y = start_y + i * gap_y
        
        # Draw Icon
        icon_rect = pygame.Rect(WIDTH + 30, current_y, icon_size, icon_size)
        
        if asset:
            # Scale asset to fit icon size
            scaled_asset = pygame.transform.scale(asset, (icon_size, icon_size))
            screen.blit(scaled_asset, icon_rect)
        else:
            # Draw colored rectangle
            pygame.draw.rect(screen, color, icon_rect)
            pygame.draw.rect(screen, UI_BORDER, icon_rect, 1)

        # Draw Text
        text_surf = item_font.render(text, True, TEXT_COLOR)
        text_y = current_y + (icon_size - text_surf.get_height()) // 2
        screen.blit(text_surf, (WIDTH + 30 + icon_size + 15, text_y))

    pygame.display.flip()
# Environment (Night Theme)
BG_COLOR = (15, 20, 15)        # Dark Green (Night Forest)
GRID_LINE_COLOR = (30, 45, 30) # Faint moonlit lines
WALL_COLOR = (60, 40, 20)      # Tree Trunk Brown
LEAF_COLOR = (20, 100, 40)     # Pine Needle Green

# Pathfinding (Torchlight & Warmth)
EXPLORED_COLOR = (100, 100, 40)  # Dim Torchlight (Faint Yellow overlay)
FRONTIER_COLOR = (200, 180, 60)  # Edge of Light (Bright Lantern)
PATH_COLOR = (255, 140, 0)       # Optimal Path (Orange)

# Entities
SURVIVOR_COLOR = (152, 251, 152) # Pale Green (Hiker)
CAMPFIRE_COLOR = (255, 60, 0)    # Roaring Fire Red

# Panel UI (Toolbar)
UI_BG = (40, 30, 20)           # Wood Background
UI_BORDER = (140, 100, 60)     # Light Wood Border
TEXT_COLOR = (220, 200, 160)   # Parchment/Paper Text
TEXT_WARN = (255, 100, 100)    # Red

# Constants
WIDTH, HEIGHT = 1000, 700
GRID_SIZE = 50
COLS, ROWS = WIDTH // GRID_SIZE, HEIGHT // GRID_SIZE
TOOLBAR_HEIGHT = 100

# Sidebar Configuration
SIDEBAR_WIDTH = 250
WINDOW_WIDTH = WIDTH + SIDEBAR_WIDTH
WINDOW_HEIGHT = HEIGHT + TOOLBAR_HEIGHT
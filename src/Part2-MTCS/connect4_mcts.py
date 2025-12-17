import pygame
import sys
import math
import random

# ============================================================
#              PART 1 - GAME CONSTANTS AND COLORS
# ============================================================
# In Connect 4, the board has 6 rows and 7 columns.
ROWS = 6
COLS = 7

EMPTY = 0      # No piece in this cell
PLAYER1 = 1    # Player 1 piece (red)
PLAYER2 = 2    # Player 2 piece (yellow)

# Visual settings
SQUARESIZE = 100
RADIUS = SQUARESIZE // 2 - 8
STROKE_WIDTH = 3

# Layout dimension
PANEL_WIDTH = 380             
BOARD_WIDTH = COLS * SQUARESIZE
WIDTH = PANEL_WIDTH + BOARD_WIDTH
HEIGHT = (ROWS + 2) * SQUARESIZE
SIZE = (WIDTH, HEIGHT)

# Colors (CarloConnect Theme)
BOARD_COLOR = (59, 112, 163)      # Blue board background
BG_COLOR = (255, 255, 255)        # White background
SLOT_BG = (255, 255, 255)         # for empty hold
PANEL_BG = (245, 245, 250)        # Light Grey for Panel
SEPARATOR_COLOR = (200, 200, 200) # Line between panel and board

PLAYER1_COLOR = (208, 45, 28)     # Deep Red discs for player 1
PLAYER2_COLOR = (244, 208, 0)     # Golden Yellow discs for player 2
TEXT_COLOR = (0, 0, 0)            # Black text
HIGHLIGHT_COLOR = (50, 50, 50)    # Dark Grey ring for last move
WIN_LINE_COLOR = (0, 255, 0)      # Green ring for winning line

# Bar Chart Analyse Colors
BAR_BG = (220, 220, 220)
BAR_BEST = (0, 255, 0)           # Green for the selected move

FPS = 60
MCTS_ITERATIONS = 1000 # Better decision

# ============================================================
#              PART 2 - CONNECT 4 STATE CLASS
# ============================================================
class Connect4State:
    """
    This class represents a Connect 4 game state.

    It contains:
    - The board, a list of lists of integers.
    - The current player who should move next.

    I will keep all the game logic here, but again this is not a requirement so feel free:
    - Getting legal moves
    - Applying a move
    - Checking for a win or a draw
    """
    def __init__(self, board=None, current_player=PLAYER1, last_move=None):
        """
        Constructor for the game state.

        board:
            Either None (start a new empty board)
            or an existing 2D list to copy.

        current_player:
            Either PLAYER1 or PLAYER2.
        """
        if board is None:
            # Create an empty board with ROWS x COLS filled with EMPTY
            self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        else:
            # Make a deep copy of the board so we do not modify the original
            self.board = [row[:] for row in board]

        self.current_player = current_player
        self.last_move = last_move # (row, col) of the last piece dropped

    def clone(self):
        """
        Create a new Connect4State with the same board, current player, player last move.

        Useful in MCTS when we want to simulate moves without
        changing the original game state.
        """
        return Connect4State(self.board, self.current_player, self.last_move)

    def get_legal_moves(self):
        """
        Return a list of columns (indices from 0 to COLS - 1)
        where a piece can still be dropped.

        A column is legal if its top cell (row 0) is EMPTY !!!! This is very important in the game logic
        """
        moves = []
        for c in range(COLS):
            if self.board[0][c] == EMPTY:
                moves.append(c)
        return moves

    def make_move(self, col):
        """
        Drop a piece for the current player in the given column.

        If the column is valid:
            - The piece will fall to the lowest available row.
            - The current player will switch to the other player.
            - The function returns True.

        If the column is full:
            - The function returns False and does nothing.
        """
        for r in range(ROWS - 1, -1, -1):  # Start from bottom row and go up
            if self.board[r][col] == EMPTY:
                self.board[r][col] = self.current_player
                self.last_move = (r, col) # Store this for drawing the highlight
                # Switch to the other player
                self.current_player = PLAYER1 if self.current_player == PLAYER2 else PLAYER2
                return True
        return False  # Column was full
    
    def check_winner(self):
        """
        Check if there is a winner on the board.
        Returns: PLAYER1, PLAYER2, or None
        """
        # We can reuse get_winning_line logic to keep it DRY
        line_info = self.get_winning_line()
        if line_info:
            winner, _, _ = line_info
            return winner
        return None

    def get_winning_line(self):
        """
        Check if there is a winner on the board.

        Right, we need to look for 4 equal, non-empty pieces in:
        - Horizontal lines
        - Vertical lines
        - Diagonals from top left to bottom right
        - Diagonals from bottom left to top right\
        This is very important.

        Returns:
            (winner_id, [(r1,c1), (r2,c2), (r3,c3), (r4,c4)], type_string)
            or None if no winner.
        """

        # Horizontal check
        for r in range(ROWS):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r][c + i] == piece for i in range(4)):
                        return piece, [(r, c+i) for i in range(4)], "Horizontal"

        # Vertical check
        for c in range(COLS):
            for r in range(ROWS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r + i][c] == piece for i in range(4)):
                        return piece, [(r+i, c) for i in range(4)], "Vertical"

        # Diagonal check (top left to bottom right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r + i][c + i] == piece for i in range(4)):
                        return piece, [(r+i, c+i) for i in range(4)], "Diagonal"

        # Diagonal check (bottom left to top right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r - i][c + i] == piece for i in range(4)):
                        return piece, [(r-i, c+i) for i in range(4)], "Diagonal"

        # No winner found
        return None
    
    def check_winning_move(self, col, player_check):
        """
        Checks whether placing a piece for the given player in the specified
        column would result in an immediate win.

        The move is simulated by temporarily dropping a piece into the lowest
        available row, evaluating all four connect-four directions, and then
        restoring the board state.

        Arguments:
            col (int): Column index to test.
            player_check (int): Player identifier.

        Returns:
            bool: True if the move produces a win; False otherwise or if the
            column is full.
        """
        # Find the valid row
        row = -1
        for r in range(ROWS - 1, -1, -1):
            if self.board[row][col] == EMPTY:
                row = r
                break
        
        if row == -1: 
            return False  # Column full

        # Place piece temporarily
        self.board[row][col] = player_check

        # Check all 4 directions
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        won = False

        for dr, dc in directions:
            count = 1  # Start with the piece we just placed
            
            # Check Positive Direction
            for i in range(1, 4):
                r_next, c_next = row + dr * i, col + dc * i
                if 0 <= r_next < ROWS and 0 <= c_next < COLS and self.board[r_next][c_next] == player_check:
                    count += 1
                else:
                    break # Stop counting if mismatch or out of bounds
            
            # Check Negative Direction
            for i in range(1, 4):
                r_prev, c_prev = row - dr * i, col - dc * i
                if 0 <= r_prev < ROWS and 0 <= c_prev < COLS and self.board[r_prev][c_prev] == player_check:
                    count += 1
                else:
                    break
            
            if count >= 4:
                won = True
                break

        # Backtrack
        self.board[row][col] = EMPTY    
        return won

    def is_full(self):
        """
        Check if the board is full.

        If the top row has no EMPTY cells, then no more moves can be played.
        """
        return all(self.board[0][c] != EMPTY for c in range(COLS))

    def is_terminal(self):
        """
        Check if the game is over.

        The game is terminal if:
        - someone won, or
        - the board is full (draw).
        """
        if self.check_winner() is not None:
            return True
        if self.is_full():
            return True
        return False

# ============================================================
#                 PART 3 - MCTS EXPLANATION
# ============================================================
"""
Let me now explain the Monte Carlo Tree Search (MCTS) algorithm that we will use
to suggest a good move as a hint for the current player.

MCTS is built on 4 main steps that are repeated many times:

1. SELECTION
   - Start from the root node that represents the current game state.
   - If the node has already been visited and fully expanded,
     we use a formula called UCT (Upper Confidence bound applied to Trees)
     to pick the child that balances:
        * Exploitation: children that won more often in the past.
        * Exploration: children that have been visited fewer times.
   - We follow this path of best children until we reach a node that:
        * is not fully expanded, or
        * represents a terminal game state (win, loss, or draw).

2. EXPANSION
   - If the selected node is not terminal, we can add a new child.
   - A child corresponds to playing one of the moves that has not been tried yet.
   - We pick one untried move, apply it to a copy of the game state,
     and create a new child node that stores this new state.

3. SIMULATION (also called ROLLOUT)
   - From the newly created child state, we play a random game until the end.
   - That means we randomly select legal moves until we reach a win, loss, or draw.
   - At the end we know the result:
        * The root player wins, loses, or it is a draw.
   - We convert this result into a numeric reward:
        * 1.0 for a win for the root player
        * 0.0 for a loss for the root player
        * 0.5 for a draw

4. BACKPROPAGATION
   - We then walk back from the simulation node up to the root node.
   - For each node on this path we:
        * Increase the visit count.
        * Add the reward to the node's total wins.
   - This way, each node stores:
        * How many times we visited it.
        * How many wins the root player got through this node.

After doing many iterations of these four steps:
   - The root node will have some children, each corresponding to a possible move.
   - Each child has a visit count and a total win count.
   - We can then pick the child that has the most visits.
   - The move that leads to that child is our suggested move.

The main idea:
   - Random simulations plus statistics guide us to good moves.
   - More iterations usually gives a smarter suggestion.
"""

# ============================================================
#              PART 4 - MCTS DATA STRUCTURES AND CODE
# ============================================================
class MCTSNode:
    """
    Node in the MCTS tree.

    It stores:
    - state: a Connect4State instance
    - parent: parent node in the tree (None for root)
    - move: the move (column index) that led from the parent state to this state
    - children: list of child MCTSNode objects
    - visits: how many times this node was visited in the search
    - wins: total reward from the root player's perspective
    """

    def __init__(self, state, parent=None, move=None):
        self.state = state          # Game state at this node
        self.parent = parent        # Parent node
        self.move = move            # Move that led to this node from parent
        self.children = []          # List of child MCTSNode instances
        self.visits = 0             # Number of times this node has been visited
        self.wins = 0.0             # Sum of rewards from root player's point of view

    def is_fully_expanded(self):
        """
        Check if this node has created children for all legal moves.

        If the state is terminal, we consider it fully expanded,
        because there are no moves to expand.

        Otherwise:
        - We get all legal moves from this state.
        - We compare them with the moves that are already used by children.
        - If every legal move has a child, then the node is fully expanded.
        """
        if self.state.is_terminal():
            return True

        child_moves = {child.move for child in self.children}
        legal_moves = set(self.state.get_legal_moves())
        # Node is fully expanded if:
        # - the number of children matches the number of legal moves
        # - and every legal move already has a child
        return legal_moves.issubset(child_moves) and len(legal_moves) == len(child_moves)

    def best_child(self, c_param=1.4):
        """
        Select a child using the UCT formula.

        UCT score for a child:
            exploit = wins / visits
            explore = sqrt( 2 * ln(parent_visits) / child_visits )
            score = exploit + c_param * explore

        - exploit encourages moves that have good win ratio.
        - explore encourages trying moves that are less visited.

        c_param (exploration constant) controls how much we explore.
        A common choice is around 1.4 (square root of 2).

        If a child has never been visited (visits == 0),
        we treat its score as infinity to ensure it is explored at least once.
        """
        best_score = float("-inf")
        best_children = []

        for child in self.children:
            if child.visits == 0:
                # Encourage at least one visit for every child
                score = float("inf")
            else:
                exploit = child.wins / child.visits
                parent_visits = self.visits if self.visits > 0 else 1
                explore = math.sqrt(2 * math.log(parent_visits) / child.visits)
                score = exploit + c_param * explore

            # Keep track of the best score and all children that achieve it
            if score > best_score:
                best_score = score
                best_children = [child]
            elif score == best_score:
                best_children.append(child)

        # If several children tie, pick one at random
        return random.choice(best_children)

    def most_visited_child(self):
        """
        After MCTS finishes, we want to pick the move that was explored the most.

        This function returns the child with the highest visit count.
        If there are no children (no moves), returns None.
        """
        if not self.children:
            return None
        return max(self.children, key=lambda c: c.visits)

def rollout(state):
    """
    Performs a heuristic rollout (simulation) from the given game state
    until a terminal position is reached.

    The rollout is executed on a cloned state and follows a simple policy:
        1. Play an immediate winning move if available.
        2. Block the opponent’s immediate winning move if necessary.
        3. Otherwise, select a random legal move.

    Arguments:
        state: Starting Connect-4 game state.

    Returns:
        int or None:
            The winning player identifier if a win occurs,
            or None if the rollout ends in a draw.
    """
    temp_state = state.clone()

    # Play moves until the game is over
    while not temp_state.is_terminal():
        legal_moves = temp_state.get_legal_moves()
        if not legal_moves:
            break  # Draw

        # Smart rollout
        chosen_move = None
        current_p = temp_state.current_player
        opponent = PLAYER1 if current_p == PLAYER2 else PLAYER2
        
        # Check for immediate win
        for move in legal_moves:
            if temp_state.check_winning_move(move, current_p):
                chosen_move = move
                break

         # Check for immediate Block
        if chosen_move is None:
            for move in legal_moves:
                if temp_state.check_winning_move(move, opponent):
                    chosen_move = move
                    break
        
        # Fallback to Random
        if chosen_move is None:
            chosen_move = random.choice(legal_moves)
            
        temp_state.make_move(chosen_move)
    
    return temp_state.check_winner()

    # # Determine result
    # winner = temp_state.check_winner()
    # if winner is None:
    #     return 0.5 # Draw
    # if winner == root_player:
    #     return 1.0 # Win for MCTS root
    # else:
    #     return 0.0 # Loss for MCTS root

def mcts_search(root_state, n_iter=400):
    """
    Run MCTS from the given root_state and return the best move.

    Arguments:
        root_state:
            The current game state from which MCTS is performed.
        n_iter (int):
            Number of MCTS iterations to run.

    Returns:
        best_move (int or None):
            Column index of the selected move, or None if no legal move exists.
        stats (dict):
            Per-move statistics including visit count, win rate, and UCB score.

    Steps:
        1. Create a root MCTSNode that holds a copy of root_state.
        2. For n_iter iterations:
            a) Selection (using UCB)
            b) Expansion
            c) Simulation (heuristic rollout)
            d) Backpropagation
        3. Return the move of the most visited child of the root.
    """
    # If the game is already finished, we return no move
    if root_state.is_terminal():
        return None, {}
        
    # The root player is the player who is about to move in root_state
    root_player = root_state.current_player
    # Create a root node for the MCTS tree
    root_node = MCTSNode(root_state.clone())

    for _ in range(n_iter):
        # # Prevent window freezing during long calculations
        # pygame.event.pump()

        # Start at the root node and work on a fresh copy of root_state
        node = root_node
        state = root_state.clone()

        # 1. SELECTION
        while node.children and node.is_fully_expanded() and not state.is_terminal():
            node = node.best_child()
            # Apply the move that led to this child to our simulation state
            if node.move is not None:
                state.make_move(node.move)

        # 2. EXPANSION
        if not state.is_terminal():
            legal_moves = state.get_legal_moves()
            existing_moves = {child.move for child in node.children}
            # Untried moves are legal moves without a child yet
            untried_moves = [m for m in legal_moves if m not in existing_moves]

            if untried_moves:
                # Pick one untried move at random
                move = random.choice(untried_moves)
                # Apply it to the simulation state
                state.make_move(move)
                # Create the new child node
                child_node = MCTSNode(state.clone(), parent=node, move=move)
                # Attach this new child to the tree
                node.children.append(child_node)
                # And select this new child as the node to simulate from
                node = child_node

        # 3. SIMULATION (ROLLOUT)
        winner = rollout(state)

        # 4. BACKPROPAGATION
        while node is not None:
            node.visits += 1
            if node.parent is not None:
                mover = node.parent.state.current_player
                
                if winner == mover:
                    node.wins += 1.0
                elif winner is None:
                    node.wins += 0.5 # Draw
                else:
                    node.wins += 0.0 # Loss for the mover
            
            node = node.parent

    # Collect Statistics
    stats = {}
    if root_node.visits > 0:
        for child in root_node.children:
            if child.visits > 0:
                win_rate = child.wins / child.visits
                # Calculate UCB for display purposes (c=1.4)
                ucb = win_rate + 1.4 * math.sqrt(2 * math.log(root_node.visits) / child.visits)
                stats[child.move] = {
                    "visits": child.visits,
                    "win_rate": win_rate,
                    "ucb": ucb
                }
    
    # Retrieve best move
    best_child = root_node.most_visited_child()
    best_move = best_child.move if best_child else None
    return best_move, stats

# ============================================================
#             PART 5 - DRAWING AND UI
# ============================================================
def draw_legend(screen, x, y, width):
    """
    Draws the legend panel explaining board colors and visual indicators.

    Arguments:
        screen: Pygame surface to draw on.
        x (int): Left position of the legend panel.
        y (int): Top position of the legend panel.
        width (int): Width of the legend panel.
    """
    # Background
    height = 80
    rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, (230, 230, 235), rect)
    small_font = pygame.font.SysFont("verdana", 11)

    items = [
        (BAR_BEST, "AI Best Move", False, True), # Color, Text, IsRing, IsOutline
        (WIN_LINE_COLOR, "Winning Pattern", True, False),
        (HIGHLIGHT_COLOR, "Last Played Move", True, False),
        (PLAYER1_COLOR, "Player 1 (Red)", False, False),
        (PLAYER2_COLOR, "Player 2 (Yellow)", False, False),
    ]

    # Draw in 2 rows
    start_x = x + 10
    start_y = y + 5
    col_width = width // 2
    
    for i, (color, text, is_ring, is_outline) in enumerate(items):
        row = i // 2
        col = i % 2
        
        ix = start_x + (col * col_width)
        iy = start_y + (row * 22)
        
        # Icon
        icon_rect = pygame.Rect(ix, iy, 12, 12)
        if is_outline:
            pygame.draw.rect(screen, color, icon_rect, 2, border_radius=3)
        elif is_ring:
            pygame.draw.circle(screen, color, (ix + 6, iy + 6), 5, 2)
        else:
            pygame.draw.rect(screen, color, icon_rect, border_radius=3)
            
        # Text
        screen.blit(small_font.render(text, True, (80, 80, 80)), (ix + 18, iy - 1))

def draw_controls_panel(screen, x, y, width):
    """
    Draws the controls panel listing valid user inputs.

    Arguments:
        screen: Pygame surface to draw on.
        x (int): Left position of the controls panel.
        y (int): Top position of the controls panel.
        width (int): Width of the controls panel.
    """
    height = 100
    rect = pygame.Rect(x, y, width, height)
    
    # Background Box
    pygame.draw.rect(screen, (240, 240, 245), rect, border_radius=8)
    pygame.draw.rect(screen, (210, 210, 210), rect, 1, border_radius=8)
    pygame.draw.line(screen, SEPARATOR_COLOR, (0, y), (PANEL_WIDTH, y), 2)

    # Header
    header_font = pygame.font.SysFont("verdana", 12, bold=True)
    key_font = pygame.font.SysFont("consolas", 11, bold=True)
    desc_font = pygame.font.SysFont("verdana", 11)

    screen.blit(header_font.render("Controls", True, (50, 50, 60)), (x + 10, y + 8))
    pygame.draw.line(screen, (200, 200, 200), (x + 10, y + 25), (x + width - 10, y + 25), 1)

    current_y = y + 32
    
    def draw_row(key, desc):
        nonlocal current_y
        # Key Box
        k_surf = key_font.render(key, True, (50, 50, 50))
        k_rect = pygame.Rect(x + 10, current_y, k_surf.get_width() + 8, 16)
        pygame.draw.rect(screen, (255, 255, 255), k_rect, border_radius=4)
        pygame.draw.rect(screen, (180, 180, 180), k_rect, 1, border_radius=4)
        screen.blit(k_surf, (x + 14, current_y + 1))
        
        # Desc
        screen.blit(desc_font.render(desc, True, (80, 80, 80)), (k_rect.right + 8, current_y + 1))
        current_y += 20

    draw_row("CLICK", "Drop Piece")
    draw_row("<- / ->", "Review History")
    draw_row("R/ESC", "Return to Menu")
                 
def draw_panel(screen, stats, best_move, waiting_for_input, state, mode, winning_info=None, history_step=None, history_idx=0, total_history=0):
    """
    Draws the left-side information panel.

    Displays:
    - Human or AI turn status
    - MCTS statistics and rankings
    - Win analysis and history review (if enabled)
    - Controls and legend panels

    Arguments:
        screen: Pygame surface to draw on.
        stats (dict): MCTS statistics per column.
        best_move (int): Selected move based on MCTS.
        waiting_for_input (bool): Whether AI is awaiting confirmation.
        state: Current Connect-4 game state.
        mode (int): Game mode identifier.
        winning_info (tuple, optional): Winner analysis data.
        history_step (dict, optional): Move history snapshot.
        history_idx (int): Current history index.
        total_history (int): Total number of recorded moves.
    """
    # Panel background
    panel_rect = pygame.Rect(0, 0, PANEL_WIDTH, HEIGHT)
    pygame.draw.rect(screen, PANEL_BG, panel_rect)
    # Separator line
    pygame.draw.line(screen, SEPARATOR_COLOR, (PANEL_WIDTH, 0), (PANEL_WIDTH, HEIGHT), 2)
    
    # Fonts
    title_font = pygame.font.SysFont("verdana", 28, bold=True)
    header_font = pygame.font.SysFont("verdana", 18, bold=True)
    val_font = pygame.font.SysFont("verdana", 22, bold=True) 
    small_font = pygame.font.SysFont("verdana", 14)
    tiny_font = pygame.font.SysFont("verdana", 12)

    # Define Areas
    CONTROLS_Y = HEIGHT - 200
    LEGEND_Y = HEIGHT - 90

    # History review analysis panel
    if winning_info:
        if history_step == None:
            return
        # Title
        screen.blit(title_font.render("History Review", True, (50, 50, 60)), (20, 20))
        current_y = 70
        # --- WINNER ANALYSIS PANEL (Only if Game Over) ---
        if winning_info:
            winner, coords, pattern_type, win_ucb_score = winning_info
            
            # Colors
            win_color = PLAYER1_COLOR if winner == PLAYER1 else PLAYER2_COLOR
            bg_tint = (255, 235, 235) if winner == PLAYER1 else (255, 255, 230)
            
            # Box
            bnr_height = 110
            bnr_rect = pygame.Rect(15, current_y, PANEL_WIDTH - 30, bnr_height)
            pygame.draw.rect(screen, bg_tint, bnr_rect, border_radius=8)
            pygame.draw.rect(screen, win_color, bnr_rect, 2, border_radius=8)
            
            # Trophy Icon
            pygame.draw.circle(screen, win_color, (50, current_y + 55), 22)
            pygame.draw.circle(screen, (255,255,255), (50, current_y + 55), 18, 2)

            # Text Info
            w_name = "PLAYER 1" if winner == PLAYER1 else "PLAYER 2"
            screen.blit(header_font.render(w_name + " WINS!", True, (0,0,0)), (85, current_y + 20))
            
            # Stats line
            screen.blit(tiny_font.render(f"Pattern: {pattern_type}", True, (80,80,80)), (85, current_y + 45))
            
            ucb_col = (0, 150, 0) if win_ucb_score > 0 else (200, 50, 50)
            screen.blit(tiny_font.render("Line Strength (UCB):", True, (80,80,80)), (85, current_y + 65))
            screen.blit(header_font.render(f"{win_ucb_score:.2f}", True, ucb_col), (220, current_y + 63))
            
            current_y += bnr_height + 15

        # Navigation Control Box
        nav_rect = pygame.Rect(20, current_y, PANEL_WIDTH - 40, 40)
        pygame.draw.rect(screen, (225, 225, 230), nav_rect, border_radius=20)
        pygame.draw.rect(screen, (200, 200, 200), nav_rect, 1, border_radius=20)
        
        nav_text = f"<  Move {history_idx + 1} of {total_history}  >"
        nav_surf = header_font.render(nav_text, True, (50, 50, 50))
        screen.blit(nav_surf, (nav_rect.centerx - nav_surf.get_width()//2, nav_rect.centery - nav_surf.get_height()//2))
        current_y += 55
        
        move_col = history_step['move']
        h_stats = history_step['stats']

        # Player label
        p_color = PLAYER1_COLOR if history_step['player'] == PLAYER1 else PLAYER2_COLOR
        p_name = "Red's Move" if history_step['player'] == PLAYER1 else "Yellow's Move"

        # Mini header
        pygame.draw.circle(screen, p_color, (30, current_y + 10), 6)
        screen.blit(header_font.render(f"{p_name} (Column {move_col})", True, (0,0,0)), (45, current_y))
        current_y += 30

        if h_stats and move_col in h_stats:
            data = h_stats[move_col]
            
            # 3 statistic boxes
            box_w = (PANEL_WIDTH - 60) // 3
            bx_h = 60

            # Win Rate
            bx1 = pygame.Rect(20, current_y, box_w, bx_h)
            pygame.draw.rect(screen, (235, 250, 235), bx1, border_radius=6)
            screen.blit(tiny_font.render("Win Rate", True, (100,100,100)), (bx1.x+5, bx1.y+5))
            screen.blit(val_font.render(f"{data['win_rate']*100:.0f}%", True, (0,100,0)), (bx1.x+5, bx1.y+25))

            # UCB
            bx2 = pygame.Rect(20 + box_w + 10, current_y, box_w, bx_h)
            pygame.draw.rect(screen, (235, 235, 250), bx2, border_radius=6)
            screen.blit(tiny_font.render("UCB Score", True, (100,100,100)), (bx2.x+5, bx2.y+5))
            screen.blit(val_font.render(f"{data['ucb']:.2f}", True, (0,0,150)), (bx2.x+5, bx2.y+25))

            # Visits
            bx3 = pygame.Rect(20 + 2*(box_w + 10), current_y, box_w, bx_h)
            pygame.draw.rect(screen, (250, 240, 230), bx3, border_radius=6)
            screen.blit(tiny_font.render("Visits", True, (100,100,100)), (bx3.x+5, bx3.y+5))
            screen.blit(val_font.render(f"{data['visits']}", True, (150,50,0)), (bx3.x+5, bx3.y+25))
            
            current_y += 75

            # Rankings List
            screen.blit(small_font.render("Alternative Choices:", True, (50,50,50)), (20, current_y))
            current_y += 25
            
            # Draw Table Headers
            col_x = [30, 120, 200, 280] 
            headers = ["Move", "Win Rate %", "UCB", "Trials"]
            
            for i, h_text in enumerate(headers):
                screen.blit(tiny_font.render(h_text, True, (120,120,120)), (col_x[i], current_y))
            
            current_y += 18 # Space after header
            
            # Sort by visits (most explored first)
            sorted_moves = sorted(h_stats.items(), key=lambda x: x[1]['visits'], reverse=True)
            
            # Show top 6 moves
            for i, (m_col, m_data) in enumerate(sorted_moves[:6]):
                is_sel = (m_col == move_col)
                
                # Row Dimensions
                row_h = 24
                row_rect = pygame.Rect(20, current_y, PANEL_WIDTH - 40, row_h)
                
                # Background Color
                bg_color = (255, 240, 200) if is_sel else (250, 250, 250)
                pygame.draw.rect(screen, bg_color, row_rect, border_radius=4)
                
                if is_sel: 
                    pygame.draw.rect(screen, (220, 180, 0), row_rect, 1, border_radius=4)
                
                # Text Color
                txt_col = (0,0,0) if is_sel else (60,60,60)
                
                # Column 1: Rank & Move
                rank_str = f"#{i+1} Column {m_col}"
                screen.blit(tiny_font.render(rank_str, True, txt_col), (col_x[0], current_y + 5))
                
                # Column 2: Win Rate
                win_str = f"{m_data['win_rate']*100:.1f}%"
                # Color code the win rate (Green good, Red bad)
                wr_color = (0, 100, 0) if m_data['win_rate'] > 0.5 else (150, 50, 50)
                screen.blit(tiny_font.render(win_str, True, wr_color), (col_x[1], current_y + 5))
                
                # Column 3: UCB 
                ucb_str = f"{m_data['ucb']:.2f}"
                screen.blit(tiny_font.render(ucb_str, True, txt_col), (col_x[2], current_y + 5))
                
                # Column 4: Trials/Visits 
                vis_str = f"{m_data['visits']}"
                screen.blit(tiny_font.render(vis_str, True, (100,100,100)), (col_x[3], current_y + 5))

                current_y += row_h + 4 # Spacing between rows
        else:
            # Human move
            pygame.draw.rect(screen, (245,245,245), (20, current_y, PANEL_WIDTH-40, 40), border_radius=5)
            screen.blit(small_font.render("Human move (No analysis statistic perform)", True, (150,150,150)), (30, current_y+10))

        # Draw Footer elements
        draw_controls_panel(screen, 15, CONTROLS_Y, PANEL_WIDTH - 30)
        draw_legend(screen, 15, LEGEND_Y, PANEL_WIDTH - 30)
        return 
    
    # Normal gameplay panel
    is_human_turn = False
    if mode == 1: 
        is_human_turn = True
    elif mode == 2 and state.current_player == PLAYER1:
        is_human_turn = True

    # Header panel for human player
    if is_human_turn:
        screen.blit(title_font.render("Your Turn", True, PLAYER1_COLOR if state.current_player == PLAYER1 else PLAYER2_COLOR), (20, 20))
        screen.blit(header_font.render("Awaiting Human Input...", True, (100, 100, 100)), (20, 60))
        
        # Human Instructions
        pygame.draw.rect(screen, (255, 255, 255), (20, 100, PANEL_WIDTH - 40, 100), border_radius=10)
        screen.blit(small_font.render("Instructions:", True, (0,0,0)), (35, 110))
        screen.blit(small_font.render("- Click a column to drop.", True, (50,50,50)), (35, 135))
        screen.blit(small_font.render("- Connect 4 to win.", True, (50,50,50)), (35, 155))
        
        # Draw Legend at bottom
        draw_controls_panel(screen, 15, CONTROLS_Y, PANEL_WIDTH - 30)
        draw_legend(screen, 15, LEGEND_Y, PANEL_WIDTH - 30)
        return # Do not show AI stats for human
    
    # Header panel for AI player
    screen.blit(title_font.render("MCTS AI Analysis", True, PLAYER1_COLOR), (20, 20))

    # Status Indicator
    status_msg = "Thinking..."
    status_color = (150, 150, 150)
    
    if waiting_for_input:
        status_msg = "Wanting for Confirmation"
        status_color = PLAYER1_COLOR
        
        # Blink effect instruction
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            instr = header_font.render("Press [SPACE] to continue", True, (0, 0, 0))
            screen.blit(instr, (20, 80))
    else:
        # If not waiting, normal status
        screen.blit(small_font.render("Analyzing...", True, (100, 100, 100)), (20, 80))

    screen.blit(header_font.render(status_msg, True, status_color), (20, 55))
    iter_text = tiny_font.render(f"Configuration: {MCTS_ITERATIONS} Iterations per move", True, (80, 80, 80))
    screen.blit(iter_text, (20, 110))

    # If no stats, stop here
    if not stats: 
        draw_controls_panel(screen, 15, CONTROLS_Y, PANEL_WIDTH - 30)
        draw_legend(screen, 15, LEGEND_Y, PANEL_WIDTH - 30)
        return

    # --- Selected Move Info Box ---
    if best_move is not None and best_move in stats:
        best_data = stats[best_move]
        # Box background
        box_rect = pygame.Rect(15, 140, PANEL_WIDTH - 30, 70)
        pygame.draw.rect(screen, (255, 255, 255), box_rect, border_radius=8)
        pygame.draw.rect(screen, PLAYER2_COLOR, box_rect, 2, border_radius=8) # Yellow border
        
        txt1 = header_font.render(f"Chosen Column: {best_move}", True, (0, 0, 0))
        txt2 = small_font.render(f"Win Confidence: {best_data['win_rate']*100:.1f}%", True, (50, 50, 50))
        txt3 = tiny_font.render(f"Simulations: {best_data['visits']} | UCB: {best_data['ucb']:.2f}", True, (100, 100, 100))
        
        screen.blit(txt1, (25, 148))
        screen.blit(txt2, (25, 170))
        screen.blit(txt3, (25, 190))

    # Stacked bar chart visualization
    chart_y = 250
    chart_h = 150
    bar_w = 30
    gap = 10
    start_x = 30
    
    screen.blit(header_font.render("Win Rate Distribution (P1 vs P2)", True, (0, 0, 0)), (20, 220))
    is_p1_turn = (state.current_player == PLAYER1)
    for i in range(COLS):
        # Draw baseline
        bx = start_x + i * (bar_w + gap)
        
        # Column label (0, 6)
        lbl = tiny_font.render(str(i), True, (50, 50, 50))
        screen.blit(lbl, (bx + 8, chart_y + chart_h + 5))
        
        # Background Bar
        bg_bar = pygame.Rect(bx, chart_y, bar_w, chart_h)
        pygame.draw.rect(screen, BAR_BG, bg_bar, border_radius=3)
        
        if i in stats:
            wr = stats[i]['win_rate']

            # Normalize to P1 (Red) vs P2 (Yellow)
            if is_p1_turn:
                p1_rate = wr
                p2_rate = 1.0 - wr
            else:
                p2_rate = wr
                p1_rate = 1.0 - wr

            # Clamp to 0.0 - 1.0 to prevent glitches
            p1_rate = max(0.0, min(1.0, p1_rate))
            p2_rate = max(0.0, min(1.0, p2_rate))

            # Calculate pixel heights
            p1_h = int(chart_h * p1_rate)
            p2_h = int(chart_h * p2_rate)

            # Player 2 (Yellow) - Bottom
            if p2_h > 0:
                p2_rect = pygame.Rect(bx, chart_y + (chart_h - p2_h), bar_w, p2_h)
                # If P1 exists on top, flat top corners. Else rounded.
                top_rad = 0 if p1_h > 0 else 3
                pygame.draw.rect(screen, PLAYER2_COLOR, p2_rect,
                                 border_bottom_left_radius=3, border_bottom_right_radius=3,
                                 border_top_left_radius=top_rad, border_top_right_radius=top_rad)

                # Text for P2
                if p2_h > 20:
                    txt = tiny_font.render(f"{int(p2_rate * 100)}", True, (50, 50, 50))
                    # Center text: x + (width/2) - (text_width/2)
                    tx = bx + (bar_w - txt.get_width()) // 2
                    ty = chart_y + chart_h - (p2_h // 2) - 6
                    screen.blit(txt, (tx, ty))

            # Player 1 (Red) - Top
            if p1_h > 0:
                # Starts above P2
                p1_rect = pygame.Rect(bx, chart_y + (chart_h - p2_h - p1_h), bar_w, p1_h)
                bot_rad = 0 if p2_h > 0 else 3
                pygame.draw.rect(screen, PLAYER1_COLOR, p1_rect,
                                 border_top_left_radius=3, border_top_right_radius=3,
                                 border_bottom_left_radius=bot_rad, border_bottom_right_radius=bot_rad)

                # Text for P1
                if p1_h > 20:
                    txt = tiny_font.render(f"{int(p1_rate * 100)}", True, (255, 255, 255))
                    tx = bx + (bar_w - txt.get_width()) // 2
                    ty = chart_y + (chart_h - p2_h - p1_h) + (p1_h // 2) - 6
                    screen.blit(txt, (tx, ty))

            # Best move indicator
            if i == best_move:
                total_h = p1_h + p2_h
                hl_rect = pygame.Rect(bx - 3, chart_y, bar_w + 6, chart_h)
                pygame.draw.rect(screen, WIN_LINE_COLOR, hl_rect, 3, border_radius=8)
                
    # Rank Moves List
    list_y = 440
    screen.blit(header_font.render("Move Rankings:", True, (0, 0, 0)), (20, 415))
    
    sorted_moves = sorted(stats.items(), key=lambda x: x[1]['visits'], reverse=True)
    
    for i, (move, data) in enumerate(sorted_moves):
        color = (50, 50, 50)
        prefix = f"{i+1}. "
        if move == best_move: 
            color = (200, 150, 0) # Gold text for best
            
        text = f"{prefix}Column {move}: {data['win_rate']*100:.1f}% | UCB: {data['ucb']:.2f} | {data['visits']} visits"
        screen.blit(small_font.render(text, True, color), (25, list_y))
        list_y += 20
    
    draw_controls_panel(screen, 15, CONTROLS_Y, PANEL_WIDTH - 30)
    draw_legend(screen, 15, LEGEND_Y, PANEL_WIDTH - 30)

def draw_board(screen, state, font, mode, message="", stats=None, best_move=None, waiting=False, winning_info=None, history_step=None, history_idx=0, total_history=0):
    """
    Renders the full game screen.

    Includes:
    - Side information panel
    - Game board and pieces
    - Turn / status messages
    - AI hint indicators and winning highlights

    Arguments:
        screen: Pygame surface to draw on.
        state: Current Connect-4 game state.
        font: Font used for rendering text.
        mode (int): Selected game mode.
        message (str): Status message at the top.
        stats (dict, optional): MCTS statistics.
        best_move (int, optional): AI-selected column.
        waiting (bool): Whether AI is waiting for confirmation.
        winning_info (tuple, optional): Winning pattern information.
        history_step (dict, optional): History review data.
        history_idx (int): Current history position.
        total_history (int): Total history length.
    """
    # Fill the screen with background color
    screen.fill(BG_COLOR)

    # Draw side panel
    draw_panel(screen, stats, best_move, waiting, state, mode, winning_info, history_step, history_idx, total_history)

    # Draw message area at the top
    text_surface = font.render(message, True, TEXT_COLOR)
    screen.blit(text_surface, (PANEL_WIDTH + 20, 10))

    # --- Draw Mode Indicator (Top Right) ---
    mode_text = ""
    if mode == 1: mode_text = "Mode: Human vs Human"
    elif mode == 2: mode_text = "Mode: Human vs AI"
    elif mode == 3: mode_text = "Mode: AI vs AI"

    # Draw it in a subtle color
    mode_surface = font.render(mode_text, True, (150, 150, 150)) 
    screen.blit(mode_surface, (WIDTH - mode_surface.get_width() - 20, 50))
    
    # Draw Board Background
    board_rect = pygame.Rect(PANEL_WIDTH, 2 * SQUARESIZE, WIDTH, ROWS * SQUARESIZE)
    pygame.draw.rect(screen, BOARD_COLOR, board_rect)

    # Draw blue board and empty holes
    for c in range(COLS):
        for r in range(ROWS):
            x_pos = PANEL_WIDTH + c * SQUARESIZE + SQUARESIZE // 2
            y_pos = (r + 2) * SQUARESIZE + SQUARESIZE // 2
            
            piece = state.board[r][c]
            color = SLOT_BG # Empty slot color

            if piece == PLAYER1: color = PLAYER1_COLOR
            elif piece == PLAYER2: color = PLAYER2_COLOR
            
            pygame.draw.circle(screen, color, (x_pos, y_pos), RADIUS)
            
            # Highlight Last Move
            if state.last_move == (r, c):
                pygame.draw.circle(screen, HIGHLIGHT_COLOR, (x_pos, y_pos), RADIUS, 3)
    
    # Highlight winning line
    if winning_info:
        winner_id, coords, _, _ = winning_info
        for r, c in coords:
            if state.board[r][c] == winner_id:
                x_pos = PANEL_WIDTH + c * SQUARESIZE + SQUARESIZE // 2
                y_pos = (r + 2) * SQUARESIZE + SQUARESIZE // 2
                pygame.draw.circle(screen, WIN_LINE_COLOR, (x_pos, y_pos), RADIUS + 4, 4)

    # Draw "Ghost" coin pointing to chosen column for AI player
    if waiting and best_move is not None:
        ghost_x = PANEL_WIDTH + best_move * SQUARESIZE + SQUARESIZE // 2
        ghost_y = SQUARESIZE + SQUARESIZE // 2

        ghost_color = PLAYER1_COLOR if state.current_player == PLAYER1 else PLAYER2_COLOR

        # Draw a translucent or outlined piece indicating where AI wants to go
        pygame.draw.circle(screen, ghost_color, (ghost_x, ghost_y), RADIUS, 4)
        
        # Draw Arrow
        arrow_points = [(ghost_x, ghost_y + 10), (ghost_x - 10, ghost_y - 10), (ghost_x + 10, ghost_y - 10)]
        pygame.draw.polygon(screen, ghost_color, arrow_points)

    # Update the display
    pygame.display.update()

def draw_menu(screen, font):
    """
    Draws the main menu screen.

    Displays available game modes and quit option.

    Arguments:
        screen: Pygame surface to draw on.
        font: Font used for rendering menu text.
    """
    screen.fill(BG_COLOR)

    title = font.render("CarloConnect - AI EDITION", True, PLAYER1_COLOR)
    option1 = font.render("1. Human vs Human", True, TEXT_COLOR)
    option2 = font.render("2. Human vs AI Agent", True, TEXT_COLOR)
    option3 = font.render("3. AI Agent vs AI Agent", True, TEXT_COLOR)
    option_quit = font.render("Q. Quit", True, TEXT_COLOR)

    # Centering text
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 120))
    screen.blit(option1, (WIDTH//2 - option1.get_width()//2, 220))
    screen.blit(option2, (WIDTH//2 - option2.get_width()//2, 280))
    screen.blit(option3, (WIDTH//2 - option3.get_width()//2, 340))
    screen.blit(option_quit, (WIDTH//2 - option_quit.get_width()//2, 420))
    
    pygame.display.update()

# ============================================================
#              PART 6 - GAME LOOP LOGIC WITH PYGAME
# ============================================================
def run_game(screen, mode):
    """
    Runs the main Connect-4 game loop for the selected game mode.

    Manages:
    - Human and AI turns
    - MCTS-based decision making
    - Game state updates and history tracking
    - Win detection and post-game analysis
    - Rendering and user input handling

    Arguments:
        screen: Pygame surface used for rendering.
        mode (int):
            Game mode selector:
                1 - Human vs Human
                2 - Human vs AI
                3 - AI vs AI

    Returns:
        None. Exits when the game ends or the user returns to the menu.
    """
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("verdana", 22, bold=True)
    state = Connect4State()
    game_over = False

    # History tracking
    history = [] # { 'state': Connect4State, 'stats': dict, 'move': int, 'player': int }
    view_index = -1
    
    # Pause mechanic
    waiting_for_input = False 
    pending_ai_move = None
    last_stats = {}      # To store stats from the last AI move
    winning_info = None
    
    while True:
        clock.tick(FPS)
        
        # Check Win Status and compute Stats
        if game_over and winning_info is None:
            # Get the raw line info from the state
            raw_win_info = state.get_winning_line() 
            
            if raw_win_info:
                winner, coords, pattern = raw_win_info
                involved_cols = set(c for r, c in coords)
                total_ucb = 0.0
                count = 0
                for col in involved_cols:
                    if col in last_stats:
                        total_ucb += last_stats[col]['ucb']
                        count += 1
                
                final_score = total_ucb / count if count > 0 else 0.0 
                # Store full info tuple for UI
                winning_info = (winner, coords, pattern, final_score)
            # Default to viewing the last move
            if history:
                view_index = len(history) - 1
            else:
                view_index = 0

        # Determine Status Message
        if game_over:
            winner = state.check_winner()
            if winner == PLAYER1:
                msg = f"Player 1 ({'Human' if mode in (1, 2) else 'AI'}) Wins!"
            elif winner == PLAYER2:
                msg = f"Player 2 ({'AI' if mode in (2, 3) else 'AI'}) Wins!"
            else: 
                msg = "Draw!"
        else:
            p_name = "Red" if state.current_player == PLAYER1 else "Yellow"
            
            # Determine player type label based on mode
            if mode == 3:
                p_type = "AI"
            elif mode == 1:
                p_type = "Human"
            else: # mode 2
                p_type = "Human" if state.current_player == PLAYER1 else "AI"
            
            msg = f"{p_name} ({p_type}) Turn"
        
        # Input Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: # Restart
                    return 
                if event.key == pygame.K_ESCAPE:
                    return # Back to menu
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()
                # History navigation
                if game_over and history:
                    if event.key == pygame.K_LEFT:
                        view_index = max(0, view_index - 1)
                    if event.key == pygame.K_RIGHT:
                        view_index = min(len(history) - 1, view_index + 1)
                # SPACE to continue
                if event.key == pygame.K_SPACE and waiting_for_input:
                    # AI move execute
                    curr_player = state.current_player
                    state.make_move(pending_ai_move)

                    # Record History (AI player)
                    history.append({
                        'state': state.clone(),
                        'stats': last_stats, 
                        'move': pending_ai_move,
                        'player': curr_player
                    })

                    if state.is_terminal(): 
                        game_over = True
                    waiting_for_input = False
                    pending_ai_move = None

            # Handle mouse if it is a Human Turn
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over and not waiting_for_input:
                # Mode 1: Human is P1 and P2
                # Mode 2: Human is P1
                is_human = False
                if mode == 1: 
                    is_human = True # Both players are human
                elif mode == 2 and state.current_player == PLAYER1: 
                    is_human = True # Only player 1 is human

                if is_human:
                    x, _ = event.pos
                    if x > PANEL_WIDTH:
                        col = (x - PANEL_WIDTH) // SQUARESIZE
                        if col in state.get_legal_moves():
                            curr_player = state.current_player
                            state.make_move(col)

                            # Record history (Human player)
                            history.append({
                                'state': state.clone(),
                                'stats': None,
                                'move': col,
                                'player': curr_player
                            })
                        
                            last_stats = {} # No UCB perform
                            if state.is_terminal(): 
                                game_over = True

        # AI LOGIC
        if not game_over and not waiting_for_input:
            # Mode 2: It is P2's turn
            # Mode 3: It is ANY turn
            is_ai = False
            
            if mode == 2 and state.current_player == PLAYER2:
                is_ai = True
            elif mode == 3:
                is_ai = True # Both are AI
            
            if is_ai:
                draw_board(screen, state, font, mode, msg + " - Thinking...", last_stats, None, False, None)
                pygame.display.update()
                # Calculate
                best_move, stats = mcts_search(state, n_iter=MCTS_ITERATIONS)
                if best_move is not None:
                    # Store results and Enter wait state
                    pending_ai_move = best_move
                    last_stats = stats
                    waiting_for_input = True
                else:
                    pass
  
        # Render
        if game_over and history:
            # Review History Move MCTS
            step = history[view_index]
            # Pass the history step to draw_board
            draw_board(screen, step['state'], font, mode, msg, 
                       stats=None, best_move=None, waiting=False, 
                       winning_info=winning_info, 
                       history_step=step, 
                       history_idx=view_index, 
                       total_history=len(history))
        else:
            # MCTS Live Analyse
            display_move = pending_ai_move if waiting_for_input else None
            draw_board(screen, state, font, mode, msg, last_stats, display_move, waiting_for_input, winning_info)

# game menu
def main_menu():
    """
    Initializes the Pygame environment and executes the main menu loop.

    Displays the title screen and handles keyboard input to trigger game modes:
    1. Human vs Human
    2. Human vs AI
    3. AI vs AI
    Or 'Q' to quit.
    """
    pygame.init()
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("MCTS - CarloConnect")
    font = pygame.font.SysFont("verdana", 30, bold=True)
    
    while True:
        draw_menu(screen, font)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    run_game(screen, 1) # Human vs Human
                if event.key == pygame.K_2:
                    run_game(screen, 2) # Human vs AI
                if event.key == pygame.K_3:
                    run_game(screen, 3) # AI vs AI
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                    
# main
if __name__ == "__main__":
    # Call the main function to execute the program
    main_menu()

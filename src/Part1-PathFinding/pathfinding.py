import math
import heapq
from settings import COLS, ROWS

# Calculate the Octile distance between two locations
def octile_distance(current_node, goal):
    """
    Octile distance heuristic for 8-direction movement where:
      - orthogonal cost = 1
      - diagonal cost = sqrt(2)

    Args:
        current_node (Node): The current node.
        goal (Node): The target node.

    Returns:
        int: Octile distance between current node and goal node.
    """
    dx = abs(current_node.x - goal.x)
    dy = abs(current_node.y - goal.y)
    D = 1.0
    D2 = math.sqrt(2)
    return D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)

#  Retrieves all valid, walkable neighboring nodes for a given node in the grid
def get_neighbors(grid, node):
    """
    Args:
        grid (list[list[Node]]): The 2D array representing the map.
        node (Node): The current node instance to expand from.

    Returns:
        list[Node]: A list of valid Node objects that can be traversed next.
    """
    neighbors = []
    directions = [
        (0, -1), (0, 1), (-1, 0), (1, 0),   
        (-1, -1), (-1, 1), (1, -1), (1, 1)  
    ]
    for dx, dy in directions:
        new_x, new_y = node.x + dx, node.y + dy
        if 0 <= new_x < COLS and 0 <= new_y < ROWS:
            neighbor = grid[new_y][new_x]
            if not neighbor.is_wall:
                # prevent clipping through tight corners
                # if abs(dx) == 1 and abs(dy) == 1:
                #     if grid[node.y][new_x].is_wall and grid[new_y][node.x].is_wall:
                #         continue
                neighbors.append(neighbor)
    return neighbors

# Executes the A* pathfinding algorithm to find the shortest path between two nodes
def find_path(grid, start_node, end_node):
    """
    Args:
        grid (list[list[Node]]): The 2D grid of Node objects representing the map.
        start_node (Node): The node to start the search from.
        end_node (Node): The target destination node.

    Returns:
        tuple: A tuple containing three lists:
            - path (list[Node]): The reconstructed path from start to end. Returns empty if no path found.
            - explored (list[Node]): All nodes that were visited (closed set) during the search.
            - frontier (list[Node]): All nodes currently in the open set (discovered but not yet fully processed).
    """
    # Reset costs
    for row in grid:
        for node in row:
            node.g_cost = float('inf')
            node.f_cost = float('inf')
            node.parent = None
    
    # trivial case
    if start_node == end_node:
        start_node.g_cost = 0
        start_node.h_cost = 0
        start_node.f_cost = 0
        yield [start_node], [start_node], []
        return

    start_node.g_cost = 0
    start_node.h_cost = octile_distance(start_node, end_node)
    start_node.f_cost = start_node.h_cost

    open_heap = []
    counter = 0  # tie-breaker
    # store tuples: (f_cost, g_cost, counter, node)
    heapq.heappush(open_heap, (start_node.f_cost, start_node.g_cost, counter, start_node))
    counter += 1

    closed_set = set()
    explored = []

    while open_heap:
        f, g, _, current = heapq.heappop(open_heap)

        # If we've already finalized this node
        if (current.x, current.y) in closed_set:
            continue

        # Mark as expanded
        closed_set.add((current.x, current.y))
        explored.append(current)

        # Extract current frontier for visualization
        frontier_unique = {}
        for item in open_heap:
            n = item[3]
            if (n.x, n.y) not in closed_set:
                # If node is already in dict, keep the one with lower F-cost
                if (n.x, n.y) not in frontier_unique or n.f_cost < frontier_unique[(n.x, n.y)].f_cost:
                    frontier_unique[(n.x, n.y)] = n
        
        current_frontier = list(frontier_unique.values())
        # Yield current state
        yield [], explored, current_frontier 

        # Optimal path found
        if current == end_node:
            # Reconstruct path
            path = []
            node = current
            while node:
                path.append(node)
                node = node.parent

            frontier_nodes = []
            for _, _, _, node in open_heap:
                if (node.x, node.y) not in closed_set:
                    frontier_nodes.append(node)

            yield path[::-1], explored, frontier_nodes
            return

        for neighbor in get_neighbors(grid, current):
            if (neighbor.x, neighbor.y) in closed_set:
                continue

            # Movement cost: diagonal = sqrt(2), orthogonal = 1
            is_diag = (current.x != neighbor.x) and (current.y != neighbor.y)
            move_cost = math.sqrt(2) if is_diag else 1.0

            tentative_g = current.g_cost + move_cost

            if tentative_g < neighbor.g_cost:
                neighbor.parent = current
                neighbor.g_cost = tentative_g
                neighbor.h_cost = octile_distance(neighbor, end_node)
                neighbor.f_cost = neighbor.g_cost + neighbor.h_cost

                # Push a new entry onto the heap
                heapq.heappush(open_heap, (neighbor.f_cost, neighbor.g_cost, counter, neighbor))
                counter += 1

    # Fail to reach campfire
    frontier_nodes = []
    for _, _, _, node in open_heap:
        if (node.x, node.y) not in closed_set:
            frontier_nodes.append(node)

    yield [], explored, frontier_nodes
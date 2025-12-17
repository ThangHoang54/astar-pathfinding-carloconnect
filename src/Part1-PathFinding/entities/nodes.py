class Node:
    # Constructor
    def __init__(self, x, y):
        """
        Args:
            x (int): The x-coordinate (column index) in the grid.
            y (int): The y-coordinate (row index) in the grid.
        """
        self.x = x 
        self.y = y
        self.g_cost = float('inf')
        self.h_cost = 0
        self.f_cost = float('inf')
        self.parent = None
        self.is_wall = False

    # Comparison operator for priority queues based on f-cost
    def __lt__(self, other):
        """
        Args:
            other (Node): The other node to compare against.

        Returns:
            bool: True if this node's f_cost is less than the other node's f_cost.
        """
        return self.f_cost < other.f_cost
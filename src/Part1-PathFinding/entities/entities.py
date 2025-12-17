import pygame
from settings import GRID_SIZE, SURVIVOR_COLOR

class Survivor:
    # Constructor
    def __init__(self, x, y):
        """
        Args:
            x (float): Initial x-coordinate in pixels.
            y (float): Initial y-coordinate in pixels.
        """
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        
        # Tuning variables for "Natural" feel
        self.max_speed = 2.8
        self.max_force = 0.2  
        self.waypoint_radius = 30 
        
        self.path = []
        self.current_waypoint_index = 0

    # Converts a list of grid nodes into world-space vector waypoints for the agent to follow
    def set_path(self, path_nodes):
        """
        Args:
            path_nodes (list[Node]): List of grid nodes representing the path.
        
        Returns:
            None
        """
        self.path = [pygame.math.Vector2(node.x * GRID_SIZE + GRID_SIZE/2, 
                                         node.y * GRID_SIZE + GRID_SIZE/2) 
                     for node in path_nodes]
        self.current_waypoint_index = 0

    # Applies a physics force vector to the agent's acceleration
    def apply_force(self, force):
        """
        Args:
            force (pygame.math.Vector2): The force vector to apply.
        
        Returns:
            None
        """
        self.acc += force

    # Calculates a steering force to move towards a target at maximum speed
    def seek(self, target):
        """
        Args:
            target (pygame.math.Vector2): The target position vector.
        
        Returns:
            pygame.math.Vector2: The calculated steering force vector.
        """
        desired = target - self.pos
        distance = desired.length()
        if distance > 0:
            desired = desired.normalize() * self.max_speed
        else:
            desired = pygame.math.Vector2(0, 0)

        steer = desired - self.vel
        if steer.length() > self.max_force:
            steer.scale_to_length(self.max_force)
        return steer

    # Calculates a steering force to move towards a target, slowing down as it approaches
    def arrive(self, target):
        """
        Args:
            target (pygame.math.Vector2): The target position vector.
        
        Returns:
            pygame.math.Vector2: The calculated steering force vector.
        """
        desired = target - self.pos
        distance = desired.length()
        slowing_radius = 50 

        if distance < slowing_radius:
            desired_speed = self.max_speed * (distance / slowing_radius)
            if distance > 0:
                desired = desired.normalize() * desired_speed
            else:
                desired = pygame.math.Vector2(0, 0)
        else:
            if distance > 0:
                desired = desired.normalize() * self.max_speed
            else:
                desired = pygame.math.Vector2(0, 0)

        steer = desired - self.vel
        if steer.length() > self.max_force:
            steer.scale_to_length(self.max_force)
        return steer
    
    # Updates the agent's position, velocity, and path progress based on steering behaviors
    def update(self):
        if self.path and self.current_waypoint_index < len(self.path):
            target = self.path[self.current_waypoint_index]
            dist = self.pos.distance_to(target)

            is_final_destination = (self.current_waypoint_index == len(self.path) - 1)

            steering_force = pygame.math.Vector2(0, 0)

            if is_final_destination:
                steering_force = self.arrive(target)
                if dist < 5: 
                    self.pos = target
                    self.path = []
                    self.vel = pygame.math.Vector2(0,0)
                    return
            else:
                steering_force = self.seek(target)
                if dist < self.waypoint_radius:
                    self.current_waypoint_index += 1

            self.apply_force(steering_force)

        self.vel += self.acc
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)
        self.pos += self.vel
        self.acc *= 0

    # Renders the survivor agent to the screen using an image or a fallback shape
    def draw(self, screen, survivor_image=None):
        """
        Args:
            screen (pygame.Surface): The surface to draw onto.
            survivor_image (pygame.Surface | None): The sprite to use. If None, draws a circle.
        
        Returns:
            None
        """
        if survivor_image:
            # Draw the sprite centered on the position
            img_rect = survivor_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(survivor_image, img_rect)
        else:
            # Draw the code-generated agent if image fails
            pygame.draw.circle(screen, SURVIVOR_COLOR, (int(self.pos.x), int(self.pos.y)), GRID_SIZE // 2)
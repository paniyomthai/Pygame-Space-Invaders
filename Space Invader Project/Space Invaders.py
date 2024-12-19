import pygame
import os
import time
import random

# Initialize ability to import fonts for on-screen display
pygame.font.init()

# Setting up display area by indicating number of pixels (x, y)
# Ex. QHD (2k resolution) screen = 2048 x 1080 pixels
WIDTH, HEIGHT = 1000, 900
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DIY Space Invaders")

# Loading image assets from "assets" folder
RED_SHIP = pygame.image.load(os.path.join("Space Invader Project", "assets", "ship_red.png"))
BLUE_SHIP = pygame.image.load(os.path.join("Space Invader Project", "assets", "ship_blue.png"))
GREEN_SHIP = pygame.image.load(os.path.join("Space Invader Project", "assets", "ship_green.png"))
PLAYER_SHIP = pygame.image.load(os.path.join("Space Invader Project", "assets", "ship_player.png"))
RED_LASER = pygame.image.load(os.path.join("Space Invader Project", "assets", "laser_red.png"))
PLAYER_LASER = pygame.image.load(os.path.join("Space Invader Project", "assets", "laser_player.png"))

# Scaling static background image to full-screen (image size = window size)
BG = pygame.transform.scale(pygame.image.load(os.path.join("Space Invader Project", "assets", "background_static.png")), (WIDTH, HEIGHT))

# Superclass for laser projectiles
class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    # Window attribute allows the object itself to be used as the drawing parameter
    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    # +vel moves laser down (increase), -vel moves laser up (decrease)
    def move(self, vel):
        self.y += vel  

    # Detecting offscreen laser projectile (so that particular instance can be removed) 
    def off_screen(self, height):  
        return not(height >= self.y >= 0)

    # Detecting laser collision with enemy ships
    def collision(self, obj):  
        return collide(self, obj)

# Superclass for spaceships (general; for inheritance)
class Ship:
    COOLDOWN = 50  # If set FPS = 100, 50 frames = 0.5 second of cooldown

    def __init__(self, x, y, health = 100): 
        self.x = x  
        self.y = y
        self.health = health
        # General class for inheritance, leave img file path blank (specify in subclass for player/enemy)
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        # Setting cooldown for laser
        self.cooldown_counter = 0  

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

# Moving enemy laser projectiles
    def move_lasers(self, vel, obj):  # obj attribute represents player; checks for collision with player
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            # Removing laser offscreen
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            # Reducing player health from collision with enemy projectile, then removing laser after first contact
            elif laser.collision(obj):
                obj.health -= 25  
                self.lasers.remove(laser)

    def cooldown(self):
        # Once counter reaches cooldown threshold, reset to 0 (can shoot again)
        if self.cooldown_counter >= self.COOLDOWN:  
            self.cooldown_counter = 0
        # If counter hasn't reached threshold, increment by 1 per every window refresh
        elif self.cooldown_counter > 0:  
            self.cooldown_counter += 1

    def shoot(self):
        if self.cooldown_counter == 0:  # Creating new laser object when cooldown = 0
            laser = Laser(self.x, self.y, self.laser_img)  # Creating laser at player location
            self.lasers.append(laser)  # When new laser projectile is shot, laser object is added to the lasers list
            self.cooldown_counter = 1  # Adjust to modify firing rate

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


# Creating subclass for player ship
# Player subclass inherits class attributes and methods from Ship class within parentheses
class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = PLAYER_SHIP
        self.laser_img = PLAYER_LASER
        # Creating mask around ship surface for a wrapped hit-box (and not just a square box around the ship)
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health  # Creating max health for point of % deduction from damage

    # Moving player lasers
    def move_lasers(self, vel, objs):  # objs represents enemies; checks for laser collision with enemies
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)  # enemy object removed after collision = 1-hit kill
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window) 
        self.health_bar(window)

    # Drawing player health bar
        # Using two overlapping rectangles to represent HP remaining (red & green)
        # Making health bar that hovers above player ship
            # Using program window (WIN) as surface will cause health bar to be static
            # Using window attribute as surface will tell the program to use the bar as its own parameters
    def health_bar(self, window):
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10))
        # Green bar (remaining HP) will be drawn as % of much HP we have
        # y-coordinate of player ship plus the height gives bottom end, and then space out by 10 pixels to draw bar

class Enemy(Ship):
    ASSET_COLOR = {"red": (RED_SHIP, RED_LASER),
                   "green": (GREEN_SHIP, RED_LASER),
                   "blue": (BLUE_SHIP, RED_LASER)}
    # Create dictionary for asset color mapping to bypass need for manual input

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.ASSET_COLOR[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

# Enemy AI will only move straight down
    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cooldown_counter == 0:  # Cooldown for EACH enemy, so all can still shoot at same time
            laser = Laser(self.x-17, self.y, self.laser_img)
            # Laser not centered with enemy model when shot, adjust pixels using self.x
            # Centered for player though, could be due to width pixel numbers?
            self.lasers.append(laser)
            self.cooldown_counter = 1.5

# Use masks to detect collision of pixels between two objects. Overlapping of pixels = collision
    # Since mask detection also occurs at top left corner, use offset of coordinates to detect pixel overlap
def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None
    # If pixels aren't overlapping, .overlap will return None
    # Otherwise, will return (x, y) tuple for point of intersection


# Main loop for handling events (collisions, calling things onto screen, quitting game, etc.)
def main():
    run = True
    fps = 100
    level = 0
    lives = 5
    default_font = pygame.font.SysFont("verdana", 36)
    lost_font = pygame.font.SysFont("verdana", 60, True)

    enemies = []
    spawn_count = 5  # Amount of enemy per round. Game initiates from lvl 0 to 1
    vel_enemy = 0.45  # Initial enemy speed

    player = Player(450, 780)  # Player spawn point
    # Player movement speed. As control input registers, ship will move n pixels according to assigned value
    # Ex. For 100 fps, game will refresh and check for executed input 100 times per second
    # Higher fps means player will move more often if key is held (refreshed more times than lower fps)
    vel_player = 5

    vel_laser_player = 6
    vel_laser_enemy = 3.5

    lost = False
    lost_count = 0

    clock = pygame.time.Clock()

    # Rendering/drawing the visuals (.blit()  places an image onto the application screen)
    # PyGame coordinates have a reversed y-axis, starts 0 and increases downwards
    def redraw_window():
        # Drawing background onto window
        WIN.blit(BG, (0, 0))
        # Drawing texts. 3 numbers are RGB hexadecimal values. All 250 is white.
        label_lives = default_font.render(f"Lives: {lives}", True, (250, 250, 250))
        label_level = default_font.render(f"Level: {level}", True, (250, 250, 250))

        WIN.blit(label_lives, (10, 10))
        WIN.blit(label_level, (WIDTH - label_level.get_width() - 10, 10))
        # x-coord will establish where the left side of the label starts
        # Call up label width (using method) and subtract it from window width
        # Difference will be the starting x-coord of the lvl label
        # But this will fit perfectly on right side, so subtract 10 pixels to move label to the left (to mirror)

        for ea_enemy in enemies:
            ea_enemy.draw(WIN)
        # enemies has .draw method as part of inheritance that Enemy receives from Ship

        player.draw(WIN)

        if lost:
            lost_label = lost_font.render("Game Over", True, (255, 10, 10))
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 450))  
            # Similar equation for centering text

        # Window will update and redraw itself at the rate of given FPS
        pygame.display.update()  

    while run:
        
        # Game clock speed (i.e. tick rate) set to designated FPS
        clock.tick(fps)
        
        # Refresh window according to FPS, higher FPS = more frequent refreshing = more responsive
        redraw_window()  

        # PROGRESS: loop runs indefinitely, so lives rapidly deplete after HP reaches 0 the first time
        if player.health <= 0:
            for i in range(5, -1, -1):
                if lives == i:
                    lives -= 1
                    player.draw(WIN)
          
                elif lives < 0:  
                    lost = True
                    lost_count += 1
        
        if lost:
            if lost_count > fps * 3:  # fps = 1 second, so game will quit after lost conditions activate for >3 sec
                run = False
            else:
                continue  # Ends current iteration of for/while loop and continues to next iteration
                # If lost counter isn't written, game infinitely loops redraw_window() and will crash
            
        if len(enemies) == 0:  # Progress lvl by 1 if total enemy count is 0. Initiates game from "lvl 0" to lvl 1
            level += 1
            spawn_count += 5
            for i in range(spawn_count):
                enemy = Enemy(random.randrange(100, WIDTH - 100),
                              random.randrange(-1000, -50),
                              # y-axis rng makes enemies spawn down at different distances
                              # Range might be too narrow for higher levels with greater amount of enemies
                              # Could increment the range by level, ex. (-1000 * level/8, -50)
                              random.choice(["red", "blue", "green"]))
                enemies.append(enemy)  # Enemies must be added into "enemies" list first to move

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()  # Allows for the infinite loop to stop when exiting (clicking X on game window)

# Keybinding
    # Can put controls in the above for loop, but loop detects one input at a time (can't move diagonally)
        keys = pygame.key.get_pressed()  # returns dict that tells which keys are being pressed
        # In the key dict, UP key = up arrow, LEFT = left arrow, etc.
        if keys[pygame.K_UP] and player.y - vel_player > 0:
            player.y -= vel_player
        # If y-axis (length) of ship hasn't cross window border coord while moving, ship can continue to move
        if keys[pygame.K_DOWN] and player.y + player.get_width() + vel_player + 10 < HEIGHT:  # +10 for health bar under
            player.y += vel_player
        if keys[pygame.K_LEFT] and player.x - vel_player > 0:
            player.x -= vel_player
        if keys[pygame.K_RIGHT] and player.x + player.get_height() + vel_player < WIDTH:
            player.x += vel_player
        """ Since asset model detection happens at its top left corner, the right and bottom frames will clip through the game window. 
        Set up 'and' condition that accounts for those edges by adding number of pixels of entire length/width to detect the opposite 
        edge of that axis (for moving to right and bottom borders of screen)"""
        if keys[pygame.K_s]:
            player.shoot()

        for enemy in enemies[:]:  
            enemy.move(vel_enemy)
            enemy.move_lasers(vel_laser_enemy, player)

            if random.randrange(0, 100*2) == 1:
                enemy.shoot()
            # Randomized chance of enemies shooting within 1 second
            # Since there are 100 fps, (0, 200) would mean 50% probability each enemy will shoot per sec
            # 50% of shooting per sec = 100% of shooting within 2 seconds, hence 100*2
            # Modify coefficient to adjust probability of enemy shooting

            if collide(enemy, player):
                player.health -= 50
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)  # Remove objects from "enemies" list after they pass the bottom frame of window

        player.move_lasers(-vel_laser_player, enemies)  # Player laser moving up, so velocity must be negative


def menu():
    menu_font1 = pygame.font.SysFont("verdana", 70)
    menu_font2 = pygame.font.SysFont("verdana", 45, False, True)
    menu_font3 = pygame.font.SysFont("verdana", 30)
    menu_font4 = pygame.font.SysFont("verdana", 30)
    title_text1 = menu_font1.render("Space Invaders (1.5)", True, (255, 255, 255))
    title_text2 = menu_font2.render("Press any button to begin", True, (0, 255, 255))
    title_text3 = menu_font3.render("Ship control = Arrows", True, (255, 255, 255))
    title_text4 = menu_font4.render("Shoot = S", True, (255, 255, 255))
    run = True
    while run:
        WIN.blit(BG, (0, 0))
        WIN.blit(title_text1, (WIDTH/2 - title_text1.get_width()/2, 50))
        WIN.blit(title_text2, (WIDTH/2 - title_text2.get_width()/2, 450))
        WIN.blit(title_text3, (WIDTH/2 - title_text3.get_width()/2, 300))
        WIN.blit(title_text4, (WIDTH/2 - title_text4.get_width()/2, 350))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                main()

menu()

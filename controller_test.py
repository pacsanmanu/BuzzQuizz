import pygame
import time

# Initialize pygame and the joystick module
pygame.init()
pygame.joystick.init()

# Get the number of connected controllers
num_controllers = pygame.joystick.get_count()

print("Number of controllers connected:", num_controllers)

# Check if there are two controllers connected
if num_controllers < 2:
    print("Two controllers are required for this test.")
    exit()

# Initialize both controllers
controller_1 = pygame.joystick.Joystick(0)  # PS4 controller (Team 1)
print("Initializing controller 1:", controller_1.get_name())
controller_1.init()
print("Controller 1 initialized:", controller_1.get_name())

controller_2 = pygame.joystick.Joystick(1)  # Xbox One controller (Team 2)
print("Initializing controller 2:", controller_2.get_name())
controller_2.init()
print("Controller 2 initialized:", controller_2.get_name())

# Set up the Pygame display
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Controller Test")

# Define fonts for displaying text
font = pygame.font.Font(None, 74)

# Set initial message
message_team_1 = "Team 1: Press X (PS4)"
message_team_2 = "Team 2: Press A (Xbox)"
team_1_color = (255, 255, 255)  # White color for team 1
team_2_color = (255, 255, 255)  # White color for team 2

# Main loop
running = True
while running:
    # Clear the screen
    screen.fill((0, 0, 0))  # Black background
    
    # Display instructions
    text_team_1 = font.render(message_team_1, True, team_1_color)
    screen.blit(text_team_1, (50, 150))

    text_team_2 = font.render(message_team_2, True, team_2_color)
    screen.blit(text_team_2, (50, 250))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        # Check for button presses from both controllers
        if event.type == pygame.JOYBUTTONDOWN:
            if event.joy == 0:  # Team 1's controller (PS4 controller)
                if event.button == 0:  # "X" button on PS4
                    message_team_1 = "Team 1 OK!"
                    team_1_color = (0, 255, 0)  # Change color to green for success

            if event.joy == 1:  # Team 2's controller (Xbox One controller)
                if event.button == 0:  # "A" button on Xbox One
                    message_team_2 = "Team 2 OK!"
                    team_2_color = (0, 255, 0)  # Change color to green for success

    time.sleep(0.1)

# Quit Pygame
pygame.quit()

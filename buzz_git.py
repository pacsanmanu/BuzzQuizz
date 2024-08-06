import pybuzzers
import time
import pygame
import threading

TIME_TO_ANSWER = 10

buzzer_controller = pybuzzers.get_all_buzzers()[0]

buzzer_controller.set_lights([False, False, False, False])

pygame.init()

beep_sound = pygame.mixer.Sound('beep.mp3')
error = pygame.mixer.Sound('error.mp3')
correct = pygame.mixer.Sound('correct.mp3')

correct_answer = False
correct_answer_mutex = threading.Lock()
countdown_active = False
countdown_active_mutex = threading.Lock()
first_buzzer_time = 0
second_buzzer_time = 0

def respond_to_press(buzzer_set: pybuzzers.BuzzerSet, buzzer: int, button: int):
    '''
    Responds to a button press on a buzzer.
    '''
    global countdown_active
    global correct_answer
    global first_buzzer_time
    global second_buzzer_time

    # Controllers 0 and 1 are the only ones that can buzz in
    with countdown_active_mutex:
        if buzzer in [0, 1] and button == 0 and not countdown_active:
            first_buzzer_time = time.time()
            countdown_active = True
            thread_turns = threading.Thread(target=handle_answer, args=(buzzer, True))
            thread_turns.start()
        elif buzzer in [0, 1] and button == 0 and countdown_active and second_buzzer_time == 0:
            second_buzzer_time = time.time()
            print(f"+{second_buzzer_time - first_buzzer_time}")
        # The others are used to mark a correct answer
        elif buzzer in [2, 3] and countdown_active:
            with correct_answer_mutex:
                correct_answer = True

def reset_lights():
    '''
    Turns off the lights of the buzzers.
    '''
    buzzer_controller.set_lights([False, False, False, False])

def handle_answer(buzzer: int, with_rebound: bool):
    '''
    Handles the case where a player can answer, optionally with rebounding.
    If with_rebound is True, the other player can answer if the first player does not answer in time.
    '''
    reset_lights()

    buzzers = [buzzer] if not with_rebound else [buzzer, 1 - buzzer]

    for current_buzzer in buzzers:
        if countdown_light(current_buzzer):
            break

    reset_lights()

    with countdown_active_mutex:
        global countdown_active
        countdown_active = False

    global first_buzzer_time
    global second_buzzer_time

    first_buzzer_time = 0
    second_buzzer_time = 0


def countdown_light(buzzer):
    '''
    Lights up the buzzer and waits for the player to answer.
    Returns True if the player answered correctly, False if the player did not answer in time or answered incorrectly.
    '''
    global correct_answer, countdown_active
    with correct_answer_mutex:
        correct_answer = False
    actual_seconds = time.time()

    while time.time() - actual_seconds < TIME_TO_ANSWER:
        with correct_answer_mutex:
            if correct_answer:
                # Correct answer
                correct.play()
                buzzer_controller.set_light(buzzer, True)
                time.sleep(1)
                buzzer_controller.set_light(buzzer, False)
                with countdown_active_mutex:
                    countdown_active = False
                return True
        
        # Calculate remaining time
        elapsed_time = time.time() - actual_seconds
        remaining_time = TIME_TO_ANSWER - elapsed_time
        
        # Set on-time and off-time to be proportional to remaining time
        on_time = max(0.05, remaining_time / (2 * TIME_TO_ANSWER))
        off_time = max(0.05, remaining_time / (2 * TIME_TO_ANSWER))
        
        # Turn the light on
        buzzer_controller.set_light(buzzer, True)
        beep_sound.play()
        
        # Wait for the calculated on-time
        time.sleep(on_time)
        
        # Turn the light off
        buzzer_controller.set_light(buzzer, False)
        
        # Wait for the calculated off-time before turning the light on again
        time.sleep(off_time)
    
    error.play()
    return False

buzzer_controller.on_button_down(respond_to_press)

buzzer_controller.start_listening()

while True:
    time.sleep(0.1)

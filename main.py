import pybuzzers
import time
import pygame
import threading
import multiprocessing

from ui import update_display

TIME_TO_ANSWER = 8
REBOUND = True
TEAM_1_NAME = "TEAM A"
TEAM_2_NAME = "TEAM B"

try:
    buzzer_controller = pybuzzers.get_all_buzzers()[0]
except:
    print("Could not find controllers, ensure they are connected")
    exit()

buzzer_controller.set_lights([False, False, False, False])

pygame.init()

beep_sound = pygame.mixer.Sound('data/sounds/beep.mp3')
error = pygame.mixer.Sound('data/sounds/error.mp3')
correct = pygame.mixer.Sound('data/sounds/correct.mp3')
clown = pygame.mixer.Sound('data/sounds/clown.mp3')
horn = pygame.mixer.Sound('data/sounds/horn.mp3')

buzz_sounds = [clown, horn]

correct_answer = False
answer_mutex = threading.Lock()
wrong_answer = False
answer_mutex = threading.Lock()
countdown_active = False
countdown_active_mutex = threading.Lock()
first_buzzer_time_player = [0, -1]
second_buzzer_time_player = [0, -1]

team_names = [TEAM_1_NAME, TEAM_2_NAME]
team_colors = [(0, 120, 255), (255, 255, 0)]

def respond_to_press(buzzer_set: pybuzzers.BuzzerSet, buzzer: int, button: int, queue):
    global countdown_active
    global correct_answer
    global wrong_answer
    global first_buzzer_time_player
    global second_buzzer_time_player

    if buzzer in [0, 1] and button == 0 and not countdown_active:
        buzz_sounds[buzzer].play()
        first_buzzer_time_player = [time.time(), buzzer]
        with countdown_active_mutex:
            countdown_active = True
        thread_turns = threading.Thread(target=handle_answer, args=(buzzer, REBOUND, queue))
        thread_turns.start()
    elif buzzer in [0, 1] and button == 0 and countdown_active:
        if second_buzzer_time_player[1] == -1 and buzzer != first_buzzer_time_player[1]:
            second_buzzer_time_player = [time.time(), buzzer]
            time_diff = second_buzzer_time_player[0] - first_buzzer_time_player[0]
            queue.put(f"+{time_diff:.3f} seconds")
    elif buzzer in [2, 3] and button == 0 and countdown_active:
        with answer_mutex:
            if countdown_active:
                correct_answer = True
    elif buzzer in [2, 3] and button in [1,2,3,4] and countdown_active:
        with answer_mutex:
            if countdown_active:
                wrong_answer = True

def reset_lights():
    buzzer_controller.set_lights([False, False, False, False])

def handle_answer(buzzer: int, with_rebound: bool, queue):
    reset_lights()

    buzzers = [buzzer] if not with_rebound else [buzzer, 1 - buzzer]

    for current_buzzer in buzzers:
        if countdown_light(current_buzzer, queue):
            break

    reset_lights()

    with countdown_active_mutex:
        global countdown_active
        countdown_active = False

    global first_buzzer_time_player
    global second_buzzer_time_player

    first_buzzer_time_player = [0, -1]
    second_buzzer_time_player = [0, -1]

    # Clear the team text
    queue.put(("", (255, 255, 255)))

def countdown_light(buzzer, queue):
    queue.put((f"{team_names[buzzer]}", team_colors[buzzer]))

    global correct_answer, countdown_active, wrong_answer
    with answer_mutex:
        correct_answer = False
    with answer_mutex:
        wrong_answer = False
    actual_seconds = time.time()

    while time.time() - actual_seconds < TIME_TO_ANSWER:
        with answer_mutex:
            if correct_answer:
                correct.play()
                queue.put(("Correct", (0,255,0)))
                queue.put("")
                buzzer_controller.set_light(buzzer, True)
                while pygame.mixer.get_busy():
                    pass
                buzzer_controller.set_light(buzzer, False)
                return True

            if wrong_answer:
                error.play()
                queue.put(("Incorrect", (255,0,0)))
                queue.put("")
                buzzer_controller.set_light(buzzer, True)
                while pygame.mixer.get_busy():
                    pass
                buzzer_controller.set_light(buzzer, False)
                return False

        elapsed_time = time.time() - actual_seconds
        remaining_time = TIME_TO_ANSWER - elapsed_time
        on_time = max(0.05, remaining_time / (2 * TIME_TO_ANSWER))
        off_time = max(0.05, remaining_time / (2 * TIME_TO_ANSWER))

        buzzer_controller.set_light(buzzer, True)
        beep_sound.play()
        time.sleep(on_time)
        buzzer_controller.set_light(buzzer, False)
        time.sleep(off_time)    

    error.play()
    queue.put(("Tiempo!", (255,0,0)))
    queue.put("")
    while pygame.mixer.get_busy():
        pass
    return False

def main():
    queue = multiprocessing.Queue()
    ui_process = multiprocessing.Process(target=update_display, args=(queue,))
    ui_process.start()

    buzzer_controller.on_button_down(lambda buzzer_set, buzzer, button: respond_to_press(buzzer_set, buzzer, button, queue))
    buzzer_controller.start_listening()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        reset_lights()
        ui_process.terminate()
        ui_process.join()

if __name__ == '__main__':
    main()

import pygame
import time
import threading
import multiprocessing

from ui import update_display

TIME_TO_ANSWER = 8
REBOUND = True
TEAM_1_NAME = "TIGRES"
TEAM_2_NAME = "LEONES"

pygame.init()
pygame.joystick.init()

# Inicializar mandos
try:
    joystick_team_1 = pygame.joystick.Joystick(0)
    joystick_team_1.init()
    joystick_team_2 = pygame.joystick.Joystick(1)
    joystick_team_2.init()
except pygame.error:
    print("Could not find controllers, ensure they are connected")
    exit()

beep_sound = pygame.mixer.Sound('data/sounds/beep.mp3')
error = pygame.mixer.Sound('data/sounds/error.mp3')
correct = pygame.mixer.Sound('data/sounds/correct.mp3')
clown = pygame.mixer.Sound('data/sounds/clown.mp3')
horn = pygame.mixer.Sound('data/sounds/horn.mp3')
timesup = pygame.mixer.Sound('data/sounds/timesup.mp3')

buzz_sounds = [clown, horn]

correct_answer = False
answer_mutex = threading.Lock()
wrong_answer = False
countdown_active = False
countdown_active_mutex = threading.Lock()
first_buzzer_time_player = [0, -1]
second_buzzer_time_player = [0, -1]

team_names = [TEAM_1_NAME, TEAM_2_NAME]
team_colors = [(0, 120, 255), (255, 255, 0)]

def respond_to_press(joystick, team, queue):
    global countdown_active
    global correct_answer
    global wrong_answer
    global first_buzzer_time_player
    global second_buzzer_time_player

    # Detectar botón "X" (botón 0)
    if team in [0, 1] and joystick.get_button(0) and not countdown_active:
        buzz_sounds[team].play()
        first_buzzer_time_player = [time.time(), team]
        with countdown_active_mutex:
            countdown_active = True
        thread_turns = threading.Thread(target=handle_answer, args=(team, REBOUND, queue))
        thread_turns.start()

    # Si otro equipo presiona "X" después del primer equipo
    elif team in [0, 1] and joystick.get_button(0) and countdown_active:
        if second_buzzer_time_player[1] == -1 and team != first_buzzer_time_player[1]:
            second_buzzer_time_player = [time.time(), team]
            time_diff = second_buzzer_time_player[0] - first_buzzer_time_player[0]
            queue.put(f"+{time_diff:.3f} segundos")

def handle_answer(team: int, with_rebound: bool, queue):
    global second_buzzer_time_player

    buzzers = [team] if not with_rebound else [team, 1 - team]

    for current_buzzer in buzzers:
        if countdown_light(current_buzzer, queue) or second_buzzer_time_player[1] == -1:
            break

    with countdown_active_mutex:
        global countdown_active
        countdown_active = False

    global first_buzzer_time_player
    first_buzzer_time_player = [0, -1]
    second_buzzer_time_player = [0, -1]

    # Limpiar el texto del equipo
    queue.put(("", (255, 255, 255)))

def countdown_light(team, queue):
    queue.put((f"{team_names[team]}", team_colors[team]))

    global correct_answer, countdown_active, wrong_answer
    with answer_mutex:
        correct_answer = False
        wrong_answer = False
    actual_seconds = time.time()

    while time.time() - actual_seconds < TIME_TO_ANSWER:
        # Revisar entrada del moderador desde event_queue
        try:
            event = event_queue.get_nowait()
            with answer_mutex:
                if event == 'enter':
                    correct_answer = True
                elif event == 'space':
                    wrong_answer = True
        except multiprocessing.queues.Empty:
            pass

        with answer_mutex:
            if correct_answer:
                correct.play()
                queue.put(("Correcto", (0,255,0)))
                queue.put("")
                time.sleep(2)  # Mostrar "Correcto" por 2 segundos
                return True

            if wrong_answer:
                error.play()
                queue.put(("Incorrecto", (255,0,0)))
                queue.put("")
                time.sleep(2)  # Mostrar "Incorrecto" por 2 segundos
                return False

        elapsed_time = time.time() - actual_seconds
        remaining_time = TIME_TO_ANSWER - elapsed_time
        on_time = max(0.05, remaining_time / (2 * TIME_TO_ANSWER))
        off_time = max(0.05, remaining_time / (2 * TIME_TO_ANSWER))

        beep_sound.play()
        time.sleep(on_time)
        time.sleep(off_time)

    timesup.play()
    queue.put(("Tiempo!", (255,155,0)))
    queue.put("")
    time.sleep(2)  # Mostrar "¡Tiempo!" por 2 segundos
    return False

def main():
    global event_queue

    queue = multiprocessing.Queue()
    event_queue = multiprocessing.Queue()
    ui_process = multiprocessing.Process(target=update_display, args=(queue, event_queue))
    ui_process.start()

    try:
        while True:
            # Procesar eventos de pygame, incluyendo los de joystick
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    # Joystick 0 es para el equipo 1, joystick 1 es para el equipo 2
                    if event.joy == 0:
                        respond_to_press(joystick_team_1, 0, queue)
                    elif event.joy == 1:
                        respond_to_press(joystick_team_2, 1, queue)
            # No es necesario procesar eventos de teclado aquí

            time.sleep(0.1)
    except KeyboardInterrupt:
        ui_process.terminate()
        ui_process.join()

if __name__ == '__main__':
    main()

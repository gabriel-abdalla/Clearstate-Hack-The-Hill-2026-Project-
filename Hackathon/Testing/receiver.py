import pygame
import socket
import threading
import json

#setup base host and port 
HOST = "127.0.0.1"
PORT = 5000

latest_apps = [] #receiving all apps

#TO RUN SCRIPT: pythonw.exe "C:\Andrew C\Hackathon\Script Tests\app_monitor.py"


def receive_apps():
    global latest_apps

    #server setup
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    connection, address = server.accept() #function pauses unless a connection is made (if script isnt open)

    buffer = "" #collect data until a new line is found

    while True:
        data = connection.recv(4096) #reads MAX 4096 bytes, (really dont need more)

        if not data: #if connection dies break whole loop and stop receiving data
            break

        buffer += data.decode("utf-8") #converts data into a string and adds it to the buffer

        while "\n" in buffer: #iff the buffer creates a new line, it means a full message has been received, so we can process it
            message, buffer = buffer.split("\n", 1) #slit at end, reset buffer, store message
            latest_apps = json.loads(message) #convert the message into a python object (list of dicts)
            for app in latest_apps:
                print(app) #full JSON string
                print(app["name"]) #individual name (2D list section)
                print(app["window"]) #window title (2D list section)

# background thread handles script, so the main thread can handle the pygame window
threading.Thread(          
    target=receive_apps,
    daemon=True
).start()


pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Application Monitor")

font = pygame.font.Font(None, 32)

running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))
    y = 30

    for app in latest_apps:
        text = f"{app['name']} - {app['window']}"
        surface = font.render(text, True, (255, 255, 255))
        screen.blit(surface, (30, y))
        y += 40

    pygame.display.flip()

pygame.quit()
import pygame
import time
from analyzer import Analyzer

def main():
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("No joystick detected.")
        return
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    print(f"Initialized Joystick: {joystick.get_name()}")


    last_hats = [(0, 0)]    
    Ana = Analyzer()
    time_saved = time.time()
    time_changed = time.time()

    running = True
    while running:
        pygame.event.pump()
        
        # Buttons
        buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
        #print("Buttons:", buttons)
        if any(buttons):
            Ana.save_recorded("recorded.txt")
            running = False
        
        # Axes
        axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
        #print("Axes:", axes)
        
        # Hats (D-Pad)
        hats = [joystick.get_hat(i) for i in range(joystick.get_numhats())]
        
        # If hats changed, add to Analyzer
        if hats != last_hats and hats != [(0, 0)]:
            #print("Hats:", hats)
            Ana.add(hats)
            print("time_changed:", int(time.time() -time_changed))
            print("time_saved:", int(time.time() -time_saved))
            time_changed = time.time()

        last_hats = hats
        
        # Auto save after x seconds of inactivity, and y seconds of last save
        x = 10
        y = 20
        time_now = time.time()
        if time_now - time_changed > 10 and time_now - time_saved > 20:
            Ana.save_recorded("recorded.txt")
            time_saved = time.time()
        
        #pygame.time.wait(100)  # Small delay to avoid spamming output
        
if __name__ == "__main__":
    main()
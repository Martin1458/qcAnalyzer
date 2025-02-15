import time
import pyautogui

time.sleep(2)
pyautogui.press('1')
time_start = time.time()
time.sleep(1.68)
pyautogui.press('1')
time_end = time.time()
print("Delay:", time_end - time_start)

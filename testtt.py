import pywhatkit
import pyautogui
import time
pywhatkit.sendwhats_image(
    receiver=f"+918792631798",
    img_path="frame.png",
    caption="Scan the QR code for patient info",
    wait_time=20,  
    tab_close=True, 
    close_time=3    
)

time.sleep(5) 
pyautogui.press("enter")
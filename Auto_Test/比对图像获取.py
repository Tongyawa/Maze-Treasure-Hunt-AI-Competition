import pyautogui
import time
from pynput import mouse, keyboard 
from PIL import Image


x1,y1=0,0
def to(x,y,t):
    pyautogui.click(x, y)
    time.sleep(t)
def compare1(a,b,c,x,y,z):
    return (abs(a-x)<=8 and abs(b-y)<=8 and abs(c-z)<=8)

def on_click(x, y, button, pressed):  
    # 这个函数在鼠标事件时被调用，但在这个例子中我们主要关注键盘事件  
    if pressed:  
        global x1,y1
        x1,y1=x,y

def test(x,y):

    finish = False

    x1, y1 = 1385, 1233  #输出log中第一行的左上角端点坐标
    x2, y2 = 1568, 1257  #输出log中第一行的右下角端点坐标
      
    # 截取屏幕区域  
    screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1)) 
    screenshot.save('original_image.png')


import keyboard
 
def on_key_press(event):
    print(f"Key {event.name} pressed")
    if event.name=="d":
        global x1,y1
        x,y=x1,y1
        test(x1,y1)
with mouse.Listener(on_click=on_click) as listener:
    keyboard.hook(on_key_press)
    keyboard.wait('ctrl')  # 等待用户按下Ctrl键后停止监听

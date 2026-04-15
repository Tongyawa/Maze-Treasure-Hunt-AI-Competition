import pyautogui
import time
from pynput import mouse, keyboard 
from PIL import Image,ImageGrab
import imagehash
import keyboard
flag=True
x_button, y_button=2243,377
input("请输入测试信息：")
def to(x,y,t):
    pyautogui.click(x, y)
    time.sleep(t)

def compare1(a,b,c,x,y,z):
    return abs(a-x)<=8 and abs(b-y)<=8 and abs(c-z)<=8

rst=0
for i in range(10):#测试次数
    to(x_button,y_button,1)
    finish = False
    while not finish:
        time.sleep(2)
        screen1 = ImageGrab.grab()
        r1, g1, b1 = screen1.getpixel((x_button,y_button))
        finish = compare1(r1,g1,b1,146,237,140)

    x1, y1 = 1337, 1233  #输出log中第一行的左上角端点坐标
    x2, y2 = 1520, 1257  #输出log中第一行的右下角端点坐标
                  
                # 截取屏幕区域  
    screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
    # screenshot.save(str(i)+'new_image.png')

                # 加载原图  
    cropped_original = Image.open('original_image.png')  
                  
                # 计算两个图像的哈希值  
    hash1 = imagehash.average_hash(screenshot)  
    hash2 = imagehash.average_hash(cropped_original)  
                  
                # 比较哈希值  
    diff = abs(hash1 - hash2)
    # print(diff, end=' ')
                  
      
                # 你可以设置一个阈值来判断是否足够相似  
    THRESHOLD = 5
    if diff < THRESHOLD:  
        rst+=1
    print(rst,"/",i+1)



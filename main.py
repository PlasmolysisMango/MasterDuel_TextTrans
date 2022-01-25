import os
import time
from PIL import Image,ImageFile
import sqlite3
import win32api,win32gui,win32ui,win32con,win32print
import ctypes
from tiny_ocr import file_to_string

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

md_process_window_name='masterduel'

cardsdb_eng_dir = './cards_eng.db'
cardsdb_chn_dir = './cards_chn.db'

tmp_img_path = './tmp.png'

#screen_shot for 1280x720
#以下所有坐标均按照该分辨率为准
#shot where card image locate
#deck
deck_width = 227
deck_height = 23
deck_left_top = 38,82
deck_right_bottom = deck_left_top[0]+deck_width,deck_left_top[1]+deck_height
# deck_left_top=(64,200)
# deck_right_bottom=(64+144,200+210)
#duel
duel_width = 200
duel_height = 23
duel_left_top=26, 102
duel_right_bottom=duel_left_top[0]+duel_width, duel_left_top[1]+duel_height

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def get_game_window_info():
    hwnd=win32gui.FindWindow(0,md_process_window_name)
    return hwnd 

def window_shot_image(hwnd:int):
    app = win32gui.GetWindowText(hwnd)
    if not hwnd or hwnd<=0 or len(app)==0:
        return False,'Not found md game process,exit'

    hDC = win32gui.GetDC(0)
    dpi1 = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    dpi2 = win32print.GetDeviceCaps(hDC, win32con.HORZRES)
    scale_factor = dpi1 / dpi2
    
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    
    w = int((right - left)*scale_factor)
    h = int((bot - top)*scale_factor)
    
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)
    
    result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    if result != 1:
        return False,"print window failed"
    return True,{
        "image":im,
        "current_window_zoom":(w/1280,h/720),
        "scale_factor": scale_factor
    }

def get_window_rect(hwnd):
    try:
        f =ctypes.windll.dwmapi.DwmGetWindowAttribute
    except WindowsError:
        f = None
    if f:
        rect = ctypes.wintypes.RECT()
        f(ctypes.wintypes.HWND(hwnd), ctypes.wintypes.DWORD(9), ctypes.byref(rect), ctypes.sizeof(rect))
        return rect.left, rect.top, rect.right, rect.bottom

def cv_card_name_deck(img:Image,zoom:tuple) -> str:
    '''
    识别卡名(卡组界面)
    '''
    zoom_w=zoom[0]
    zoom_h=zoom[1]
    crop_area = (deck_left_top[0]*zoom_w,deck_left_top[1]*zoom_h,
                deck_right_bottom[0]*zoom_w,deck_right_bottom[1]*zoom_h)
    img = img.crop(crop_area)
    img = img.convert('L')
    img = img.resize((int(deck_width*zoom_w*1.5), int(deck_height*zoom_h*1.5)), Image.ANTIALIAS)
    img.save(tmp_img_path)
    str = file_to_string(tmp_img_path)
    # print(str)
    return str

def cv_card_name_duel(img:Image,zoom:tuple) -> str:
    '''
    识别卡名(决斗界面)
    '''
    zoom_w=zoom[0]
    zoom_h=zoom[1]
    crop_area = (duel_left_top[0]*zoom_w,duel_left_top[1]*zoom_h,
                duel_right_bottom[0]*zoom_w,duel_right_bottom[1]*zoom_h)
    img = img.crop(crop_area)
    img = img.convert('L')
    img = img.resize((int(duel_width*zoom_w*1.5), int(duel_height*zoom_h*1.5)), Image.ANTIALIAS)
    img.save(tmp_img_path)
    str = file_to_string(tmp_img_path)
    # print(str)
    return str

def listen_mouse():
    if os.path.exists(tmp_img_path):
        os.remove(tmp_img_path)
    print('使用方法: 点击需要识别的卡片待其显示在左侧之后，点击鼠标中键即可识别。\n可自动识别决斗和组卡场景，不需要额外操作')
    state_middle = win32api.GetKeyState(0x04) # Middle button down = 0 or 1. Button up = -127 or -128
    while True:
        c = win32api.GetKeyState(0x04)
        if c != state_middle:  # Button state changed
            state_middle = c
            # print(c)
            if c >= 0:
                mainloop(1)
                pass
        time.sleep(0.01)

def compare_rgb(rgb1, rgb2) -> int:
    r = abs(rgb1[0]-rgb2[0])
    g = abs(rgb1[1]-rgb2[1])
    b = abs(rgb1[2]-rgb2[2])
    return max(r,g,b)

def judge_type(img: Image, zoom = tuple) -> int:
    '''
    type==1:
        翻译卡组卡片
    type==2:
        翻译决斗卡片
    type==0:
        识别失败
    '''
    deck_point = int(30*zoom[0]),int(32*zoom[1])
    deck_rgb = 200,250,0
    duel_point = int(33*zoom[0]),int(34*zoom[1])
    duel_rgb = 32,185,251
    maxerr = 20
    str_strlist = img.load()
    while True:
        deck_check = str_strlist[deck_point[0],deck_point[1]]
        if compare_rgb(deck_check,deck_rgb) < maxerr:
            return 1
        duel_check = str_strlist[duel_point[0], duel_point[1]]
        if compare_rgb(duel_check, duel_rgb) < maxerr:
            return 2
        maxerr += 5
        if maxerr > 100:
            return 0

def transcontent(content) -> str:
    if not content:
        return None
    else:
        string = ""
        for c in content:
            if c == '"':
                string += c
            elif c == "'":
                string += "''"
            elif c == "\\":
                string += "\\\\"
            elif c == "—":
                string += "-"
            else:
                string += c
    return string
            

def mainloop(type:int):
    hwnd=get_game_window_info()
    status,result=window_shot_image(hwnd)
    if not status:
        print('screenshot failed!')
        return None
    img = result['image']
    zoom = result['current_window_zoom']
    type = judge_type(img, zoom)
    cls()
    card_str=None
    if type==1:
        # print("翻译卡组卡片")
        card_str=cv_card_name_deck(img, zoom)
    elif type==2:
        # print("翻译决斗卡片")
        card_str=cv_card_name_duel(img, zoom)
    else:
        print('识别场景失败')
        return
    if not card_str:
        print('识别卡名失败')
        return
    eng_sql = sqlite3.connect(cardsdb_eng_dir)
    chn_sql = sqlite3.connect(cardsdb_chn_dir)
    trytimes = 0
    while (trytimes < 3):
        cursor = eng_sql.execute("SELECT id,name from texts WHERE name LIKE '%{}%' LIMIT 1".format(transcontent(card_str)))
        data=cursor.fetchone()
        if not data:
            card_str = card_str[:-1]
            trytimes += 1
            continue
        else:
            card_id = data[0]
            card_name = data[1]
            break
    if not data:
        print(f"card {card_str} not found in english database")
        eng_sql.close()
        chn_sql.close()
        return
    cursor = chn_sql.execute("SELECT name,desc from texts WHERE id = ? LIMIT 1", (card_id, ))
    data=cursor.fetchone()
    if cursor.arraysize!=1 or not data:
        print(f"card {card_name} not found in chinese database")
        eng_sql.close()
        chn_sql.close()
        return
    card_name_chn = data[0]
    card_desc = data[1]

    print("-----------------------------------")
    print('id: {}\n中文卡名: {}\n英文卡名: {}\n效果: {}\n'.format(card_id, card_name_chn, card_name, card_desc))

    eng_sql.close()
    chn_sql.close()
    if os.path.exists(tmp_img_path):
        os.remove(tmp_img_path)
    
if __name__ == '__main__':
    listen_mouse()
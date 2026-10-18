import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math
import time
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
screen_w, screen_h = pyautogui.size()
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
cap = cv2.VideoCapture(0)
margin = 100
smooth = 5
prev_x, prev_y = 0, 0
last_click = 0
last_right = 0
prev_scroll_y = None
while True:
    success, img = cap.read()
    if not success:
        print("Camera not working")
        break
    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    result = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    cv2.rectangle(img, (margin, margin), (w - margin, h - margin), (255, 0, 255), 2)
    mode = ""
    if result.multi_hand_landmarks:
        hand = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)
        lm = [(int(p.x * w), int(p.y * h)) for p in hand.landmark]
        ix, iy = lm[8]
        mx, my = lm[12]
        index_up = lm[8][1] < lm[6][1]
        middle_up = lm[12][1] < lm[10][1]
        ring_up = lm[16][1] < lm[14][1]
        pinky_up = lm[20][1] < lm[18][1]
        if index_up and middle_up and ring_up and not pinky_up:
            mode = "SCROLL"
            if prev_scroll_y is not None:
                dy = prev_scroll_y - iy
                if abs(dy) > 3:
                    pyautogui.scroll(int(dy * 5))
            prev_scroll_y = iy
        else:
            prev_scroll_y = None
            if index_up and middle_up and not ring_up:
                mode = "CLICK MODE"
                dist = math.hypot(mx - ix, my - iy)
                cv2.line(img, (ix, iy), (mx, my), (255, 0, 0), 3)
                if dist < 40 and time.time() - last_click > 0.5:
                    pyautogui.click()
                    last_click = time.time()
                    cv2.circle(img, (ix, iy), 15, (0, 0, 255), -1)
            elif index_up and not middle_up and not ring_up and not pinky_up:
                mode = "MOVE"
                x = np.interp(ix, (margin, w - margin), (0, screen_w))
                y = np.interp(iy, (margin, h - margin), (0, screen_h))
                cur_x = prev_x + (x - prev_x) / smooth
                cur_y = prev_y + (y - prev_y) / smooth
                pyautogui.moveTo(cur_x, cur_y)
                prev_x, prev_y = cur_x, cur_y
                cv2.circle(img, (ix, iy), 12, (0, 255, 0), -1)
            elif pinky_up and not index_up and not middle_up and not ring_up:
                mode = "RIGHT CLICK"
                if time.time() - last_right > 1:
                    pyautogui.rightClick()
                    last_right = time.time()
    else:
        prev_scroll_y = None
    cv2.putText(img, mode, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv2.imshow("Virtual Mouse", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
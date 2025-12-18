import cvzone
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import math
import random

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = HandDetector(detectionCon=0.8, maxHands=1)

class SnakeGameClass:
    def __init__(self, pathFood):
        self.points = []
        self.lengths = []
        self.currentLength = 0
        self.allowedLength = 150
        self.previousHead = (640, 360)
        self.score = 0
        self.gameOver = False
        self.paused = False

        self.imgFood = cv2.imread(pathFood, cv2.IMREAD_UNCHANGED)
        if self.imgFood is None:
            raise FileNotFoundError(f"Image file '{pathFood}' not found.")
        self.hFood, self.wFood, _ = self.imgFood.shape
        self.foodpoint = (0, 0)
        self.randomFoodLocation()

    def randomFoodLocation(self):
        self.foodpoint = random.randint(100, 1100), random.randint(100, 600)

    def update(self, imgMain, currentHead):
        cx, cy = currentHead

        if self.gameOver:
            cvzone.putTextRect(imgMain, "Game Over", (300, 400), scale=7,
                               thickness=5, colorR=(0, 0, 255), colorT=(255, 255, 255))
            cvzone.putTextRect(imgMain, f"Score: {self.score}", (500, 550), scale=5,
                               thickness=5, colorR=(0, 0, 255), colorT=(255, 255, 255))
            return imgMain

        if self.paused:
            cvzone.putTextRect(imgMain, "PAUSED", (450, 300), scale=6,
                               thickness=5, colorR=(50, 50, 50))
            cvzone.putTextRect(imgMain, "Press P to Resume", (420, 380),
                               scale=3, thickness=3)
            self.previousHead = (cx, cy)
        else:
            px, py = self.previousHead
            self.points.append([cx, cy])
            distance = math.hypot(cx - px, cy - py)
            self.lengths.append(distance)
            self.currentLength += distance
            self.previousHead = (cx, cy)

            while self.currentLength > self.allowedLength and self.lengths:
                self.currentLength -= self.lengths.pop(0)
                self.points.pop(0)

            # Check for food
            rx, ry = self.foodpoint
            food_radius = max(self.wFood, self.hFood) // 2 + 15
            if (rx - food_radius < cx < rx + food_radius and
                ry - food_radius < cy < ry + food_radius):
                self.randomFoodLocation()
                self.allowedLength += 50
                self.score += 1

            # Check for collision
            if len(self.points) > 36:
                head = np.array([cx, cy])
                
                
                for point in self.points[10:25]:
                    body_point = np.array(point)
                    dist = np.linalg.norm(head - body_point)
                    if dist < 22:  
                        print("Head touched body! Game Over!")
                        self.gameOver = True
                        break
                
                if not self.gameOver:
                    for point in self.points[32:-10]:
                        body_point = np.array(point)
                        dist = np.linalg.norm(head - body_point)
                        if dist < 28:
                            print("Game Over!")
                            self.gameOver = True
                            break

        # Snake Draw
        if self.points:
            total = len(self.points)
            for i in range(1, total):
                p1 = tuple(self.points[i-1])
                p2 = tuple(self.points[i])
                t = i / float(total)
                thickness = int(8 + 18 * t)
                color = (0, int(120 + 135 * t), 0)
                cv2.line(imgMain, p1, p2, color, thickness)

            head = tuple(self.points[-1])
            if total >= 2:
                hx, hy = self.points[-1]
                tx, ty = self.points[-2]
                dx, dy = hx - tx, hy - ty
                mag = math.hypot(dx, dy) or 1.0
                ux, uy = dx / mag, dy / mag
            else:
                ux, uy = 1.0, 0.0

            px, py = -uy, ux

            head_center = (int(head[0]), int(head[1]))
            major, minor = 32, 24
            angle = math.degrees(math.atan2(uy, ux))
            cv2.ellipse(imgMain, head_center, (major // 2, minor // 2), angle, 0, 360, (0, 180, 0), cv2.FILLED)
            cv2.ellipse(imgMain, head_center, (major // 2, minor // 2), angle, 0, 360, (0, 130, 0), 2)

            eye_offset = 10
            forward_offset = 4
            ex1 = int(head_center[0] + px * eye_offset + ux * forward_offset)
            ey1 = int(head_center[1] + py * eye_offset + uy * forward_offset)
            ex2 = int(head_center[0] - px * eye_offset + ux * forward_offset)
            ey2 = int(head_center[1] - py * eye_offset + uy * forward_offset)
            cv2.circle(imgMain, (ex1, ey1), 6, (255, 255, 255), cv2.FILLED)
            cv2.circle(imgMain, (ex2, ey2), 6, (255, 255, 255), cv2.FILLED)
            pupil_forward = 3
            cv2.circle(imgMain, (int(ex1 + ux * pupil_forward), int(ey1 + uy * pupil_forward)), 3, (0, 0, 0), cv2.FILLED)
            cv2.circle(imgMain, (int(ex2 + ux * pupil_forward), int(ey2 + uy * pupil_forward)), 3, (0, 0, 0), cv2.FILLED)

            mouth_x = int(head_center[0] + ux * (major // 2))
            mouth_y = int(head_center[1] + uy * (major // 2))
            tip_len = 14
            fork = 6
            tip = (int(mouth_x + ux * tip_len), int(mouth_y + uy * tip_len))
            left_tip = (int(mouth_x + ux * (tip_len - 6) + px * fork), int(mouth_y + uy * (tip_len - 6) + py * fork))
            right_tip = (int(mouth_x + ux * (tip_len - 6) - px * fork), int(mouth_y + uy * (tip_len - 6) - py * fork))
            cv2.line(imgMain, (mouth_x, mouth_y), tip, (0, 0, 255), 2)
            cv2.line(imgMain, tip, left_tip, (0, 0, 255), 2)
            cv2.line(imgMain, tip, right_tip, (0, 0, 255), 2)

        # Draw Food
        rx, ry = self.foodpoint
        imgMain = cvzone.overlayPNG(imgMain, self.imgFood,
                                   (rx - self.wFood // 2, ry - self.hFood // 2))

        # UI
        cvzone.putTextRect(imgMain, f"Score: {self.score}", (50, 80), scale=3,
                           thickness=3, colorR=(0, 0, 0), colorT=(255, 255, 255))
        cvzone.putTextRect(imgMain, "P - Pause | R - Restart", (50, 140),
                           scale=2, thickness=2)

        return imgMain

    def reset(self):
        self.points = []
        self.lengths = []
        self.currentLength = 0
        self.allowedLength = 150
        self.previousHead = (640, 360)
        self.score = 0
        self.gameOver = False
        self.paused = False
        self.randomFoodLocation()

game = SnakeGameClass("Snake_game/donuta.png")

lastHead = (640, 360)

while True:
    success, img = cap.read()
    if not success:
        break
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    if hands:
        lmList = hands[0]['lmList']
        pointindex = lmList[8][0:2]
        currentHead = pointindex
        lastHead = pointindex
    else:
        currentHead = lastHead

    img = game.update(img, currentHead)

    cv2.imshow("Image", img)
    key = cv2.waitKey(1)

    if key == ord('p') or key == ord('P'):
        if not game.gameOver:
            game.paused = not game.paused

    if key == ord('r') or key == ord('R'):
        game.reset()

    if key == 27:
        break
cap.release()
cv2.destroyAllWindows()
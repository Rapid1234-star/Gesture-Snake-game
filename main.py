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
        self.previousHead = (640, 360)  # Start in center
        self.score = 0
        self.gameOver = False
        self.paused = False

        self.imgFood = cv2.imread(pathFood, cv2.IMREAD_UNCHANGED)
        if self.imgFood is None:
            raise FileNotFoundError(f"Image file '{pathFood}' not found. Ensure the file exists in the script's directory.")
        self.hFood, self.wFood, _ = self.imgFood.shape
        self.foodpoint = (0, 0)
        self.randomFoodLocation()

    def randomFoodLocation(self):
        self.foodpoint = random.randint(100, 1100), random.randint(100, 600)

    def update(self, imgMain, currentHead):
        cx, cy = currentHead

        # Game Over Screen
        if self.gameOver:
            cvzone.putTextRect(imgMain, "Game Over", (300, 400), scale=7,
                               thickness=5, colorR=(0, 0, 255), colorT=(255, 255, 255))
            cvzone.putTextRect(imgMain, f"Score: {self.score}", (500, 550), scale=5,
                               thickness=5, colorR=(0, 0, 255), colorT=(255, 255, 255))
            return imgMain

        # Paused state
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

            # Length reduction
            while self.currentLength > self.allowedLength and self.lengths:
                self.currentLength -= self.lengths.pop(0)
                self.points.pop(0)

            # Eat food 
            rx, ry = self.foodpoint
            food_radius = max(self.wFood, self.hFood) // 2 + 15  # extra buffer
            if (rx - food_radius < cx < rx + food_radius and
                ry - food_radius < cy < ry + food_radius):
                self.randomFoodLocation()
                self.allowedLength += 50
                self.score += 1

            if len(self.points) > 30:  
                
                body_parts = np.array(self.points[:-25], np.int32)
                if len(body_parts) > 5:
                    body_parts = body_parts.reshape((-1, 1, 2))
                    dist = cv2.pointPolygonTest(body_parts, (cx, cy), True)
                    # Only game over if head is DEEP inside old body
                    if dist < -18:  # Very negative = clearly overlapping old part
                        print("Real collision - Game Over!")
                        self.gameOver = True

        # Draw Snake
        if self.points:
            for i in range(1, len(self.points)):
                cv2.line(imgMain, tuple(self.points[i-1]), tuple(self.points[i]), (0, 255, 0), 20)
            cv2.circle(imgMain, tuple(self.points[-1]), 20, (0, 200, 0), cv2.FILLED)

        # Draw Food
        rx, ry = self.foodpoint
        imgMain = cvzone.overlayPNG(imgMain, self.imgFood,
                                   (rx - self.wFood // 2, ry - self.hFood // 2))

        
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

# Prevent snake jump when hand disappears
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

    if key == 27:  # ESC key
        break

# === Clean exit ===
cap.release()
cv2.destroyAllWindows()
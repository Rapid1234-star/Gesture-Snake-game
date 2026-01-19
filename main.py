import cvzone
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import math
import random
import time

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
        self.smoothHead = (640.0, 360.0)
        self.smoothingFactor = 0.4  # Smoothness
        self.score = 0
        self.gameOver = False
        self.paused = False
        self.gameStarted = False
        self.countdownActive = False
        self.countdownStart = 0
        self.countdownValue = 5
        self.showInstructions = False

        # velocity tracking
        self.velocity = [0.0, 0.0]
        self.velocitySmoothing = 0.15

        self.imgFood = cv2.imread(pathFood, cv2.IMREAD_UNCHANGED)
        if self.imgFood is None:
            raise FileNotFoundError(f"Image file '{pathFood}' not found.")
        self.hFood, self.wFood, _ = self.imgFood.shape
        self.foodpoint = (0, 0)
        self.randomFoodLocation()

    def randomFoodLocation(self):
        self.foodpoint = random.randint(100, 1100), random.randint(100, 600)

    def startCountdown(self):
        self.countdownActive = True
        self.countdownStart = time.time()
        self.countdownValue = 5

    def drawModernBackground(self, imgMain):
        # Grid pattern 
        for x in range(0, 1280, 40):
            cv2.line(imgMain, (x, 0), (x, 720), (30, 30, 30), 1)
        for y in range(0, 720, 40):
            cv2.line(imgMain, (0, y), (1280, y), (30, 30, 30), 1)
        
        # Border glow effect
        cv2.rectangle(imgMain, (0, 0), (1280, 720), (0, 100, 255), 3)
        cv2.rectangle(imgMain, (3, 3), (1277, 717), (0, 150, 255), 1)

    def drawStartScreen(self, imgMain):
        # Dark overlay
        overlay = imgMain.copy()
        cv2.rectangle(overlay, (0, 0), (1280, 720), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, imgMain, 0.3, 0, imgMain)

        # Title 
        title = "HAND SNAKE"
        for offset in range(5, 0, -1):
            cvzone.putTextRect(imgMain, title, (270 - offset, 200 - offset), 
                             scale=7, thickness=8, 
                             colorR=(0, 50, 100), colorT=(0, 100, 200), offset=20)
        cvzone.putTextRect(imgMain, title, (270, 200), 
                         scale=7, thickness=8, 
                         colorR=(0, 0, 0), colorT=(0, 255, 255), offset=20)

        # Pulsing start button
        pulse = abs(math.sin(time.time() * 3)) * 0.3 + 0.7
        start_color = (int(0 * pulse), int(255 * pulse), int(200 * pulse))
        cvzone.putTextRect(imgMain, "PRESS  [S]  TO START", (320, 400), 
                         scale=4, thickness=6, 
                         colorR=(0, 0, 0), colorT=start_color, offset=15)

        # Warning Message
        warning_y = 520
        cvzone.putTextRect(imgMain, "PRO TIP:", (400, warning_y), 
                         scale=2.5, thickness=3, 
                         colorR=(40, 40, 40), colorT=(255, 200, 0), offset=10)
        cvzone.putTextRect(imgMain, "Keep That Finger Dancing!", (280, warning_y + 60), 
                         scale=2.8, thickness=4, 
                         colorR=(40, 40, 40), colorT=(255, 255, 255), offset=10)
        cvzone.putTextRect(imgMain, "Stop Moving = Game Over!", (300, warning_y + 120), 
                         scale=2.2, thickness=3, 
                         colorR=(40, 40, 40), colorT=(255, 100, 100), offset=10)

        # Instructions button
        cvzone.putTextRect(imgMain, "PRESS  [I]  FOR INSTRUCTIONS", (300, 690), 
                         scale=2, thickness=3, 
                         colorR=(40, 40, 40), colorT=(100, 200, 255), offset=10)

    def drawInstructions(self, imgMain):
        # Dark overlay
        overlay = imgMain.copy()
        cv2.rectangle(overlay, (0, 0), (1280, 720), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.85, imgMain, 0.15, 0, imgMain)

        # Title
        cvzone.putTextRect(imgMain, "HOW TO PLAY", (450, 50), 
                         scale=4.5, thickness=6, 
                         colorR=(0, 0, 0), colorT=(0, 255, 150), offset=15)

        # Instructions text
        instructions = [
            ("HAND REQUIREMENTS:", True),
            ("  • Use Right Hand with Index Finger extended", False),
            ("  • Keep your palm facing the camera", False),
            ("", False),
            ("GAME MECHANICS:", True),
            ("  • Snake follows your INDEX FINGER movement", False),
            ("  • Continuous movement prevents game over", False),
            ("  • Stop moving = INSTANT GAME OVER", False),
            ("", False),
            ("SCORING:", True),
            ("  • Collect donuts (food) to increase score", False),
            ("  • Each donut adds 50 length to the snake", False),
            ("", False),
            ("COLLISIONS:", True),
            ("  • Hitting walls = Game Over", False),
            ("  • Snake hitting itself = Game Over", False),
        ]

        y_pos = 100
        for line, is_header in instructions:
            if line == "":
                y_pos += 10
            elif is_header:
                cvzone.putTextRect(imgMain, line, (40, y_pos), 
                                 scale=1.9, thickness=3, 
                                 colorR=(0, 0, 0), colorT=(255, 200, 0), offset=8)
                y_pos += 35
            else:
                cvzone.putTextRect(imgMain, line, (40, y_pos), 
                                 scale=1.6, thickness=2, 
                                 colorR=(0, 0, 0), colorT=(200, 200, 200), offset=6)
                y_pos += 28

        # Controls section
        cvzone.putTextRect(imgMain, "CONTROLS:", (40, y_pos), 
                         scale=1.9, thickness=3, 
                         colorR=(0, 0, 0), colorT=(255, 200, 0), offset=8)
        y_pos += 35

        controls = [
            "[S] Start Game",
            "[P] Pause/Resume",
            "[R] Restart",
            "[I] Instructions",
            "[ESC] Quit"
        ]

        for ctrl in controls:
            cvzone.putTextRect(imgMain, ctrl, (60, y_pos), 
                             scale=1.6, thickness=2, 
                             colorR=(0, 0, 0), colorT=(0, 255, 200), offset=6)
            y_pos += 28

        # Close instruction prompt
        pulse = abs(math.sin(time.time() * 3)) * 0.3 + 0.7
        close_color = (int(100 * pulse), int(255 * pulse), int(150 * pulse))
        cvzone.putTextRect(imgMain, "PRESS  [I]  TO CLOSE", (420, 690), 
                         scale=2, thickness=3, 
                         colorR=(0, 0, 0), colorT=close_color, offset=10)

    def drawCountdown(self, imgMain):
        elapsed = time.time() - self.countdownStart
        remaining = max(0, self.countdownValue - int(elapsed))

        if remaining > 0:
            # Dark overlay
            overlay = imgMain.copy()
            cv2.rectangle(overlay, (0, 0), (1280, 720), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, imgMain, 0.4, 0, imgMain)

            # Countdown number 
            scale_factor = 1.0 + (0.5 * (1 - (elapsed % 1)))
            size = int(15 * scale_factor)
            thickness = int(15 * scale_factor)
            
            # Color transitions
            colors = [
                (0, 100, 255),  # Blue
                (0, 200, 255),  # Cyan
                (0, 255, 200),  # Green-cyan
                (0, 255, 100),  # Green
                (0, 255, 0)     # Bright green
            ]
            color_idx = min(self.countdownValue - remaining, len(colors) - 1)
            color = colors[color_idx]

            # Glow effect
            for glow in range(8, 0, -2):
                cvzone.putTextRect(imgMain, str(remaining), (580, 300), 
                                 scale=size + glow, thickness=thickness, 
                                 colorR=(0, 0, 0), colorT=(color[0]//2, color[1]//2, color[2]//2), 
                                 offset=30)
            
            cvzone.putTextRect(imgMain, str(remaining), (580, 300), 
                             scale=size, thickness=thickness, 
                             colorR=(0, 0, 0), colorT=color, offset=30)

            cvzone.putTextRect(imgMain, "GET READY!", (450, 500), 
                             scale=3, thickness=4, 
                             colorR=(0, 0, 0), colorT=(255, 255, 255), offset=15)
        else:
            self.countdownActive = False
            self.gameStarted = True

    def update(self, imgMain, currentHead):
        self.drawModernBackground(imgMain)

        if self.showInstructions:
            self.drawInstructions(imgMain)
            return imgMain

        if not self.gameStarted and not self.countdownActive:
            self.drawStartScreen(imgMain)
            return imgMain

        if self.countdownActive:
            self.drawCountdown(imgMain)

            cx, cy = currentHead
            smoothX = self.smoothingFactor * cx + (1 - self.smoothingFactor) * self.smoothHead[0]
            smoothY = self.smoothingFactor * cy + (1 - self.smoothingFactor) * self.smoothHead[1]
            self.smoothHead = (smoothX, smoothY)
            self.previousHead = (round(smoothX), round(smoothY))
            return imgMain

        cx, cy = currentHead

        # smoothing for ultra-smooth movement
        smoothX = self.smoothingFactor * cx + (1 - self.smoothingFactor) * self.smoothHead[0]
        smoothY = self.smoothingFactor * cy + (1 - self.smoothingFactor) * self.smoothHead[1]
        
        # Velocity smoothing 
        targetVelX = smoothX - self.smoothHead[0]
        targetVelY = smoothY - self.smoothHead[1]
        self.velocity[0] = self.velocitySmoothing * targetVelX + (1 - self.velocitySmoothing) * self.velocity[0]
        self.velocity[1] = self.velocitySmoothing * targetVelY + (1 - self.velocitySmoothing) * self.velocity[1]
        
        smoothX = self.smoothHead[0] + self.velocity[0]
        smoothY = self.smoothHead[1] + self.velocity[1]
        
        self.smoothHead = (smoothX, smoothY)
        cx = round(smoothX)
        cy = round(smoothY)

        if self.gameOver:
            # game over screen with dark overlay
            overlay = imgMain.copy()
            cv2.rectangle(overlay, (0, 0), (1280, 720), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.85, imgMain, 0.15, 0, imgMain)

            # Game over title with glow effect
            for glow in range(6, 0, -2):
                cvzone.putTextRect(imgMain, "GAME OVER", (280 - glow // 2, 150 - glow // 2), scale=8,
                                 thickness=10, colorR=(0, 0, 0), colorT=(100, 20, 20), offset=25)
            
            cvzone.putTextRect(imgMain, "GAME OVER", (280, 150), scale=8,
                             thickness=10, colorR=(0, 0, 0), colorT=(255, 50, 50), offset=25)
            
            # Decorative line
            cv2.line(imgMain, (200, 210), (1080, 210), (255, 100, 100), 2)

            # Final score label
            cvzone.putTextRect(imgMain, "FINAL SCORE", (420, 290), scale=3.5,
                             thickness=4, colorR=(0, 0, 0), colorT=(255, 200, 0), offset=15)
            
            # Score display with glow
            score_text = f"{self.score}"
            for glow in range(4, 0, -1):
                cvzone.putTextRect(imgMain, score_text, (500 - glow // 2, 400 - glow // 2), scale=7,
                                 thickness=8, colorR=(0, 0, 0), colorT=(0, 100, 100), offset=20)
            
            cvzone.putTextRect(imgMain, score_text, (500, 400), scale=7,
                             thickness=8, colorR=(0, 0, 0), colorT=(0, 255, 200), offset=20)

            # Decorative line
            cv2.line(imgMain, (200, 470), (1080, 470), (0, 255, 200), 2)

            # Restart prompt with pulsing effect
            pulse = abs(math.sin(time.time() * 3)) * 0.4 + 0.6
            restart_color = (int(100 * pulse), int(255 * pulse), int(150 * pulse))
            cvzone.putTextRect(imgMain, "PRESS  [R]  TO RESTART", (350, 580), scale=3,
                             thickness=4, colorR=(0, 0, 0), colorT=restart_color, offset=15)
            
            # Instructions hint
            cvzone.putTextRect(imgMain, "PRESS  [I]  FOR INSTRUCTIONS", (330, 650), scale=2,
                             thickness=3, colorR=(0, 0, 0), colorT=(100, 200, 255), offset=10)
            
            return imgMain

        if self.paused:
            overlay = imgMain.copy()
            cv2.rectangle(overlay, (0, 0), (1280, 720), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, imgMain, 0.4, 0, imgMain)
            
            cvzone.putTextRect(imgMain, "PAUSED", (450, 280), scale=8,
                             thickness=10, colorR=(0, 0, 0), colorT=(100, 100, 255), offset=25)
            cvzone.putTextRect(imgMain, "PRESS  [P]  TO RESUME", (350, 420),
                             scale=3, thickness=4, colorR=(0, 0, 0), colorT=(200, 200, 255), offset=15)
            self.previousHead = (cx, cy)
        else:
            px, py = self.previousHead
            self.points.append([cx, cy])
            distance = math.hypot(cx - px, cy - py)
            self.lengths.append(distance)
            self.currentLength += distance
            self.previousHead = (cx, cy)

            # Trim tail
            while self.currentLength > self.allowedLength and self.lengths:
                self.currentLength -= self.lengths.pop(0)
                self.points.pop(0)

            # Wall collision 
            if cx < 35 or cx > 1245 or cy < 35 or cy > 685:
                print("💥 Hit the wall! Game Over!")
                self.gameOver = True

            # Food collision
            if not self.gameOver:
                rx, ry = self.foodpoint
                food_radius = max(self.wFood, self.hFood) // 2 + 20
                if (rx - food_radius < cx < rx + food_radius and
                    ry - food_radius < cy < ry + food_radius):
                    self.randomFoodLocation()
                    self.allowedLength += 50
                    self.score += 1
                    print(f"🍩 Yum! Score: {self.score}")

            # self-collision detection
            if not self.gameOver and len(self.points) > 20:
                head_np = np.array([cx, cy])
                COLLISION_DIST = 25  
                SKIP_RECENT = 15  
                num_points_to_check = len(self.points) - SKIP_RECENT
                if num_points_to_check > 0:
                    for i in range(num_points_to_check):
                        body_np = np.array(self.points[i])
                        if np.linalg.norm(head_np - body_np) < COLLISION_DIST:
                            print("🔁 Self-collision! Game Over!")
                            self.gameOver = True
                            break

        #  snake rendering
        if self.points:
            total = len(self.points)
            
            # snake body 
            for i in range(1, total):
                p1 = tuple(self.points[i-1])
                p2 = tuple(self.points[i])
                t = i / float(total)
                
                # Gradient thickness and color
                thickness = int(10 + 20 * t)
                color = (0, int(80 + 175 * t), int(20 * t))
                
                # Glow effect
                cv2.line(imgMain, p1, p2, (0, int(60 * t), 0), thickness + 4)
                cv2.line(imgMain, p1, p2, color, thickness)

            # snake head
            head = tuple(self.points[-1])
            if total >= 2:
                hx, hy = self.points[-1]
                tx, ty = self.points[-2]
                dx, dy = hx - tx, hy - ty
                mag = math.hypot(dx, dy) or 1.0
                ux, uy = dx / mag, dy / mag
            else:
                ux, uy = 1.0, 0.0

            px_snake, py_snake = -uy, ux

            head_center = (int(head[0]), int(head[1]))
            major, minor = 36, 28
            angle = math.degrees(math.atan2(uy, ux))
            
            # Head glow
            cv2.ellipse(imgMain, head_center, (major // 2 + 4, minor // 2 + 4), 
                       angle, 0, 360, (0, 100, 0), cv2.FILLED)
            # Head main
            cv2.ellipse(imgMain, head_center, (major // 2, minor // 2), 
                       angle, 0, 360, (0, 220, 0), cv2.FILLED)
            # Head outline
            cv2.ellipse(imgMain, head_center, (major // 2, minor // 2), 
                       angle, 0, 360, (0, 150, 0), 3)

            # Snake eyes
            eye_offset = 11
            forward_offset = 5
            ex1 = int(head_center[0] + px_snake * eye_offset + ux * forward_offset)
            ey1 = int(head_center[1] + py_snake * eye_offset + uy * forward_offset)
            ex2 = int(head_center[0] - px_snake * eye_offset + ux * forward_offset)
            ey2 = int(head_center[1] - py_snake * eye_offset + uy * forward_offset)
            
            
            cv2.circle(imgMain, (ex1, ey1), 7, (255, 255, 255), cv2.FILLED)
            cv2.circle(imgMain, (ex2, ey2), 7, (255, 255, 255), cv2.FILLED)
            
            cv2.circle(imgMain, (ex1, ey1), 7, (0, 100, 0), 1)
            cv2.circle(imgMain, (ex2, ey2), 7, (0, 100, 0), 1)
            
            pupil_forward = 3
            cv2.circle(imgMain, (int(ex1 + ux * pupil_forward), int(ey1 + uy * pupil_forward)), 
                      4, (0, 0, 0), cv2.FILLED)
            cv2.circle(imgMain, (int(ex2 + ux * pupil_forward), int(ey2 + uy * pupil_forward)), 
                      4, (0, 0, 0), cv2.FILLED)

            # tongue
            mouth_x = int(head_center[0] + ux * (major // 2))
            mouth_y = int(head_center[1] + uy * (major // 2))
            tip_len = 16
            fork = 7
            tip = (int(mouth_x + ux * tip_len), int(mouth_y + uy * tip_len))
            left_tip = (int(mouth_x + ux * (tip_len - 6) + px_snake * fork), 
                       int(mouth_y + uy * (tip_len - 6) + py_snake * fork))
            right_tip = (int(mouth_x + ux * (tip_len - 6) - px_snake * fork), 
                        int(mouth_y + uy * (tip_len - 6) - py_snake * fork))
            
            cv2.line(imgMain, (mouth_x, mouth_y), tip, (50, 50, 255), 3)
            cv2.line(imgMain, tip, left_tip, (50, 50, 255), 3)
            cv2.line(imgMain, tip, right_tip, (50, 50, 255), 3)

        # Food with glow
        rx, ry = self.foodpoint
        # Food glow effect
        glow_size = int(5 + 3 * abs(math.sin(time.time() * 3)))
        cv2.circle(imgMain, (rx, ry), self.wFood // 2 + glow_size, (100, 200, 255), 2)
        imgMain = cvzone.overlayPNG(imgMain, self.imgFood,
                                   (rx - self.wFood // 2, ry - self.hFood // 2))

        #  UI panel
        # Score display
        cvzone.putTextRect(imgMain, f"SCORE: {self.score}", (40, 60), scale=3.5,
                         thickness=5, colorR=(0, 0, 0), colorT=(0, 255, 200), offset=15)
        
        # Controls
        cvzone.putTextRect(imgMain, "[P] PAUSE  |  [R] RESTART", (40, 130),
                         scale=2, thickness=3, colorR=(20, 20, 20), colorT=(200, 200, 200), offset=10)

        # Movement message reminder
        pulse = abs(math.sin(time.time() * 2)) * 0.4 + 0.6
        reminder_color = (int(255 * pulse), int(200 * pulse), int(100 * pulse))
        cvzone.putTextRect(imgMain, "KEEP MOVING!", (1000, 60),
                         scale=2, thickness=3, colorR=(20, 20, 20), colorT=reminder_color, offset=10)

        return imgMain

    def reset(self):
        self.points = []
        self.lengths = []
        self.currentLength = 0
        self.allowedLength = 150
        self.previousHead = (640, 360)
        self.smoothHead = (640.0, 360.0)
        self.velocity = [0.0, 0.0]
        self.score = 0
        self.gameOver = False
        self.paused = False
        self.gameStarted = False
        self.countdownActive = False
        self.randomFoodLocation()

game = SnakeGameClass("Snake_game/donuta.png")

lastHead = (640, 360)

print("🎮 Hand Snake Game Started!")
print("📌 Controls:")
print("   [S] - Start Game")
print("   [P] - Pause/Resume")
print("   [R] - Restart")
print("   [I] - Instructions")
print("   [ESC] - Quit")

while True:
    success, img = cap.read()
    if not success:
        break
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    if hands:
        lmList = hands[0]['lmList']
        pointindex = lmList[8][0:2]
        currentHead = tuple(pointindex)
        lastHead = currentHead
    else:
        currentHead = lastHead

    img = game.update(img, currentHead)

    cv2.imshow("Hand Snake Game", img)
    key = cv2.waitKey(1)

    # Start game
    if key == ord('s') or key == ord('S'):
        if not game.gameStarted and not game.countdownActive and not game.gameOver and not game.showInstructions:
            game.startCountdown()

    # Pause/Resume
    if key == ord('p') or key == ord('P'):
        if game.gameStarted and not game.gameOver and not game.showInstructions:
            game.paused = not game.paused

    # Restart
    if key == ord('r') or key == ord('R'):
        game.reset()

    # Instructions
    if key == ord('i') or key == ord('I'):
        game.showInstructions = not game.showInstructions

    # Quit
    if key == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
print("👋 Thanks for playing!")
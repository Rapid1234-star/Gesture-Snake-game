import cvzone
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector 
import math
import random

cap=cv2.VideoCapture(0)
cap.set(3,1280)
cap.set(4,720)

detector= HandDetector(detectionCon=0.8,maxHands=1)

class SnakeGameClass:
    def __init__(self,pathFood):
        self.points= []
        self.lengths= []
        self.currentLength=0
        self.allowedLength=150
        self.previousHead=0,0
        self.score=0 
        self.gameOver=False

        self.imgFood= cv2.imread(pathFood,cv2.IMREAD_UNCHANGED)
        if self.imgFood is None:
            raise FileNotFoundError(f"Image file '{pathFood}' not found. Ensure the file exists in the script's directory.")
        self.hFood, self.wFood, _ = self.imgFood.shape
        self.foodpoint=0,0
        self.ramdomFoodLocation()

    def ramdomFoodLocation(self):
        self.foodpoint=random.randint(100,1000),random.randint(100,600)

    def update(self,imgMain,currentHead):

        if self.gameOver:
            cvzone.putTextRect(imgMain,"Game Over",(300,400),scale=7,
                               thickness=5,colorR=(0,0,255),colorT=(255,255,255))
            
            cvzone.putTextRect(imgMain,f"Score: {self.score}",(500,550),scale=5,
                               thickness=5,colorR=(0,0,255),colorT=(255,255,255))
            


        else:
            px,py= self.previousHead
            cx,cy= currentHead

            self.points.append([cx,cy])
            distance=math.hypot(cx-px,cy-py)
            self.lengths.append(distance)
            self.currentLength += distance
            self.previousHead= cx,cy

            #Length Reduction
            if self.currentLength > self.allowedLength:
                for i,length in enumerate(self.lengths):
                    self.currentLength -= length
                    self.lengths.pop(i)
                    self.points.pop(i)
                    if self.currentLength < self.allowedLength:
                        break

            #Check if snake ate the food
            rx,ry= self.foodpoint
            if rx-self.wFood//2 <cx< rx + self.wFood//2 and ry-self.hFood//2<cy< ry + self.hFood//2:
                self.ramdomFoodLocation()
                self.allowedLength +=50
                self.score +=1


            #Draw Snake 
            if self.points:
                for i,point in enumerate(self.points):
                    if i !=0:
                        cv2.line(imgMain,self.points[i-1],self.points[i],(0,255,0),20)  # Changed to green for body
                cv2.circle(imgMain,self.points[-1],20,(0,200,0),cv2.FILLED)  # Changed to darker green for head

            #Draw Food
            imgMain=cvzone.overlayPNG(imgMain,self.imgFood,(rx-self.wFood//2,ry-self.hFood//2))

            cvzone.putTextRect(imgMain,f"Score: {self.score}",(50,80),scale=3,
                            thickness=3,colorR=(0,0,0),colorT=(255,255,255))

            #Check for collision with itself
            pts= np.array(self.points[:-2],np.int32)
            pts= pts.reshape((-1,1,2))
            cv2.polylines(imgMain,[pts],False,(0,0,255),3)
            minDist=cv2.pointPolygonTest(pts,(cx,cy),True)

            if -1<= minDist <=1:
                print("Game Over")
                self.gameOver=True
                self.points= []
                self.lengths= []
                self.currentLength=0
                self.allowedLength=150
                self.previousHead=0,0
                self.ramdomFoodLocation()

        return imgMain


game= SnakeGameClass("Snake_game/donuta.png")

while True:
    success, img= cap.read()
    img=cv2.flip(img,1)
    hands,img =detector.findHands(img,flipType=False)

    if hands:
        lmList= hands[0]['lmList']
        pointindex= lmList[8][0:2]
        img= game.update(img,pointindex)

    cv2.imshow("Image",img)
    key=cv2.waitKey(1)

    if key==ord('r'):
        game.gameOver=False 
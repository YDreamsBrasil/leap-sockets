#! /usr/bin/env python
"""
Read the docs:
    https://developer.leapmotion.com/documentation/python/index.html




"""

from __future__ import print_function
import sys, os, string
import socket

sys.path.insert(0, "lib")
import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
from time import sleep


HOST = 'localhost'
PORT = 3000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

leapResult = { 'posX': 0, 'posY': 0, 'posType': 'NE', 'default': 0 }
global leapMotion
global conn


class YLeap(Leap.Listener):
    global leapResult
    """
        Leap Motion class to provide coordinates on the format
        of "X, Y, NE, 0" in order to allow legacy YDreams Programs
        to work with the Leap hardware.
    """
    def __init__(self):
        super(YLeap, self).__init__()
        self.controller  = Leap.Controller()
        self.controller.add_listener(self)
        self.controller.set_policy(Leap.Controller.POLICY_BACKGROUND_FRAMES)
        self.controller.set_policy(Leap.Controller.POLICY_IMAGES)
        self.controller.set_policy(Leap.Controller.POLICY_OPTIMIZE_HMD)


    def on_connect(self, controller):
        print("Leap Motion Connected")
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE)
        controller.config.set("Gesture.Swipe.MinLength", 100.0)
        controller.config.set("Gesture.Swipe.MinVelocity", 750)
        controller.config.save()

    def on_disconnect(self, controller):
        print("Leap Motion Disconnected")


    def on_frame(self, controller):
        """
            The return:
            position: x, y, z coordinates milimeters
            velocity: x, y, z milimeters per second
            direction: x, y, z vector pointing from the center of the palm toward the fingers
        """
        frame = controller.frame()
        hand = frame.hands[0]
        position = hand.palm_position
        velocity = hand.palm_velocity
        direction = hand.direction
 
        pixelX = int(position[0] * 72 / 25.2)
        pixelY = int(position[1] * 72 / 25.2)
        leapResult['posX'] = pixelX
        leapResult['posY'] = pixelY

        tmp = string.Template('$x,$y,$t,0')
        posType = "NE"


        # Here we check if there were any 
        # gestures present in the current frame
        # and if yes, we insert it on the response.
        if not frame.gestures().is_empty:
             for gesture  in frame.gestures():
                if gesture.type is Leap.Gesture.TYPE_SWIPE:
                    swipe = Leap.SwipeGesture(gesture)
                    swipe_direction = swipe.direction
                    if leapResult['posX'] != 0 and leapResult['posY'] != 0:

                        leapResult['posType'] = "FR" if swipe_direction[0] > 0 else "FL"
                        print(tmp.substitute(x= leapResult['posX'], y= leapResult['posY'], t=leapResult['posType']))
                        conn.send(tmp.substitute(x= leapResult['posX'], y= leapResult['posY'], t=leapResult['posType']))
                        leapResult['posType'] = "NE"
 

        else:
            leapResult['posType'] = "NE"


        # Printing or sending the result 
        print(tmp.substitute(x= leapResult['posX'], y= leapResult['posY'], t=leapResult['posType']))
        if leapResult['posX'] != 0: 
            conn.send(tmp.substitute(x= leapResult['posX'], y= leapResult['posY'], t=leapResult['posType']))

if __name__ == "__main__":
    sock.bind((HOST, PORT))
    sock.listen(20)
    conn, addr = sock.accept()
    leapMotion = YLeap()

while True:
    data, addr = conn.recvfrom(1024)
    print(data.strip(), addr)

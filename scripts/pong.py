#!/usr/bin/env python

import sys
import random
import time
import numpy as np
import xbox
import BlinkyTape as bt


# COLORS
class Col(object):
    BLACK = (0, 0, 0)
    CYAN = (0, 189, 189)
    GREEN = (0, 255, 0)
    ORANGE = (255, 80, 0)
    RED = (255, 0, 0)
    WHITE = (255, 255, 255)
    YELLOW = (255, 200, 0)
    LIGHT_GREEN = (0, 127, 0)
    PURPLE = (255, 0, 255)


class Pong(object):
    def __init__(self,
                 length=25,
                 width=7,
                 pad_rad=1,
                 rate=0.1):

        self.port = '/dev/ttyACM1'

        self.length = length
        self.width = width
        self.pad_rad = pad_rad
        self.frame = [Col.BLACK for _ in range(self.length * self.width)]

        # Player Attributes
        self.pos1 = self.width // 2
        self.pts1 = 0
        self.pos2 = self.width // 2
        self.pts2 = 0

        # Ball Attributes
        self.rate = rate
        self.posb = np.zeros((2))
        self.posb = [(self.length // 2), (self.width // 2)]
        self.velb = np.zeros((2))

        self.reaction_time = 5 * self.rate
        self.last_calc = time.time()
        self.last_move = time.time()
        self.blt = bt.BlinkyTape(self.port,
                                 (self.length * self.width),
                                 buffered=False)

    def flatten(self, mat):
        if type(mat) is not np.ndarray:
            print('Passed invalid argument type: {}'.format(type(mat)))
        elif mat.shape != (self.width, self.length):
            print('Passed a matrix of invalid size \n' +
                  '\tExpected: {} * {}'.format(self.length, self.width) +
                  '\tReceived: {} * {}'.format(mat.shape[0], mat.shape[1]))

        colours = []

        for i in range(self.width):
            if (i % 2) == 0:
                for j in range(self.length):
                    colours.append(mat[i][j])
            else:
                for j in range(self.length):
                    colours.append(mat[i][(self.length - 1) - j])

        return colours

    def colorize_mask(self, mask, col):
        colours = self.frame
        maskf = self.flatten(mask)

        for i in range(len(maskf)):
            if maskf[i] == 1:
                colours[i] = col

        return colours

    def drop_ball(self, x_mod, y_mod):
        self.posb = [(self.width // 2), (self.length // 2)]
        score_fac = 0.25 * (self.pts1 + self.pts2)

        # Reroll if too low...
        self.velb[0] = random.uniform(-1, 1) * y_mod + score_fac  # y
        if abs(self.velb[0] < 0.3):
            self.velb[0] = random.uniform(-1, 1) * y_mod + score_fac  # y

        self.velb[1] = random.uniform(0.5, 1) * x_mod + score_fac  # x

        if (self.pts1 >= 7) or (self.pts2 >= 7):
            self.draw_frame()
            time.sleep(1)
            self.winbow()

    def handle_input(self):
        if self.joy.Start():
            self.reset()

        if self.joy.Back():
            self.winbow()

        if self.joy.dpadDown() or self.joy.dpadRight():
            if int(round(self.pos1)) < (self.width - self.pad_rad - 1):
                self.pos1 += 1

        if self.joy.dpadUp() or self.joy.dpadLeft():
            if int(round(self.pos1)) >= (self.pad_rad + self.pad_rad):
                self.pos1 -= 1

        if (time.time() - self.last_move) < self.reaction_time:
            return

        if (self.posb[0] > 3.5):
            if int(round(self.pos2)) < (self.width - self.pad_rad - 1):
                    self.pos2 += 1
        else:
            if int(round(self.pos2)) >= (self.pad_rad + self.pad_rad):
                    self.pos2 -= 1

        self.last_move = time.time()

    def calc_traj(self):
        if (time.time() - self.last_calc) <= self.rate:
            return

        self.posb[0] += self.velb[0]
        self.posb[1] += self.velb[1]

        # Top Border Check
        if self.posb[0] < 0:
            self.posb[0] = 1
            self.velb[0] *= -1

        # Bottom Border Check
        if self.posb[0] > self.width - 1:
            self.posb[0] = self.width - 2
            self.velb[0] *= -1

        # Red (p1) Paddle Check
        if self.posb[1] <= 1:
            if (((int(round(self.posb[0])) == self.pos1) or
                 (int(round(self.posb[0])) == (self.pos1 - self.pad_rad)) or
                 ((int(round(self.posb[0]))) == (self.pos1 + self.pad_rad)))):
                self.posb[1] = 2
                self.velb[1] *= -1

        # Blue (p2) Paddle Check
        if self.posb[1] >= self.length - 2:
            if (((int(round(self.posb[0])) == self.pos2) or
                 (int(round(self.posb[0])) == (self.pos2 - self.pad_rad)) or
                 (int(round(self.posb[0])) == (self.pos2 + self.pad_rad)))):
                self.posb[1] = self.length - 3
                self.velb[1] *= -1

        # Blue (p2) Point Check
        if self.posb[1] <= 1:
            self.pts2 += 1
            self.drop_ball(1, 1)

        # Red (p1) Point Check
        if self.posb[1] >= self.length - 1:
            self.pts1 += 1
            self.drop_ball(-1, 1)

        self.last_calc = time.time()

    def draw_frame(self):
        self.frame = [Col.BLACK for _ in range(self.length * self.width)]

        # # Draw Red (p1) Paddle
        mask = np.zeros((self.width, self.length))
        y_min = (self.pos1 - self.pad_rad)
        y_max = (self.pos1 + self.pad_rad) + 1
        for i in range(y_min, y_max):
            mask[i][1] = 1
        self.frame = self.colorize_mask(mask, Col.RED)

        # # Draw Blue (p2) Paddle
        mask = np.zeros((self.width, self.length))
        y_min = (self.pos2 - self.pad_rad)
        y_max = (self.pos2 + self.pad_rad) + 1
        for i in range(y_min, y_max):
            mask[i][self.length - 2] = 1
        self.frame = self.colorize_mask(mask, Col.CYAN)

        # Draw Ball
        mask = np.zeros((self.width, self.length))
        mask[int(round(self.posb[0]))][int(round(self.posb[1]))] = 1
        self.frame = self.colorize_mask(mask, Col.GREEN)

        # # Draw Red (p1) Score
        mask = np.zeros((self.width, self.length))
        for i in range(self.pts1):
            mask[i][0] = 1
        self.frame = self.colorize_mask(mask, Col.YELLOW)

        # # Draw Blue (p2) Score
        mask = np.zeros((self.width, self.length))
        for i in range(self.pts2):
            mask[i][self.length - 1] = 1
        self.frame = self.colorize_mask(mask, Col.YELLOW)

        for i in range(len(self.frame)):
            self.blt.sendPixel(*self.frame[i])
        self.blt.show()

    def initialize(self):
        self.joy = xbox.Joystick()

        self.drop_ball(1.0, 1.0)
        self.draw_frame()
        time.sleep(0.75)

    def reset(self):
        self.frame = [Col.BLACK for _ in range(self.length * self.width)]

        # Player Attributes
        self.pos1 = self.width // 2
        self.pts1 = 0
        self.pos2 = self.width // 2
        self.pts2 = 0

        self.drop_ball(1, 1)

    def winbow(self):
        winbow_rate = 0.5
        for _ in range(3):

            hues = [Col.BLACK,
                    Col.RED,
                    Col.ORANGE,
                    Col.YELLOW,
                    Col.GREEN,
                    Col.CYAN,
                    Col.PURPLE]

        while True:
            if self.joy.Back():
                sys.exit(0)

            for hue in hues:
                self.frame = [hue for _ in range(self.length * self.width)]
                for i in range(len(self.frame)):
                    self.blt.sendPixel(*self.frame[i])
                self.blt.show()

                esc = self.joy.Start()
                if esc:
                    break
                time.sleep(winbow_rate)

            if esc:
                break

        self.reset()


if __name__ == "__main__":
    pong = Pong()
    pong.initialize()

    while True:
        pong.calc_traj()
        pong.handle_input()
        pong.draw_frame()
        time.sleep(0.1)

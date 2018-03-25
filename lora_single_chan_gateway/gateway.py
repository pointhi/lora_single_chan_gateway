#!/usr/bin/env python3

import logging

from board_config import LoraBoardDraguino
from rf95 import RF95
import RPi.GPIO as GPIO


logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    #with LoraBoardDraguino(433300000, 7) as board:
    with RF95() as board:
        #logging.info("Listening at SF{} on {} MHz".format(board.sf, board.frequency/1000000))

        while True:
            if GPIO.input(board._pin_dio0) == 1:
                payload = board.receive_package()
                logging.info("Received: {}".format(payload))
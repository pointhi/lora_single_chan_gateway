#!/usr/bin/env python3

import logging

from board_config import LoraBoardDraguino
import RPi.GPIO as GPIO


if __name__ == "__main__":
    with LoraBoardDraguino(433300000, 7) as board:
        logging.info("Listening at SF{} on {} MHz".format(board.sf, board.frequency/1000000))

        while True:
            if GPIO.input(board._pin_dio0) == 1:
                payload = board.receive_package()
                logging.info("Received: {}".format(payload))
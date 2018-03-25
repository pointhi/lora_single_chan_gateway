#!/usr/bin/env python3

import base64
import logging

from board_config import LoraBoardDraguino
import RPi.GPIO as GPIO


logging.basicConfig(level=logging.DEBUG)


def construct_semtec_udp(board, payload):
    return {
        "rxpk":
            {
                "time": payload['datetime'].isoformat(),
                "freq": board.frequency / 1000 / 1000,
                "stat": 1 if payload['crc'] is True else -1,
                "modu": "LORA",
                "datr": "SF7BW125",  # TODO: configurable
                "codr": "4/5",
                "rssi": payload['pkt_rssi'],
                "lsnr": payload['pkt_ssr'],
                "size": len(payload['payload']),
                "data": base64.standard_b64encode(payload['payload'])
            }
    }



if __name__ == "__main__":
    with LoraBoardDraguino(433300000, 7) as board:
        logging.info("Listening at SF{} on {} MHz".format(board.sf, board.frequency/1000000))

        while True:
            if GPIO.input(board._pin_dio0) == 1:
                payload = board.receive_package()
                logging.info(construct_semtec_udp(board, payload))
                #logging.info("Received: {}".format(payload))
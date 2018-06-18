#!/usr/bin/env python3

import base64
import json
import logging
from random import randint
import socket
import sqlite3

from board_config import LoraBoardDraguino
import RPi.GPIO as GPIO


logging.basicConfig(level=logging.DEBUG)


GATEWAY_HOST = "router.eu.thethings.network"
GATEWAY_PORT = 1700


class LoRaPacketsDB(object):
    def __init__(self):
        self.conn = sqlite3.connect('gateway_packages.db')  # we only need the db at runtime
        self.c = self.conn.cursor()

        self._init_db()

    def _init_db(self):
        create_table = """CREATE TABLE IF NOT EXISTS `PACKETS` (
            `ID` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            `DATETIME` TEXT NOT NULL,
            `DATA` BLOB,
            `FREQUENCY` NUMERIC,
            `IS_CRC_OK` INTEGER,
            `PKT_SNR` NUMERIC,
            `PKT_RSSI` NUMERIC,
            `RSSI` NUMERIC
        )"""
        self.conn.execute(create_table)

    def log_pkg(self, board, packet):
        query = """INSERT INTO `PACKETS` (
            `DATETIME`,
            `DATA`,
            `FREQUENCY`,
            `IS_CRC_OK`,
            `PKT_SNR`,
            `PKT_RSSI`,
            `RSSI`
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            self.c.execute(query, (payload['datetime'].isoformat(),
                                   payload.get('payload'),
                                   board.frequency,
                                   payload.get('crc'),
                                   payload.get('pkt_snr'),
                                   payload.get('pkt_rssi'),
                                   payload.get('rssi')))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            logging.exception("SQL ERROR: ", e)


def construct_semtec_udp(board, payload):
    # https://github.com/Lora-net/packet_forwarder/blob/d0226eae6e7b6bbaec6117d0d2372bf17819c438/PROTOCOL.TXT#L99
    frame = bytearray()
    frame.append(2)  # Protocol version = 2
    frame.extend([randint(0, 255), randint(0, 255)])  # Random numbers
    frame.extend([0x80, 0xFA, 0x5C, 0xFF, 0xFF, 0x69, 0x33, 0xBB])  # TODO: construct from hardware

    data = {
        "rxpk":
            {
                "time": payload['datetime'].isoformat(),
                "freq": board.frequency / 1000 / 1000,
                "stat": 1 if payload['crc'] is True else -1,
                "modu": "LORA",
                "datr": "SF7BW125",  # TODO: configurable
                "codr": "4/5",
                "rssi": payload['pkt_rssi'],
                "lsnr": payload['pkt_snr'],
                "size": len(payload['payload']),
                "data": base64.standard_b64encode(payload['payload']).decode("utf-8")
            }
    }

    frame.extend(map(ord, json.dumps(data)))

    return bytes(frame)


if __name__ == "__main__":
    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    db = LoRaPacketsDB()

    with LoraBoardDraguino(433300000, 7) as board:
        board.set_mode_rx()
        logging.info("Listening at SF{} on {} MHz".format(board.sf, board.frequency/1000000))

        while True:
            if GPIO.input(board._pin_dio0) == 1:
                payload = board.receive_package()

                # semtec_udp = construct_semtec_udp(board, payload)
                # sock.sendto(semtec_udp, (GATEWAY_HOST, GATEWAY_PORT))
                # logging.info(semtec_udp)

                # logging.info("Received: {}".format(payload))
                logging.info("Received at {}: {} = {}".format(payload['datetime'].isoformat(), payload['payload'].hex(), payload['payload'][4:]))

                db.log_pkg(board, payload)

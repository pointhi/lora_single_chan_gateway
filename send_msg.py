#!/usr/bin/env python3

import argparse
import logging

from lora_single_chan_gateway.board_config import LoraBoardDraguino


logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('message', type=str, help='message to send')

    # http://www.airspayce.com/mikem/arduino/RadioHead/classRH__RF95.html "packet format"
    parser.add_argument('--from', type=int, default=0xFF)
    parser.add_argument('--to', type=int, default=0xFF)
    parser.add_argument('--id', type=int, default=0x00)
    parser.add_argument('--flags', type=int, default=0x00)

    args = parser.parse_args()

    GATEWAY_HEADER = bytes([args.to, args.__dict__['from'], args.id, args.flags])

    with LoraBoardDraguino(433300000, 7) as board:
        msg = GATEWAY_HEADER + args.message.encode('utf-8')
        print(msg)

        board.send_package(msg)
#!/usr/bin/env python3

from decode_msg import decode_msg, pretty_print_header, pretty_print_payload, MSG_TYPES

import sqlite3

if __name__ == "__main__":
    conn = sqlite3.connect('gateway_packages.db')
    c = conn.cursor()

    c.execute('SELECT * FROM `PACKETS`')

    for line in c.fetchall():
        try:
            line = list(line)

            msg = {'id': line[0],
                   'datetime': line[1],
                   'data': bytes(line[2]).hex(),
                   'crc': line[3],
                   'pkt_snr': line[4],
                   'pkt_rssi': line[4],
                   'rssi': line[4]}

            decoded = decode_msg(msg['data'])

            color = '\033[92m' if msg['crc'] else '\033[91m'

            print(color, '### {id:04d} ({datetime}): {header}\033[0m (PKT_SNR={pkt_snr}, PKT_RSSI={pkt_rssi}, RSSI={rssi}) '.format(**msg, header=pretty_print_header(decoded)))

            # weather report
            if decoded['type'] == 0x10:
                print(pretty_print_payload(decoded))
        except:
            print("ERROR in: ", line)

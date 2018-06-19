#!/usr/bin/env python3

import dateutil.parser
import sqlite3

import matplotlib.dates
import matplotlib.pyplot
import matplotlib.pyplot as plt

from decode_msg import decode_msg


if __name__ == "__main__":
    conn = sqlite3.connect('gateway_packages.db')
    c = conn.cursor()

    c.execute('SELECT * FROM `PACKETS`')

    dates = []
    values_temp = []
    values_press = []
    values_bat_val = []
    values_cell_val = []

    for line in c.fetchall():
        try:
            line = list(line)

            msg = {'id': line[0],
                   'datetime': line[1],
                   'data': bytes(line[2]).hex(),
                   'frequency': line[3],
                   'crc': line[4],
                   'pkt_snr': line[5],
                   'pkt_rssi': line[6],
                   'rssi': line[7]}

            if not msg['crc']:
                continue

            decoded = decode_msg(msg['data'])

            # weather report
            if decoded['type'] == 0x10:
                datetime = dateutil.parser.parse(msg['datetime'])
                temperatur = None
                pressure = None
                battery_voltage = None
                solar_voltage = None
                for val in decoded['values']:
                    if val['id'] == 0x20:
                        temperatur = val['val']
                    elif val['id'] == 0x22:
                        pressure = val['val']
                    elif val['id'] == 0x80:
                        battery_voltage = val['val']
                    elif val['id'] == 0x90:
                        solar_voltage = val['val']

                dates.append(datetime)
                values_temp.append(temperatur)
                values_press.append(pressure)
                values_bat_val.append(battery_voltage)
                values_cell_val.append(solar_voltage)
        except:
            print("ERROR in: ", line)
    print('plot!')

    fig, ax1 = plt.subplots()

    ax1.set_xlabel('time')
    ax1.set_ylabel('voltage')

    ax1.plot_date(dates, values_bat_val, linestyle='solid', marker='None', label='Battery Voltage')
    ax1.plot_date(dates, values_cell_val, linestyle='solid', marker='None', label='Solar Cell Voltage')
    ax1.plot_date(dates, values_press, linestyle='solid', marker='None', label='Temperatur')
    plt.legend()
    matplotlib.pyplot.show()

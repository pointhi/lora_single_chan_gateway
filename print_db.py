#!/usr/bin/env python3

import sqlite3

if __name__ == "__main__":
    conn = sqlite3.connect('gateway_packages.db')
    c = conn.cursor()

    c.execute('SELECT * FROM `PACKETS`')

    for line in c.fetchall():
        line = list(line)
        line[2] = bytes(line[2]).hex()
        print(line)

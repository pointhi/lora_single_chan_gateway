#!/usr/bin/env python

import sqlite3

if __name__ == "__main__":
    conn = sqlite3.connect('gateway_packages.db')
    c = conn.cursor()

    c.execute('SELECT * FROM `PACKETS`')

    for line in c.fetchall():
        print(line)

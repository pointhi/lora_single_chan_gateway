#!/usr/bin/env python3

import struct

MSG_TYPES = {0x01: 'PING',
             0x02: 'PONG',
             0x10: 'Weather Report',
             0x11: 'Weather Report Request'}

PAYLOAD_TYPES = {0x20: 'Outside Temperature',
                 0x21: 'Outside Humidity',
                 0x22: 'Outside Pressure',
                 0x50: 'Inside Temperature',
                 0x51: 'Inside Humidity',
                 0x52: 'Inside Pressure',
                 0x80: 'Battery Voltage',
                 0x81: 'Battery Current',
                 0x90: 'Solar Cell Voltage',
                 0x91: 'Solar Cell Current'}

def decode_msg(msg):
    binary = bytes.fromhex(msg)

    if len(binary) < 5:
        return {}

    decoded = {
        'to': binary[0],
        'from': binary[1],
        'id': binary[2],
        'flags': binary[3],
        'type': binary[4],
        'values': []
    }

    for i in range(5, len(binary), 5):
        decoded['values'].append({'id': binary[i],
                                  'val': struct.unpack('f', binary[i+1:][:4])[0]})
    return decoded


def pretty_print_header(decoded):
    type_msg = MSG_TYPES.get(decoded['type'], "")
    return '0x{from:02x} -> 0x{to:02x} (ID={id}, FLAGS=0x{flags:02x}) TYPE(0x{type:02x})="{type_msg}" '.format(**decoded, type_msg=type_msg)


def pretty_print_payload(decoded):
    values = []
    for val in decoded['values']:
        values.append('  (0x{id:02x}) {type:20s} = {val:15.4f}'.format(type=PAYLOAD_TYPES.get(val['id'], ''), **val))
    return '\n'.join(values)

if __name__ == "__main__":
    decoded = decode_msg("ff100f0010203333c74122806ed247804c3751409000000000")

    print("####", pretty_print_header(decoded))
    print(pretty_print_payload(decoded))

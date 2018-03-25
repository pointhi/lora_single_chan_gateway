
import datetime


class ReceivedPackage(object):
    def __init__(self, payload=None, frequency=None):
        self.datetime = datetime.datetime.now()

        self.modulation = None

        self.frequency = frequency  # given in MHz

        self.snr = None
        self.rssi = None

        self.payload = payload

    def __str__(self):
        ret_str = ""

        ret_str += self.modulation + " "


class LoraReceivedPackage(ReceivedPackage):
    def __init__(self, payload=None, frequency=None, datarate = None, codingrate = None, crc = None):
        super(LoraReceivedPackage).__init__(self, payload=payload, frequency=frequency)

        self.modulation = "LORA"

        self.datarate = datarate
        self.codingrate = codingrate

        self.crc = crc

    def __str__(self):
        return "LORA:"
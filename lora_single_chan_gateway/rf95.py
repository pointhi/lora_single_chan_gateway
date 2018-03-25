# configuration based on: https://github.com/PaulStoffregen/RadioHead/blob/master/RH_RF95.cpp

import datetime
import logging
import time

import RPi.GPIO as GPIO
import spidev

class RF95(object):
    def __init__(self):
        # pin are given in BCM schema, for Draguino Board
        self._pin_ss = 25  # GPIO 6
        self._pin_dio0 = 4  # GPIO 7
        self._pin_rst = 17  # GPIO 0

        self._spi_bus = 0
        self._spi_cs = 0  # TODO: Draguino has it's own non-standard CS pin

        self.spi = None
        self._is_sx1272 = None  # is set in setup

        self._mode = None

    def __enter__(self):
        self.setup_device()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown_device()

    def _init_pins(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self._pin_ss, GPIO.OUT)
        GPIO.setup(self._pin_dio0, GPIO.IN)
        GPIO.setup(self._pin_rst, GPIO.OUT)

    def _init_spi(self):
        self.spi = spidev.SpiDev()
        self.spi.open(self._spi_bus, self._spi_cs)
        self.spi.max_speed_hz = 5000000  # TODO: what value works good?

    def setup_device(self):
        self._init_pins()
        self._init_spi()

        GPIO.output(self._pin_rst, 1)
        time.sleep(0.10)
        GPIO.output(self._pin_rst, 0)
        time.sleep(0.10)

        version = self.read_register(SX127x.REG_VERSION)

        if version == 0x22:
            logging.info("SX1272 detected, starting...")
            self._is_sx1272 = True
        else:
            # sx1276?
            GPIO.output(self._pin_rst, 0)
            time.sleep(0.10)
            GPIO.output(self._pin_rst, 1)
            time.sleep(0.10)

            version = self.read_register(SX127x.REG_VERSION)

            if version == 0x12:
                logging.info("SX1276 detected, starting...")
                self._is_sx1272 = False
            else:
                logging.critical("Unrecognized transceiver")
                raise RuntimeError("Unrecognized transceiver")

        # set sleep mode
        self.mode = 0x00 | 0x80  # Mode Sleep | Long Range Mode
        time.sleep(0.01)  # wait for sleep mode
        assert self.mode == (0x00 | 0x80)

        # Set up FIFO, either receive or transmit (but not both at same time)
        self.write_register(SX127x.REG_FIFO_TX_BASE_AD, 0)
        self.write_register(SX127x.REG_FIFO_RX_BASE_AD, 0)

        self.mode = 0x01  # Mode Standby

        # Bw125Cr45Sf128 (chip default)
        self.write_register(SX127x.REG_MODEM_CONFIG, 0x72)  # 125kHz 4/5
        self.write_register(SX127x.REG_MODEM_CONFIG2, (self.sf << 4) | 0x04)  # SF7, enable CTC
        self.write_register(SX127x.REG_MODEM_CONFIG3, 0x00)

        # set preamble to 8
        self.write_register(0x20, 0)
        self.write_register(0x21, 8)

        self.frequency = 433300000

        self.tx_power = 13

    def teardown_device(self):
        logging.info("tear down transceiver...")
        GPIO.cleanup()
        self.spi.close()

    def read_register(self, register):
        GPIO.output(self._pin_ss, 0)

        value = self.spi.xfer([register & 0x7F, 0])[1]

        GPIO.output(self._pin_ss, 1)

        return value

    def read_register_burst(self, register, n):
        GPIO.output(self._pin_ss, 0)

        value = self.spi.xfer([register & 0x7F] + [0]*n)[1:]

        GPIO.output(self._pin_ss, 1)

        return value

    def write_register(self, register, value):
        GPIO.output(self._pin_ss, 0)

        self.spi.xfer([register | 0x80, value])

        GPIO.output(self._pin_ss, 1)

    def receive_package(self):
        #self.write_register(SX127x.REG_IRQ_FLAGS, 0x40)  # clear rxDone

        irqflags = self.read_register(SX127x.REG_IRQ_FLAGS)
        if not irqflags & 0x40:
            self.write_register(SX127x.REG_IRQ_FLAGS, 0xFF)  # clear all IRQ flags
            return None  # RX not done yet
        if irqflags & 0x20:
            logging.warning("CRC error")
            self.write_register(SX127x.REG_IRQ_FLAGS, 0x20)
            crc = False
        else:
            crc = True

        received_count = self.read_register(SX127x.REG_RX_NB_BYTES)

        current_addr = self.read_register(SX127x.REG_FIFO_RX_CURRENT_ADDR)
        self.write_register(SX127x.REG_FIFO_ADDR_PTR, current_addr)

        payload = bytearray()
        payload.extend(self.read_register_burst(SX127x.REG_FIFO, received_count))
        #for _ in range(received_count):
        #    payload.append(self.read_register(SX127x.REG_FIFO))

        pkg = {'datetime': datetime.datetime.now(),
                'crc': crc,
                'pkt_snr': self.pkt_snr,
                'pkt_rssi': self.pkt_rssi,
                'rssi': self.rssi,
                'payload:': bytes(payload)}

        self.write_register(SX127x.REG_IRQ_FLAGS, 0xFF)  # clear all IRQ flags

        return pkg

    @property
    def mode(self):
        self._mode = self.read_register(SX127x.REG_OPMODE)
        return self._mode

    @mode.setter
    def mode(self, mode):
        if self._mode != mode:
            self._mode = mode
            self.write_register(SX127x.REG_OPMODE, mode)

    @property
    def frequency(self):
        raise NotImplementedError("getFrequency not implemented yet!")

    @frequency.setter
    def frequency(self, value):
        frf = int((value << 19) / 32000000)
        self.write_register(SX127x.REG_FRF_MSB, (frf >> 16) & 0xFF)
        self.write_register(SX127x.REG_FRF_MID, (frf >> 8) & 0xFF)
        self.write_register(SX127x.REG_FRF_LSB, frf & 0xFF)

    @property
    def tx_power(self):
        raise NotImplementedError("getTxPower not implemented yet!")

    @mode.setter
    def tx_power(self, power):
        if power > 23:
            power = 23
        elif power < 5:
            power = 5

        if power > 20:
            self.write_register(0x4D, 0x07)  # PA_DAC_ENABLE
            power -= 3
        else:
            self.write_register(0x4D, 0x04)  # PA_DAC_DISABLE

        self.write_register(0x4D, 0x09 | (power-5))  # PA_SELECT | (power-5)

    @property
    def pkt_snr(self):
        snr_value = self.read_register(SX127x.REG_PKT_SNR_VALUE)
        if snr_value & 0x80:
            snr_value = ((~snr_value + 1) & 0xFF) >> 2
            return -snr_value
        else:
            return (snr_value & 0xFF) >> 2

    @property
    def pkt_rssi(self):
        if self._is_sx1272:
            rssicorr = 139
        else:
            rssicorr = 157
        return self.read_register(0x1A) - rssicorr

    @property
    def rssi(self):
        if self._is_sx1272:
            rssicorr = 139
        else:
            rssicorr = 157
        return self.read_register(0x1B) - rssicorr


class SX127x:
    REG_FIFO                    = 0x00
    REG_FRF_MSB                 = 0x06
    REG_FRF_MID                 = 0x07
    REG_FRF_LSB                 = 0x08
    REG_LNA                     = 0x0C
    REG_FIFO_ADDR_PTR           = 0x0D
    REG_FIFO_TX_BASE_AD         = 0x0E
    REG_FIFO_RX_BASE_AD         = 0x0F
    REG_RX_NB_BYTES             = 0x13
    REG_OPMODE                  = 0x01
    REG_FIFO_RX_CURRENT_ADDR    = 0x10
    REG_IRQ_FLAGS               = 0x12
    REG_DIO_MAPPING_1           = 0x40
    REG_DIO_MAPPING_2           = 0x41
    REG_MODEM_CONFIG            = 0x1D
    REG_MODEM_CONFIG2           = 0x1E
    REG_MODEM_CONFIG3           = 0x26
    REG_SYMB_TIMEOUT_LSB        = 0x1F
    REG_PKT_SNR_VALUE           = 0x19
    REG_PAYLOAD_LENGTH          = 0x22
    REG_IRQ_FLAGS_MASK          = 0x11
    REG_MAX_PAYLOAD_LENGTH      = 0x23
    REG_HOP_PERIOD              = 0x24
    REG_SYNC_WORD               = 0x39
    REG_VERSION                 = 0x42

    SX72_MODE_RX_CONTINUOS      = 0x85
    SX72_MODE_TX                = 0x83
    SX72_MODE_SLEEP             = 0x80
    SX72_MODE_STANDBY           = 0x81

    LNA_MAX_GAIN                = 0x23
    LNA_OFF_GAIN                = 0x00
    LNA_LOW_GAIN                = 0x20
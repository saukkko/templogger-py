from logger import setup_logger
from os import open, close, write, read, O_RDWR
from fcntl import ioctl  # type: ignore
from time import sleep
from logging import Logger
from bases.AM2320Base import AM2320Base


def usleep(microseconds: int):
    return sleep(microseconds / 1000000)


class AM2320(AM2320Base):
    I2C_ADDR: int = 0x5c
    I2C_BUS: str = "/dev/i2c-1"
    IOCTL_CMD: int = 0x0703
    read_count: int = 2
    err_count: int = 0
    fd: int
    log: Logger = setup_logger("WARN")
    delay: int = 2

    def __init__(self, addr: int = None, bus: str = None, read_count: int = None, loglevel: str = None):
        super().__init__(addr, bus, read_count, loglevel)
        if loglevel:
            self.log = setup_logger(loglevel)
        if read_count:
            self.read_count = read_count
        if addr:
            self.I2C_ADDR = addr
        if bus:
            self.I2C_BUS = bus

        self.log.debug(f"Opening bus '{self.I2C_BUS}'")
        self.fd = open(self.I2C_BUS, O_RDWR)
        self.log.debug(f"calling ioctl() with command '{hex(self.IOCTL_CMD)}' "
                       f"on I2C address '{hex(self.I2C_ADDR)}'")
        ioctl(self.fd, self.IOCTL_CMD, self.I2C_ADDR)

    def __enter__(self):  # idk what's the point of this tbh
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # is this even necessary?
        if self.fd:
            close(self.fd)
        print(exc_type, exc_val, exc_tb)

    def _send(self, b: bytes):
        self.log.debug(f"SENSOR_SEND: {b.hex()}")
        return write(self.fd, b)

    def _recv(self, length: int = 8):
        return read(self.fd, length)

    def _wakeup(self):
        try:
            # will raise OSError every time if the device is asleep
            self._send(b'\xff')
        except OSError:
            pass
        usleep(850)

    def _read_registers(self, start: int, num: int):
        arr = bytearray([0x03, start, num])
        # device always sends [0x03, <num_regs_asked>, <reg_data>, crc_hi, crc_lo]
        size = num + 4

        self.log.debug(f"Sensor wakeup")
        self._wakeup()

        self.log.info(f"Request the data...")
        self._send(bytes(arr))
        usleep(1800)

        self.log.info(f"...read the data")
        data = self._recv(size)
        self.log.debug(f"SENSOR_RECV: {data.hex(' ', 2)}")

        self.log.info(f"Verifying data...")
        crc = self._crc16(data[0:size - 2])
        self.log.debug(f"CRC: {crc}")

        dev_crc = data[size - 1] << 8 | data[size - 2]
        self.log.debug(f"SENSOR_CRC: {dev_crc}")

        if self.err_count > 5:
            # to prevent recursion loop
            self.log.critical(
                f"Refusing to continue after 5 consecutive CRC Errors")
            raise IOError
        if crc != dev_crc:
            self.err_count += 1
            self.log.error(
                f"Received CRC error, re-reading (error count: {self.err_count}")
            self._read_registers(start, num)
        else:
            self.log.info(f"Read OK")
            print()
            self.err_count = 0
            return data

    def get_humidity(self):
        val = b'\x00'
        for i in range(self.read_count):
            self.log.info(f"Begin read #{i+1}")
            val = self._read_registers(0x00, 0x02)
            if i < self.read_count - 1:
                sleep(self.delay)
        return val

    def get_temperature(self):
        val = b'\x00'
        for i in range(self.read_count):
            self.log.info(f"Begin read #{i+1}")
            val = self._read_registers(0x02, 0x02)
            if i < self.read_count - 1:
                sleep(self.delay)
        return val

    def get_all(self):
        val = b'\x00'
        for i in range(self.read_count):
            self.log.info(f"Begin read #{i+1}")
            val = self._read_registers(0x00, 0x04)
            if i < self.read_count - 1:
                sleep(self.delay)
        return val

    @staticmethod
    def _crc16(data: bytes):
        # Theoretically, according to the internet, array comparison from lookup table is
        # faster than iterating over the values this way. This looks cleaner and the speed benefit is marginal
        crc = 0xFFFF
        for i in data:
            crc = crc ^ i
            for bit in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

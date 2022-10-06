from os import PathLike
from abc import ABC
from logging import Logger


class AM2320Base(ABC):
    I2C_ADDR: int
    I2C_BUS: str | bytes | PathLike[str] | PathLike[bytes]
    read_count: int
    err_count: int
    IOCTL_CMD: int
    fd: int
    log: Logger

    def __init__(self,
                 addr: int = None,
                 bus: str = None,
                 read_count: int = None,
                 loglevel: str = None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _send(self, b: bytes) -> int:
        """
        Send bytes to sensor
        :param b: bytes to send
        :return: number of bytes sent
        """
        pass

    def _recv(self, length: int = 8) -> bytes:
        """
        Read data from sensor
        :param length: how many bytes to read (4 + register size)
        :return: received bytes
        """
        pass

    def _wakeup(self) -> None:
        """
        Sensor starts to sleep after 3 seconds of inactivity to prevent
        changes in temperature caused by heat emitted by the sensor.
        This method sends single non-null (0xff) byte for the sensor to wake yp.
        :return: None
        """
        pass

    def _read_registers(self, start: int, num: int) -> bytes:
        """
        This method does the following:
            1. Sensor wakeup. (+ sleep 850 µs)
            2. Request `num` data, starting from `start` register.
            3. Give the sensor 1800 µs time to "think"
            4. Read back the requested data
            5. Verify the checksum of the data (CRC16)
            6. Return the data
        :param start: The register where to start reading from.
        :param num: How many registers to read
        :return: Received bytes from the sensor
        """
        pass

    def get_humidity(self) -> bytes:
        pass

    def get_temperature(self) -> bytes:
        pass

    def get_all(self) -> bytes:
        pass

    def something_new(self) -> str:
        pass

    @staticmethod
    def _crc16(data: bytes) -> int:
        pass

from base64 import b64encode


def fmt_response(cmd: str, data: bytes, fmt: str | None = "human", enc: str = "utf8") -> str | dict[str, float]:
    """
    Formats the response based on the message (command)
    :param cmd: The command received on what we're supposed to act upon
    :param data: Raw data as bytes
    :param fmt: Format (base64, hex, human, json)
    :param enc: (optional) Encoding. Defaults to UTF-8.
    :return: Formatted sensor data as bytes.
    """

    def handle_negative_temp(temperature: int) -> int:
        """
        Temperature register is 16 bits long and the 16th bit is there to tell if we're below zero
        """
        if temperature & 0x8000:
            return -(temperature & 0x7fff)
        else:
            return temperature

    def fmt_data(d: bytes, hi: int, lo: int) -> int:
        return d[hi] << 8 | d[lo]

    match cmd:
        case "all":
            match fmt:
                case "base64":
                    return b64encode(data).decode(enc)
                case "hex":
                    return data.hex(" ", 2)
                case "json":
                    humi = fmt_data(data, 2, 3) / 10
                    temp = fmt_data(data, 4, 5)
                    t = handle_negative_temp(temp) / 10
                    return {"humi": humi, "temp": t}
                case "human":
                    humi = fmt_data(data, 2, 3) / 10
                    temp = fmt_data(data, 4, 5)
                    t = handle_negative_temp(temp) / 10
                    return f"RH %: {humi}, \xb0C: {t}"
                case _:
                    pass
        case "humi":
            match fmt:
                case "base64":
                    return b64encode(data).decode(enc)
                case "hex":
                    return data.hex(" ")
                case "json":
                    humi = fmt_data(data, 2, 3) / 10
                    return {"humi": humi}
                case "human":
                    humi = fmt_data(data, 2, 3) / 10
                    return f"RH %: {humi}"
                case _:
                    pass
        case "temp":
            match fmt:
                case "base64":
                    return b64encode(data).decode(enc)
                case "hex":
                    return data.hex(" ")
                case "json":
                    temp = fmt_data(data, 2, 3)
                    t = handle_negative_temp(temp) / 10
                    return {"temp": t}
                case "human":
                    temp = fmt_data(data, 2, 3)
                    t = handle_negative_temp(temp) / 10
                    return f"\xb0C: {t}"
                case _:
                    pass
        case _:
            return b'\x00'.decode(enc)
    return b'\x00'.decode(enc)

import logging
import time

from django.conf import settings

try:
    import serial
    from serial import SerialException
except ImportError:  # pragma: no cover
    serial = None

    class SerialException(Exception):
        pass


logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    return bool(getattr(settings, "ARDUINO_ENABLED", False))


def _open_serial_connection():
    if not _is_enabled() or serial is None:
        return None

    port = getattr(settings, "ARDUINO_SERIAL_PORT", "")
    if not port:
        logger.warning("Arduino integration enabled without ARDUINO_SERIAL_PORT configured.")
        return None

    baudrate = int(getattr(settings, "ARDUINO_BAUD_RATE", 9600))
    timeout = float(getattr(settings, "ARDUINO_TIMEOUT_SECONDS", 1.5))
    return serial.Serial(port=port, baudrate=baudrate, timeout=timeout, write_timeout=timeout)


def send_command(command: str) -> bool:
    connection = None
    try:
        connection = _open_serial_connection()
        if connection is None:
            return False

        boot_delay = float(getattr(settings, "ARDUINO_BOOT_DELAY_SECONDS", 2.0))
        if boot_delay > 0:
            time.sleep(boot_delay)
        connection.reset_input_buffer()
        connection.write(f"{command}\n".encode("utf-8"))
        connection.flush()
        response = connection.readline().decode("utf-8", errors="ignore").strip()
        if response:
            logger.info("Arduino response: %s", response)
        return bool(response) and not response.startswith("ERR:")
    except (OSError, SerialException) as exc:
        logger.warning("Arduino command '%s' failed: %s", command, exc)
        return False
    finally:
        if connection is not None:
            connection.close()


def sync_house_output(*, pin: int, is_on: bool, flash_before_off: bool = False) -> bool:
    if flash_before_off:
        send_command("FLASH")
    command = f"HOUSE:{'ON' if is_on else 'OFF'}"
    return send_command(command)
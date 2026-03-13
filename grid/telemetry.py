import atexit
import signal
import threading
from typing import Any

from django.db import close_old_connections, transaction


_lock = threading.Lock()
_latest_values: dict[str, dict[str, Any]] = {}
_hooks_registered = False


STATUS_MAP = {
    "green": "Stable",
    "yellow": "Warning",
    "red": "Critical",
}


def record_latest(
    node_id: str,
    *,
    input_value: float,
    output_value: float,
    status: str,
    persisted_status: str | None = None,
) -> None:
    with _lock:
        _latest_values[node_id] = {
            "input": input_value,
            "output": output_value,
            "status": persisted_status or STATUS_MAP.get(status, "Stable"),
        }


def flush_latest_to_db() -> None:
    with _lock:
        if not _latest_values:
            return
        payload = dict(_latest_values)
        _latest_values.clear()

    from .models import GridNode

    close_old_connections()
    with transaction.atomic():
        for node_id, values in payload.items():
            GridNode.objects.filter(pk=node_id).update(
                input=values["input"],
                output=values["output"],
                status=values["status"],
            )
    close_old_connections()


def register_shutdown_hooks() -> None:
    global _hooks_registered

    if _hooks_registered:
        return

    atexit.register(flush_latest_to_db)

    for sig in (signal.SIGINT, signal.SIGTERM):
        previous_handler = signal.getsignal(sig)

        def _handler(signum, frame, previous=previous_handler):
            flush_latest_to_db()
            if callable(previous):
                previous(signum, frame)
            elif previous == signal.SIG_DFL:
                raise SystemExit(0)

        signal.signal(sig, _handler)

    _hooks_registered = True
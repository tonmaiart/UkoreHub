"""Bridges Python's stdlib `logging` into DebugConsole's Qt UI. Lives in
interface/ (not core/) because it subclasses QObject — core/ stays
Qt-free (see core/events/ — now retired in favor of this).

Any module anywhere in the app can now just do
`logging.getLogger("SomeName").info(...)` with no api/bus threading at
all; this handler is the one piece that turns those records into a live
DebugConsolePage view."""
from __future__ import annotations

import logging
import sys
from collections import deque

from PySide6.QtCore import QObject, Signal


class QtLogHandler(logging.Handler, QObject):
    """A logging.Handler that also emits a Qt signal per record. Must be
    constructed on the GUI thread (before QApplication.exec() starts) — a
    record logged from a worker thread still emits safely, since Qt
    auto-queues a signal emission to whatever thread the receiving QObject
    (this one) actually lives on, delivering it once the GUI event loop
    picks it up. Never mutate a widget directly from emit() itself; only
    the queued signal may reach the UI.

    logging.Handler.handle() already acquires self.lock around emit(), so
    mutating _records/_sources below is thread-safe without extra locking
    of our own."""

    log_record_emitted = Signal(object)  # logging.LogRecord

    def __init__(self, max_entries: int = 1000):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self._records: deque[logging.LogRecord] = deque(maxlen=max_entries)
        self._sources: set[str] = set()

    def emit(self, record: logging.LogRecord) -> None:
        self._sources.add(record.name)
        self._records.append(record)
        self.log_record_emitted.emit(record)

    @property
    def records(self) -> list[logging.LogRecord]:
        return list(self._records)

    @property
    def sources(self) -> list[str]:
        return sorted(self._sources)

    def clear(self) -> None:
        self._records.clear()
        self._sources.clear()


def configure_app_logging(qt_handler: QtLogHandler) -> None:
    """Called once, early in launcher.py (right after QApplication exists),
    to make every `logging.getLogger(...)` call in the app show up in
    DebugConsole. Also adds a stdout handler when there's an actual
    console to write to — the app is normally launched via pythonw.exe,
    which has no console/stdout at all, so that handler is skipped then
    rather than raising on the first write()."""
    formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", "%H:%M:%S")
    qt_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(qt_handler)

    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # boto3/botocore/urllib3 (core/vcs/cloud_sync.py's R2 client) are
    # chatty at INFO/DEBUG — keep DebugConsole and the console focused on
    # this app's own log sources.
    for noisy_logger in ("boto3", "botocore", "urllib3", "s3transfer"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

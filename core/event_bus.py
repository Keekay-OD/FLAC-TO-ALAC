from PyQt6.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    """
    Global cross-tab communication.
    ConvertTab emits progress → HistoryTab listens.
    """

    # flac_path (str), percent (int)
    progress_updated = pyqtSignal(str, int)

    # flac_path (str), success (bool)
    conversion_finished = pyqtSignal(str, bool)


# Global instance (import everywhere)
event_bus = EventBus()

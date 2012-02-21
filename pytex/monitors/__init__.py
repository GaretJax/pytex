try:
    from pytex.monitors import pyinotify as monitor
except ImportError:
    from pytex.monitors import fsevents as monitor


__all__ = ['monitor']

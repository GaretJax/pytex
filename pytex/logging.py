from __future__ import absolute_import

from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
import logging
import logging.handlers
import sys


__all__ = [
    'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL',
]


class LevelColoringFormatter(logging.Formatter):
    GRAY, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    LEVELS_TO_COLORS = {
        10: BLUE,
        20: GREEN,
        30: YELLOW,
        40: RED,
        50: RED,
    }

    def hilite(self, string, color=None, bold=False, background=None):
        attr = []

        if color:
            attr.append(str(color + 30))

        if background:
            attr.append(str(background + 40))

        if bold:
            attr.append('1')

        return '\x1b[{0}m{1}\x1b[0m'.format(';'.join(attr), string)

    def format(self, record):
        s = super(LevelColoringFormatter, self).format(record)
        level = max(0, record.levelno)
        level = min(CRITICAL, level)
        level = level // 10 * 10

        color = LevelColoringFormatter.LEVELS_TO_COLORS[level]
        return s.replace(record.levelname,
                self.hilite(record.levelname, color=color), 1)


class StdioOnnaStick(object):
    """
    A class that pretends to be a file object and instead executes a callback
    for each line written to it.
    """

    softspace = 0
    mode = 'wb'
    name = '<stdio (log)>'
    closed = 0

    def __init__(self, callback):
        self.buf = ''
        self.callback = callback

    def close(self):
        pass

    def fileno(self):
        return -1

    def flush(self):
        pass

    def read(self):
        raise IOError("can't read from the log!")

    readline = read
    readlines = read
    seek = read
    tell = read

    def write(self, data):
        d = (self.buf + data).split('\n')
        self.buf = d[-1]
        messages = d[0:-1]
        for message in messages:
            self.callback(message)

    def writelines(self, lines):
        for line in lines:
            self.callback(line)


class LoggingSubsystem(object):
    def __init__(self, verbosity, logfile):
        self.verbosity = verbosity
        self.logfile = logfile

    def start(self):
        # Configure logging
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - " \
                "%(name)s - %(message)s (%(pathname)s:%(lineno)d)")
        console_formatter = LevelColoringFormatter("%(levelname)10s: " \
                "%(message)s")

        # All console output not explicitly directed to the user should be
        # a log message instead
        self.console_handler = logging.StreamHandler(sys.__stdout__)
        self.console_handler.setFormatter(console_formatter)
        self.console_handler.setLevel(self.verbosity)

        # Capture all logging output and write it to the specified log file
        self.file_handler = logging.FileHandler(self.logfile, 'w', delay=True)
        self.file_handler.setFormatter(file_formatter)
        self.file_handler.setLevel(logging.ERROR)

        # Buffer the logging until no errors happen
        self.buffered_handler = logging.handlers.MemoryHandler(9999, CRITICAL)
        self.buffered_handler.setTarget(self.file_handler)

        logger = logging.getLogger()
        logger.setLevel(1)
        logger.addHandler(self.console_handler)
        logger.addHandler(self.buffered_handler)

    def get_logger(self, name):
        return logging.getLogger(name)

    def capture_stdout(self):
        sys.stdout = StdioOnnaStick(logging.getLogger('stdout').info)
        sys.stderr = StdioOnnaStick(logging.getLogger('stderr').error)

    def increment_verbosity(self, steps=1):
        self.verbosity = max(1, self.verbosity - 10 * steps)
        self.console_handler.setLevel(self.verbosity)
        self.file_handler.setLevel(1)

    def stop(self, status=0):
        if not status:
            self.buffered_handler.setTarget(None)
            self.buffered_handler.close()

        else:
            self.buffered_handler.flush()
            self.buffered_handler.close()

            print >>sys.__stdout__, "pytex exited with a non-zero exit " \
                    "status (%d). A complete log was stored in the %s " \
                    "file." % (status, self.logfile)

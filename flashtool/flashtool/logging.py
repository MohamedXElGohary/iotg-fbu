from logging import *
import logging.config as config
import logging.handlers as handlers
from click import style, echo
from logging import __all__

__all__.extend(["SUCCESS", "success", "ClickHandler", "SuppressExceptionFormatter"])

# adding a new level SUCCESS
SUCCESS = 25
addLevelName(SUCCESS, "SUCCESS")

def success(self, msg, *args, **kwargs):
    """
        Log 'msg % args' with level 'SUCCESS'.
    """
    if self.isEnabledFor(SUCCESS):
        self._log(SUCCESS, msg, args, **kwargs)

Logger.success = success


class ClickHandler(StreamHandler):
    '''This class colors the console output'''

    def __init__(self, stream=None, levelcolor={}):
        super().__init__(stream)
        self.levelcolor = levelcolor

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to console using click.echo(). Foregorund
        color is chosen according to level and set using click.style(msg, fg).
        """
        try:
            msg = self.format(record)
            # fg = self._LEVELCOLOR[record.levelno]
            fg = self.levelcolor.get(record.levelname, None)
            echo(style(msg, fg=fg))
        except Exception:
            self.handleError(record)


class SuppressExceptionFormatter(Formatter):
    '''Supresses the Traceback of error'''
    def format(self, record):
        """
        Format the specified record as text.

        The record's attribute dictionary is used as the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record is computed
        using LogRecord.getMessage(). If the formatting string uses the
        time (as determined by a call to usesTime(), formatTime() is
        called to format the event time. If there is exception information,
        it is discarded.
        """
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        return s


_getLogger = getLogger


def getLogger(name, *, logging_cfg=None):
    if logging_cfg:
        config.dictConfig(logging_cfg)
    logger = _getLogger(name)
    return logger

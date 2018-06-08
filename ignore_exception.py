import logging
import traceback

log = logging.getLogger(__name__)


class IgnoreExceptions:

    """
    Helper class for ignoring exceptions
    Usage:
        with SuppressExceptions(StopIteration):
            do_something_dangerous()
    This code will suppress only StopIteration exception(and all children).
    All other exceptions will be untouched
    """

    def __init__(self, exception_type=Exception, verbose=True):
        """
        Init SuppressExceptions object

        :param class exception_type: exception type(and all children) to suppress
        :param bool verbose: show(or not show) messages on suppressing(not suppressing) exceptions
        """
        self.igonre_exception_class = exception_type
        self.verbose = verbose

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if not tb:
            return True
        if isinstance(value, self.igonre_exception_class):
            if self.verbose:
                log.info('ignoring exception %s' % value)
                log.debug(traceback.format_exc())
            return True
        if self.verbose:
            log.info('not ignoring exception %s' % value)
            log.debug(traceback.format_exc())
        return False

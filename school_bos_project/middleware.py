import logging
import traceback

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class BrokenPipeLoggingMiddleware(MiddlewareMixin):
    """Middleware to catch BrokenPipeError / ConnectionResetError and log helpful request info.

    This does NOT suppress the error, but logs the request path, client address,
    and some META fields to aid debugging when clients disconnect prematurely.
    """

    def process_exception(self, request, exception):
        try:
            is_broken_pipe = isinstance(exception, (BrokenPipeError, ConnectionResetError))
        except Exception:
            is_broken_pipe = False

        if is_broken_pipe:
            try:
                client_ip = request.META.get('REMOTE_ADDR')
                client_port = request.META.get('REMOTE_PORT')
                info = {
                    'path': request.path,
                    'method': request.method,
                    'client_ip': client_ip,
                    'client_port': client_port,
                    'content_length': request.META.get('CONTENT_LENGTH'),
                    'content_type': request.META.get('CONTENT_TYPE'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                }
                logger.warning('Broken pipe / connection reset while handling request: %s', info)
            except Exception:
                logger.warning('Broken pipe / connection reset (failed to read request META)')
            # Re-raise or return None to let default handling continue
            return None


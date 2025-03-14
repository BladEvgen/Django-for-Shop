import logging
import traceback
from pathlib import Path
from logging.handlers import RotatingFileHandler

from django.conf import settings
from django.utils.timezone import now


class ClickLogger:
    """
    Enhanced logging class that uses Python's built-in logging module
    for better performance and features.
    """

    def __init__(self, log_dir=None, max_size_mb=10, backup_count=5):
        """
        Initialize the logger with configurable parameters

        Args:
            log_dir: Directory to store logs (defaults to BASE_DIR/logs)
            max_size_mb: Maximum log file size before rotation in MB
            backup_count: Number of backup files to keep
        """
        self.log_dir = log_dir or Path(settings.BASE_DIR) / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("click_logger")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            log_path = self.log_dir / "click_logs.log"

            handler = RotatingFileHandler(
                log_path,
                maxBytes=max_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding="utf-8",
            )

            formatter = logging.Formatter("%(asctime)s - %(message)s")

            formatter.datefmt = "%H:%M:%S %d.%m.%Y"

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_click(self, request, extra_data=None):
        """
        Log a click event with request information and optional extra data

        Args:
            request: Django HttpRequest object
            extra_data: Optional dictionary of additional data to log
        """
        try:
            if hasattr(request, "user") and request.user.is_authenticated:
                username = request.user.username
            else:
                username = "anonymous"

            ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[
                0
            ].strip() or request.META.get("REMOTE_ADDR", "unknown")

            log_data = {
                "username": username,
                "ip": ip,
                "method": request.method,
                "path": request.path,
                "user_agent": request.META.get("HTTP_USER_AGENT", "unknown"),
                "referer": request.META.get("HTTP_REFERER", "direct"),
            }

            if extra_data and isinstance(extra_data, dict):
                log_data.update(extra_data)

            log_message = (
                f"User: {log_data['username']}, "
                f"IP: {log_data['ip']}, "
                f"Method: {log_data['method']}, "
                f"Path: {log_data['path']}, "
                f"Referer: {log_data['referer']}, "
                f"User-Agent: {log_data['user_agent']}"
            )

            extra_fields = {
                k: v
                for k, v in log_data.items()
                if k not in ["username", "ip", "method", "path", "user_agent", "referer"]
            }

            if extra_fields:
                extras = ", ".join(f"{k}: {v}" for k, v in extra_fields.items())
                log_message += f", {extras}"

            self.logger.info(log_message)

            return True
        except Exception as e:
            self.logger.error(f"Error logging click: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False


class ClickLoggingMiddleware:
    """
    Middleware that logs information about each request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        log_dir = getattr(settings, "CLICK_LOG_DIR", None)
        max_size_mb = getattr(settings, "CLICK_LOG_MAX_SIZE_MB", 10)
        backup_count = getattr(settings, "CLICK_LOG_BACKUP_COUNT", 5)

        self.logger = ClickLogger(
            log_dir=log_dir, max_size_mb=max_size_mb, backup_count=backup_count
        )

        self.exclude_paths = getattr(
            settings,
            "CLICK_LOG_EXCLUDE_PATHS",
            [
                "/static/",
                "/media/",
                "/favicon.ico",
            ],
        )

    def __call__(self, request):
        start_time = now()

        response = self.get_response(request)

        duration_ms = (now() - start_time).total_seconds() * 1000

        if not any(request.path.startswith(path) for path in self.exclude_paths):
            extra_data = {
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }

            self.logger.log_click(request, extra_data)

        return response

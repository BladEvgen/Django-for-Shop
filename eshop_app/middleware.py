from pathlib import Path
from datetime import datetime
from django_settings.settings import BASE_DIR


class SimpleLogger:
    @staticmethod
    def log(message, file_path):
        with open(file_path, "a") as log_file:
            log_file.write(message)


class ClickLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.log_folder = Path(BASE_DIR) / "log"
        self.log_path = self.log_folder / "click_logs.log"

        self.log_folder.mkdir(parents=True, exist_ok=True)

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            username = request.user.username
        else:
            username = "anonymous"

        log_time = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
        log_data = (
            f"{log_time} - User: {username}, IP: {request.META.get('REMOTE_ADDR')}, "
            f"Method: {request.method}, Path: {request.path}, "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT')}\n"
        )

        SimpleLogger.log(log_data, self.log_path)

        return response

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')

try:
    django_application = get_wsgi_application()
except Exception as e:
    import traceback
    traceback.print_exc()
    raise


def application(environ, start_response):
    if environ.get("PATH_INFO") == "/healthz/":
        body = b"ok"
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]
    return django_application(environ, start_response)

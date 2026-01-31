from django.db import DEFAULT_DB_ALIAS, connections


class EnsureDbConnectionMiddleware:
    """Ensure SQLite connection is established before request handling."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        conn = connections[DEFAULT_DB_ALIAS]
        if conn.connection is None:
            conn.ensure_connection()
        return self.get_response(request)

class CorsMiddleware:
    """
    Minimal CORS middleware so the standalone frontend (served from Django
    static files, opened directly as a file, or run from a different local
    port) can always reach the API without CORS errors.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
        response["Access-Control-Allow-Headers"] = "*"
        return response

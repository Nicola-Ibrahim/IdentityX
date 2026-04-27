from starlette.datastructures import MutableHeaders


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":

            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = MutableHeaders(scope=message)
                    headers["X-Content-Type-Options"] = "nosniff"
                    headers["X-Frame-Options"] = "DENY"
                    headers["X-XSS-Protection"] = "1; mode=block"
                    headers["Referrer-Policy"] = "no-referrer"
                    headers["Permissions-Policy"] = "geolocation=(), microphone=()"
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

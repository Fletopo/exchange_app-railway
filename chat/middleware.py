from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.db import database_sync_to_async

class TokenAuthMiddleware:
    """
    Middleware para autenticar usuarios con tokens en WebSocket.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token_key = None

        # Extraer el token de la query string
        for param in query_string.split("&"):
            key, _, value = param.partition("=")
            if key == "token":
                token_key = value
                break

        # Autenticar al usuario con el token
        scope["user"] = await self.get_user(token_key)
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token_key):
        if not token_key:
            return AnonymousUser()
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return AnonymousUser()

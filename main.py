"""Entry point: python main.py to start the server."""

from app.main import app  # noqa: F401

if __name__ == "__main__":
    import asyncio
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import RedirectResponse
    from starlette.routing import Route

    async def redirect_to_https(request):
        url = request.url.replace(scheme="https", port=443)
        return RedirectResponse(url=str(url), status_code=301)

    redirect_app = Starlette(routes=[Route("/{path:path}", redirect_to_https)])

    async def main():
        # HTTPS server on port 443
        tls_config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=443,
            ssl_certfile="/etc/letsencrypt/live/openlabs.club/fullchain.pem",
            ssl_keyfile="/etc/letsencrypt/live/openlabs.club/privkey.pem",
        )
        tls_server = uvicorn.Server(tls_config)

        # HTTP redirect server on port 80 (lightweight, no app lifespan)
        redirect_config = uvicorn.Config(redirect_app, host="0.0.0.0", port=80, log_level="warning")
        redirect_server = uvicorn.Server(redirect_config)

        await asyncio.gather(tls_server.serve(), redirect_server.serve())

    asyncio.run(main())

"""Entry point: python main.py to start the server."""

import os

from app.main import app  # noqa: F401

if __name__ == "__main__":
    import asyncio

    import uvicorn

    environment = os.environ.get("ENVIRONMENT", "dev")
    ssl_certfile = os.environ.get("SSL_CERTFILE", "")
    ssl_keyfile = os.environ.get("SSL_KEYFILE", "")

    if environment == "prod" and ssl_certfile and ssl_keyfile:
        # Production: HTTPS on 443 + HTTP→HTTPS redirect on 80
        from starlette.applications import Starlette
        from starlette.responses import RedirectResponse
        from starlette.routing import Route

        async def redirect_to_https(request):
            url = request.url.replace(scheme="https", port=443)
            return RedirectResponse(url=str(url), status_code=301)

        redirect_app = Starlette(routes=[Route("/{path:path}", redirect_to_https)])

        async def main():
            tls_config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=443,
                ssl_certfile=ssl_certfile,
                ssl_keyfile=ssl_keyfile,
            )
            tls_server = uvicorn.Server(tls_config)

            redirect_config = uvicorn.Config(redirect_app, host="0.0.0.0", port=80, log_level="warning")
            redirect_server = uvicorn.Server(redirect_config)

            await asyncio.gather(tls_server.serve(), redirect_server.serve())

        asyncio.run(main())
    else:
        # Development: plain HTTP on 8000
        port = int(os.environ.get("PORT", "8000"))
        uvicorn.run(app, host="0.0.0.0", port=port)

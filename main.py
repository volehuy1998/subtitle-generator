"""Entry point: python main.py to start the server."""

from app.main import app  # noqa: F401

if __name__ == "__main__":
    import asyncio
    import uvicorn

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

        # HTTP redirect server on port 80
        redirect_config = uvicorn.Config(app, host="0.0.0.0", port=80, log_level="warning")
        redirect_server = uvicorn.Server(redirect_config)

        await asyncio.gather(tls_server.serve(), redirect_server.serve())

    asyncio.run(main())

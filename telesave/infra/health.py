from aiohttp import web


async def _health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def start_health_server(host: str, port: int) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/healthz", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    return runner

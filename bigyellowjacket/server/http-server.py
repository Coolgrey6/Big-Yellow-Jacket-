from aiohttp import web
import os

async def handle_index(request):
    with open('websocket_test.html', 'rb') as f:
        return web.Response(body=f.read(), content_type='text/html')

app = web.Application()
app.router.add_get('/', handle_index)

if __name__ == '__main__':
    web.run_app(app, host='localhost', port=8765)
import os
import webbrowser
import asyncio

import uvicorn
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("MS_HOST", "0.0.0.0")
port = int(os.getenv("MS_PORT", 8000))


async def run_server():
    config = uvicorn.Config("main:app", host=host, port=port, reload=True)
    server = uvicorn.Server(config)
    await server.serve()


def open_browser():
    webbrowser.open(f"http://{host}:{port}")


async def main():
    # Run the server and open the browser concurrently
    await asyncio.gather(run_server(), asyncio.to_thread(open_browser))


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

import aiomonitor
from hypercorn.asyncio import serve
from hypercorn.config import Config

from app.svp_harvester import SvpHarvester

# Initialize your FastAPI app or custom asyncio app
app = SvpHarvester()  # If SvpHarvester is a FastAPI or asyncio-based app

# Hypercorn config for an ASGI server
config = Config()
config.bind = ["0.0.0.0:8000"]  # Change to your desired host/port


async def main():
    loop = asyncio.get_event_loop()

    # Initialize the monitor before running the app
    with aiomonitor.start_monitor(loop=loop):
        # Start the ASGI server to serve FastAPI with Hypercorn
        await serve(app, config)


# Run the main coroutine in the event loop
if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())

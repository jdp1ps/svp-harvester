""" Main application and routing logic for API """
import asyncio

import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError
from starlette.staticfiles import StaticFiles

from app.api.amqp.amqp_connect import AMQPConnexion
from app.api.errors.validation_error import http422_error_handler
from app.api.routes.api import router as api_router
from app.config import get_app_settings
from app.gui.routes.gui import router as gui_router


def get_application() -> FastAPI:
    """
    Get the FastAPI application
    :return:
    """
    application = FastAPI()

    settings = get_app_settings()

    application.include_router(
        api_router, prefix=f"{settings.api_prefix}/{settings.api_version}"
    )

    application.mount(
        "/static", StaticFiles(directory="./app/static", html=True), name="static"
    )

    application.include_router(gui_router)

    application.add_exception_handler(ValidationError, http422_error_handler)

    return application


app = get_application()


@app.on_event("startup")
async def startup() -> None:  # pragma: no cover
    """Init AMQP connexion at boot time"""
    amqp_connexion = AMQPConnexion(get_app_settings())
    asyncio.create_task(amqp_connexion.listen(), name="amqp_listener")


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="0.0.0.0", port=8000)

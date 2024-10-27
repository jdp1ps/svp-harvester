from fastapi import status, APIRouter
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_app_settings


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


router = APIRouter()


@router.get(
    "/",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health(request: Request, response: Response) -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on.

    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    if get_app_settings().amqp_enabled:
        amqp_disconnected = request.app.state.amqp_disconnected
        if amqp_disconnected:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return HealthCheck(status="Unhealthy")
    return HealthCheck(status="OK")

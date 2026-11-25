import os

from fastapi import FastAPI, HTTPException, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal

try:
    from .controller import control_device
    from .devices import find_device, get_devices
except ImportError:
    from controller import control_device
    from devices import find_device, get_devices

app = FastAPI(title="Smart Home Controller API", version="1.0.0")

_default_origins = "http://localhost:5173,http://localhost:3000"
_origins = [
    origin.strip()
    for origin in os.getenv("BACKEND_CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class DeviceState(BaseModel):
    id: str
    name: str
    status: Literal["ON", "OFF"]


class DeviceList(BaseModel):
    devices: list[DeviceState]


class DeviceActionResult(DeviceState):
    message: str


class HealthResponse(BaseModel):
    message: str
    status: str


@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        message="Smart Home Controller API is running", status="ok"
    )


@app.get("/devices", response_model=DeviceList)
def list_devices() -> DeviceList:
    return DeviceList(
        devices=[
            DeviceState(id=device_id, name=device.name, status=device.status)
            for device_id, device in get_devices().items()
        ]
    )


def _set_power(device_id: str, should_turn_on: bool) -> DeviceActionResult:
    device = find_device(device_id)
    if device is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found",
        )

    message = control_device(device, should_turn_on)
    return DeviceActionResult(
        id=device_id, name=device.name, status=device.status, message=message
    )


@app.post("/devices/{device_id}/on", response_model=DeviceActionResult)
def turn_device_on(device_id: str) -> DeviceActionResult:
    return _set_power(device_id, True)


@app.post("/devices/{device_id}/off", response_model=DeviceActionResult)
def turn_device_off(device_id: str) -> DeviceActionResult:
    return _set_power(device_id, False)

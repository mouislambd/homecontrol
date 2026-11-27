"""FastAPI application: HTTP boundary only.

Business rules live in services, storage behind repository interfaces, and all
concrete wiring happens in ``container``. The original API contract is kept
byte-for-byte; new features are additive routes.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request, Response, WebSocket, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Literal

try:
    from .container import get_container, get_realtime_hub
    from .domain import DeviceStatus, DeviceType, PowerAction, TriggerType
    from .exceptions import SmartHomeError
    from .logging_config import configure_logging
    from .realtime import RealtimeHub
    from .scheduler import ScheduleRunner
    from .schemas import (
        ActivityList,
        ActivityOut,
        DeviceCreate,
        DeviceDetail,
        DeviceUpdate,
        EnergyDeviceOut,
        EnergyLogList,
        EnergyLogOut,
        EnergyStats,
        EnergySummary,
        NotificationList,
        NotificationOut,
        RoomAssignment,
        RoomCreate,
        RoomList,
        RoomOut,
        RoomUpdate,
        RuleCreate,
        RuleList,
        RuleOut,
        RuleUpdate,
        ScheduleCreate,
        ScheduleList,
        ScheduleOut,
        ScheduleUpdate,
        TemperatureUpdate,
    )
except ImportError:
    from container import get_container, get_realtime_hub
    from domain import DeviceStatus, DeviceType, PowerAction, TriggerType
    from exceptions import SmartHomeError
    from logging_config import configure_logging
    from realtime import RealtimeHub
    from scheduler import ScheduleRunner
    from schemas import (
        ActivityList,
        ActivityOut,
        DeviceCreate,
        DeviceDetail,
        DeviceUpdate,
        EnergyDeviceOut,
        EnergyLogList,
        EnergyLogOut,
        EnergyStats,
        EnergySummary,
        NotificationList,
        NotificationOut,
        RoomAssignment,
        RoomCreate,
        RoomList,
        RoomOut,
        RoomUpdate,
        RuleCreate,
        RuleList,
        RuleOut,
        RuleUpdate,
        ScheduleCreate,
        ScheduleList,
        ScheduleOut,
        ScheduleUpdate,
        TemperatureUpdate,
    )


@asynccontextmanager
async def lifespan(application: FastAPI):
    configure_logging()
    get_realtime_hub().bind_loop(asyncio.get_running_loop())
    runner = ScheduleRunner(get_container().schedule_service)
    runner.start()
    try:
        yield
    finally:
        runner.stop()


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Home Controller API", version="1.2.0", lifespan=lifespan
)

_local_origins = ("http://localhost:5173", "http://localhost:3000")


def build_allowed_origins() -> list[str]:
    configured = [
        origin.strip()
        for value in (
            os.getenv("FRONTEND_ORIGIN", ""),
            os.getenv("BACKEND_CORS_ORIGINS", ""),
        )
        for origin in value.split(",")
        if origin.strip()
    ]
    if os.getenv("APP_ENV", "").strip().lower() == "production":
        return list(dict.fromkeys(configured))
    return list(dict.fromkeys([*_local_origins, *configured]))


app.add_middleware(
    CORSMiddleware,
    allow_origins=build_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(SmartHomeError)
def handle_smart_home_error(request: Request, exc: SmartHomeError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(IntegrityError)
def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("database integrity error: %s", type(exc).__name__)
    return JSONResponse(
        status_code=http_status.HTTP_409_CONFLICT,
        content={"detail": "Database constraint violation", "code": "conflict"},
    )


@app.exception_handler(SQLAlchemyError)
def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("database error: %s", type(exc).__name__)
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database operation failed", "code": "database_error"},
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


def _device_detail(device, container) -> DeviceDetail:
    reading = container.energy_service.reading_for(device.device_id)
    return DeviceDetail(
        id=device.device_id,
        name=device.name,
        status=device.status,
        device_type=device.device_type.value,
        online=device.online,
        room_id=device.room_id,
        wattage=device.energy_meter.wattage,
        energy_wh=reading.energy_wh,
        temperature_c=device.temperature_c,
        temperature_source=device.temperature_source,
    )


@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        message="Smart Home Controller API is running", status="ok"
    )


@app.get("/devices", response_model=DeviceList)
def list_devices(container=Depends(get_container)) -> DeviceList:
    return DeviceList(
        devices=[
            DeviceState(id=device.device_id, name=device.name, status=device.status)
            for device in container.device_service.list_devices()
        ]
    )


@app.post("/devices", response_model=DeviceDetail, status_code=http_status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, container=Depends(get_container)) -> DeviceDetail:
    if payload.room_id is not None:
        container.room_service.get_room(payload.room_id)
    device = container.device_service.create_device(
        payload.id,
        payload.name,
        DeviceType(payload.device_type),
        payload.wattage,
        payload.room_id,
        payload.online,
        DeviceStatus(payload.initial_status),
    )
    return _device_detail(device, container)


@app.put("/devices/{device_id}", response_model=DeviceDetail)
def update_device(
    device_id: str, payload: DeviceUpdate, container=Depends(get_container)
) -> DeviceDetail:
    if payload.room_id is not None:
        container.room_service.get_room(payload.room_id)
    device = container.device_service.update_device(
        device_id,
        name=payload.name,
        wattage=payload.wattage,
        room_id=payload.room_id,
        online=payload.online,
    )
    return _device_detail(device, container)


@app.delete("/devices/{device_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_device(device_id: str, container=Depends(get_container)) -> Response:
    container.device_service.delete_device(device_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


def _set_power(device_id: str, should_turn_on: bool, container) -> DeviceActionResult:
    result = container.device_service.set_power(device_id, should_turn_on)
    return DeviceActionResult(
        id=device_id,
        name=result.device.name,
        status=result.device.status,
        message=result.message,
    )


@app.post("/devices/{device_id}/on", response_model=DeviceActionResult)
def turn_device_on(device_id: str, container=Depends(get_container)) -> DeviceActionResult:
    return _set_power(device_id, True, container)


@app.post("/devices/{device_id}/off", response_model=DeviceActionResult)
def turn_device_off(device_id: str, container=Depends(get_container)) -> DeviceActionResult:
    return _set_power(device_id, False, container)


@app.get("/devices/{device_id}/status", response_model=DeviceDetail)
def device_status(device_id: str, container=Depends(get_container)) -> DeviceDetail:
    return _device_detail(container.device_service.get_device(device_id), container)


@app.post("/devices/{device_id}/online", response_model=DeviceDetail)
def bring_device_online(device_id: str, container=Depends(get_container)) -> DeviceDetail:
    return _device_detail(container.device_service.set_online(device_id, True), container)


@app.post("/devices/{device_id}/offline", response_model=DeviceDetail)
def bring_device_offline(device_id: str, container=Depends(get_container)) -> DeviceDetail:
    return _device_detail(container.device_service.set_online(device_id, False), container)


@app.put("/devices/{device_id}/temperature", response_model=DeviceDetail)
def set_device_temperature(
    device_id: str, payload: TemperatureUpdate, container=Depends(get_container)
) -> DeviceDetail:
    device = container.device_service.set_temperature(device_id, payload.value)
    return _device_detail(device, container)


@app.put("/devices/{device_id}/room", response_model=DeviceDetail)
def assign_device_room(
    device_id: str, payload: RoomAssignment, container=Depends(get_container)
) -> DeviceDetail:
    return _device_detail(
        container.room_service.assign_device(device_id, payload.room_id), container
    )


@app.get("/devices/{device_id}/activity", response_model=ActivityList)
def device_activity(
    device_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    source: Literal["api", "schedule", "automation", "system"] | None = Query(default=None),
    container=Depends(get_container),
) -> ActivityList:
    container.device_service.get_device(device_id)
    return ActivityList(
        activity=[
            ActivityOut(
                id=item.id,
                device_id=item.device_id,
                action=item.action,
                previous_status=item.previous_status,
                status=item.status,
                source=item.source.value,
                occurred_at=item.occurred_at,
            )
            for item in container.activity_service.list_events(device_id, limit, source)
        ]
    )


@app.get("/rooms", response_model=RoomList)
def list_rooms(container=Depends(get_container)) -> RoomList:
    return RoomList(
        rooms=[
            RoomOut(
                id=room.id,
                name=room.name,
                description=room.description,
                device_count=len(container.room_service.devices_in(room.id)),
            )
            for room in container.room_service.list_rooms()
        ]
    )


@app.post("/rooms", response_model=RoomOut, status_code=http_status.HTTP_201_CREATED)
def create_room(payload: RoomCreate, container=Depends(get_container)) -> RoomOut:
    room = container.room_service.create_room(payload.name, payload.description)
    return RoomOut(id=room.id, name=room.name, description=room.description, device_count=0)


@app.get("/rooms/{room_id}", response_model=RoomOut)
def get_room(room_id: str, container=Depends(get_container)) -> RoomOut:
    room = container.room_service.get_room(room_id)
    return RoomOut(
        id=room.id,
        name=room.name,
        description=room.description,
        device_count=len(container.room_service.devices_in(room.id)),
    )


@app.put("/rooms/{room_id}", response_model=RoomOut)
def update_room(
    room_id: str, payload: RoomUpdate, container=Depends(get_container)
) -> RoomOut:
    room = container.room_service.update_room(
        room_id, payload.name, payload.description
    )
    return RoomOut(
        id=room.id,
        name=room.name,
        description=room.description,
        device_count=len(container.room_service.devices_in(room.id)),
    )


@app.delete("/rooms/{room_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_room(room_id: str, container=Depends(get_container)) -> Response:
    container.room_service.delete_room(room_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@app.get("/rooms/{room_id}/devices", response_model=DeviceList)
def room_devices(room_id: str, container=Depends(get_container)) -> DeviceList:
    return DeviceList(
        devices=[
            DeviceState(id=device.device_id, name=device.name, status=device.status)
            for device in container.room_service.devices_in(room_id)
        ]
    )


@app.get("/schedules", response_model=ScheduleList)
def list_schedules(container=Depends(get_container)) -> ScheduleList:
    return ScheduleList(
        schedules=[_schedule_out(item) for item in container.schedule_service.list_schedules()]
    )


@app.get("/schedules/{schedule_id}", response_model=ScheduleOut)
def get_schedule(schedule_id: str, container=Depends(get_container)) -> ScheduleOut:
    return _schedule_out(container.schedule_service.get_schedule(schedule_id))


def _schedule_out(item) -> ScheduleOut:
    return ScheduleOut(
        id=item.id,
        device_id=item.device_id,
        action=item.action.value,
        time=item.time,
        days=list(item.days),
        enabled=item.enabled,
        timezone=item.timezone,
        last_run=item.last_run,
    )


@app.post("/schedules", response_model=ScheduleOut, status_code=http_status.HTTP_201_CREATED)
def create_schedule(payload: ScheduleCreate, container=Depends(get_container)) -> ScheduleOut:
    return _schedule_out(
        container.schedule_service.create_schedule(
            payload.device_id,
            PowerAction(payload.action),
            payload.time,
            tuple(payload.days),
            payload.enabled,
            payload.timezone,
        )
    )


@app.put("/schedules/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: str, payload: ScheduleUpdate, container=Depends(get_container)
) -> ScheduleOut:
    return _schedule_out(
        container.schedule_service.update_schedule(
            schedule_id,
            device_id=payload.device_id,
            action=PowerAction(payload.action) if payload.action else None,
            time=payload.time,
            days=tuple(payload.days) if payload.days is not None else None,
            enabled=payload.enabled,
            timezone_name=payload.timezone,
        )
    )


@app.post("/schedules/{schedule_id}/toggle", response_model=ScheduleOut)
def toggle_schedule(schedule_id: str, container=Depends(get_container)) -> ScheduleOut:
    current = container.schedule_service.get_schedule(schedule_id)
    return _schedule_out(
        container.schedule_service.update_schedule(
            schedule_id, enabled=not current.enabled
        )
    )


@app.delete("/schedules/{schedule_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: str, container=Depends(get_container)) -> Response:
    container.schedule_service.delete_schedule(schedule_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@app.post("/schedules/run-now")
def run_due_schedules(container=Depends(get_container)) -> dict[str, int]:
    return {"fired": len(container.schedule_service.run_due())}


@app.get("/rules", response_model=RuleList)
def list_rules(container=Depends(get_container)) -> RuleList:
    return RuleList(
        rules=[_rule_out(item) for item in container.automation_service.list_rules()]
    )


@app.get("/rules/{rule_id}", response_model=RuleOut)
def get_rule(rule_id: str, container=Depends(get_container)) -> RuleOut:
    return _rule_out(container.automation_service.get_rule(rule_id))


def _rule_out(item) -> RuleOut:
    return RuleOut(
        id=item.id,
        name=item.name,
        trigger_device_id=item.trigger_device_id,
        trigger_status=item.trigger_status.value,
        target_device_id=item.target_device_id,
        target_action=item.target_action.value,
        enabled=item.enabled,
        trigger_type=item.trigger_type.value,
        threshold_c=item.threshold_c,
    )


@app.post("/rules", response_model=RuleOut, status_code=http_status.HTTP_201_CREATED)
def create_rule(payload: RuleCreate, container=Depends(get_container)) -> RuleOut:
    return _rule_out(
        container.automation_service.create_rule(
            payload.name,
            payload.trigger_device_id,
            DeviceStatus(payload.trigger_status),
            payload.target_device_id,
            PowerAction(payload.target_action),
            payload.enabled,
            TriggerType(payload.trigger_type),
            payload.threshold_c,
        )
    )


@app.put("/rules/{rule_id}", response_model=RuleOut)
def update_rule(
    rule_id: str, payload: RuleUpdate, container=Depends(get_container)
) -> RuleOut:
    return _rule_out(
        container.automation_service.update_rule(
            rule_id,
            name=payload.name,
            trigger_device_id=payload.trigger_device_id,
            trigger_status=(
                DeviceStatus(payload.trigger_status)
                if payload.trigger_status
                else None
            ),
            target_device_id=payload.target_device_id,
            target_action=(
                PowerAction(payload.target_action) if payload.target_action else None
            ),
            enabled=payload.enabled,
            trigger_type=TriggerType(payload.trigger_type) if payload.trigger_type else None,
            threshold_c=payload.threshold_c,
        )
    )


@app.delete("/rules/{rule_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: str, container=Depends(get_container)) -> Response:
    container.automation_service.delete_rule(rule_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@app.get("/energy", response_model=EnergySummary)
def energy_summary(container=Depends(get_container)) -> EnergySummary:
    readings = container.energy_service.readings()
    return EnergySummary(
        total_wh=round(sum(item.energy_wh for item in readings), 4),
        devices=[
            EnergyDeviceOut(
                device_id=item.device_id,
                name=item.name,
                wattage=item.wattage,
                energy_wh=item.energy_wh,
            )
            for item in readings
        ],
    )


@app.get("/energy/logs", response_model=EnergyLogList)
def energy_logs(
    device_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    container=Depends(get_container),
) -> EnergyLogList:
    return EnergyLogList(
        logs=[
            EnergyLogOut(
                id=item.id,
                device_id=item.device_id,
                started_at=item.started_at,
                ended_at=item.ended_at,
                duration_seconds=round(item.duration_seconds, 3),
                wattage=item.wattage,
                estimated_energy_wh=round(item.estimated_energy_wh, 4),
                measurement_source=item.measurement_source,
            )
            for item in container.energy_service.logs(device_id, limit)
        ]
    )


@app.get("/energy/stats", response_model=EnergyStats)
def energy_statistics(container=Depends(get_container)) -> EnergyStats:
    logs = container.energy_service.logs(None, 500)
    total = round(sum(item.estimated_energy_wh for item in logs), 4)
    peak = max(logs, key=lambda item: item.estimated_energy_wh, default=None)
    return EnergyStats(
        total_wh=total,
        interval_count=len(logs),
        average_interval_wh=round(total / len(logs), 4) if logs else 0.0,
        peak_device_id=peak.device_id if peak else None,
    )


@app.get("/energy/{device_id}", response_model=EnergyDeviceOut)
def device_energy(device_id: str, container=Depends(get_container)) -> EnergyDeviceOut:
    item = container.energy_service.reading_for(device_id)
    return EnergyDeviceOut(
        device_id=item.device_id,
        name=item.name,
        wattage=item.wattage,
        energy_wh=item.energy_wh,
    )


@app.get("/activity", response_model=ActivityList)
def activity(
    device_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    source: Literal["api", "schedule", "automation", "system"] | None = Query(default=None),
    container=Depends(get_container),
) -> ActivityList:
    return ActivityList(
        activity=[
            ActivityOut(
                id=item.id,
                device_id=item.device_id,
                action=item.action,
                previous_status=item.previous_status,
                status=item.status,
                source=item.source.value,
                occurred_at=item.occurred_at,
            )
            for item in container.activity_service.list_events(device_id, limit, source)
        ]
    )


@app.get("/notifications", response_model=NotificationList)
def notifications(container=Depends(get_container)) -> NotificationList:
    service = container.notification_service
    return NotificationList(
        notifications=[_notification_out(item) for item in service.list_notifications()],
        unread_count=service.unread_count,
    )


def _notification_out(item) -> NotificationOut:
    return NotificationOut(
        id=item.id,
        message=item.message,
        level=item.level.value,
        read=item.read,
        created_at=item.created_at,
    )


@app.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def read_notification(
    notification_id: str, container=Depends(get_container)
) -> NotificationOut:
    return _notification_out(
        container.notification_service.mark_read(notification_id)
    )


@app.delete("/notifications/{notification_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: str, container=Depends(get_container)
) -> Response:
    container.notification_service.delete(notification_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@app.delete("/notifications", status_code=http_status.HTTP_204_NO_CONTENT)
def clear_notifications(container=Depends(get_container)) -> Response:
    container.notification_service.clear()
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@app.websocket("/ws")
async def realtime_feed(
    websocket: WebSocket, hub: RealtimeHub = Depends(get_realtime_hub)
) -> None:
    await hub.handle(websocket)

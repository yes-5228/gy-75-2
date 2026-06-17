from flask import Blueprint, jsonify, request

from app.services.repair_service import (
    InvalidStatusTransition,
    create_fault,
    create_tracking_log,
    list_faults,
    list_tracking_logs,
    statistics,
)

bp = Blueprint("repair", __name__)


@bp.get("/faults")
def faults():
    return {"items": list_faults()}


@bp.post("/faults")
def add_fault():
    return create_fault(request.get_json() or {}), 201


@bp.get("/tracking")
def tracking():
    fault_id = request.args.get("faultId", type=int)
    return {"items": list_tracking_logs(fault_id)}


@bp.post("/tracking")
def add_tracking():
    try:
        return create_tracking_log(request.get_json() or {}), 201
    except InvalidStatusTransition as exc:
        return jsonify({"error": str(exc), "current": exc.current, "target": exc.target, "allowed": exc.allowed}), 400


@bp.get("/statistics")
def repair_statistics():
    return statistics()

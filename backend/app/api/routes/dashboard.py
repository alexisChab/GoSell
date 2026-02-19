from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.schemas.dashboard import DashboardSummaryReadSchema
from app.crud.dashboard import get_dashboard_summary_for_user

dashboard_bp = Blueprint("dashboard", __name__)

_out = DashboardSummaryReadSchema()


@dashboard_bp.get("/dashboard/summary")
@jwt_required()
def dashboard_summary():
    user_id = int(get_jwt_identity())

    data = get_dashboard_summary_for_user(user_id=user_id)
    return jsonify(_out.dump(data)), 200
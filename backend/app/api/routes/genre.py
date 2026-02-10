# app/api/routes/genre.py
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.crud.genre import (
    get_genres,
    get_genre_by_id,
    create_genre,
    patch_genre,
    delete_genre,
)
from app.schemas.genre import (
    GenreReadSchema,
    GenreCreateSchema,
    GenrePatchSchema,
    GenreFilterSchema,
)

genre_bp = Blueprint("genre", __name__)

_genre_out = GenreReadSchema()
_genres_out = GenreReadSchema(many=True)

_genre_create_in = GenreCreateSchema()
_genre_patch_in = GenrePatchSchema()
_genre_filters_in = GenreFilterSchema()


@genre_bp.get("/genres")
@jwt_required()
def get_genres_route():
    _ = get_jwt_identity()  # juste pour forcer l'auth (même si genre est global)
    raw = request.args.to_dict(flat=True)
    filters = _genre_filters_in.load(raw)

    items = get_genres(filters)
    return jsonify(_genres_out.dump(items)), 200


@genre_bp.get("/genres/<int:genre_id>")
@jwt_required()
def get_genre_route(genre_id: int):
    _ = get_jwt_identity()

    item = get_genre_by_id(genre_id)
    if item is None:
        return jsonify({"ok": False, "error": "GENRE_NOT_FOUND"}), 404

    return jsonify(_genre_out.dump(item)), 200


@genre_bp.post("/genres")
@jwt_required()
def post_genre_route():
    _ = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _genre_create_in.load(payload)

    item = create_genre(
        intitule=data["intitule"],
        categorie_id=data["categorie_id"],
    )
    return jsonify(_genre_out.dump(item)), 201


@genre_bp.patch("/genres/<int:genre_id>")
@jwt_required()
def patch_genre_route(genre_id: int):
    _ = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _genre_patch_in.load(payload)

    item = patch_genre(genre_id, data)
    if item is None:
        return jsonify({"ok": False, "error": "GENRE_NOT_FOUND"}), 404

    return jsonify(_genre_out.dump(item)), 200


@genre_bp.delete("/genres/<int:genre_id>")
@jwt_required()
def delete_genre_route(genre_id: int):
    _ = get_jwt_identity()

    ok = delete_genre(genre_id)
    if not ok:
        return jsonify({"ok": False, "error": "GENRE_NOT_FOUND"}), 404

    # comme tes autres routes: soit 200 avec body, soit 204
    return jsonify({"ok": True, "deleted_genre_id": genre_id}), 200

from __future__ import annotations

from sqlalchemy import select
from app.db.deps import db
from app.models import User
from app.security.passwords import hash_password, verify_password, needs_rehash



class AppError(Exception):
    code: str = "ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConflictError(AppError):
    code = "CONFLICT"


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"


class NotFoundError(AppError):
    code = "NOT_FOUND"



def get_user_by_email(email: str) -> User | None:
    return db().execute(
        select(User).where(User.email == email)
    ).scalars().first()


def get_user_by_id(user_id: int) -> User | None:
    return db().get(User, user_id)


def require_user(user_id: int) -> User:
    user = get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    return user



def create_user(*, name: str, email: str, password: str, pro: bool = False) -> User:
    if get_user_by_email(email):
        raise ConflictError("Email already used")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        pro=pro,
    )
    db().add(user)
    db().flush()
    db().refresh(user)
    return user


def authenticate(*, email: str, password: str) -> User:
    user = get_user_by_email(email)
    if not user or not verify_password(password, user.password_hash):

        raise UnauthorizedError("Invalid credentials")


    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db().flush()

    return user


def update_user_profile(
    user_id: int,
    *,
    nom: str | None = None,
    pro: bool | None = None,
) -> user:
    user = require_user(user_id)

    if nom is not None:
        user.name = nom
    if pro is not None:
        user.pro = pro

    db().flush()
    db().refresh(user)
    return user


def change_password(user_id: int, *, old_password: str, new_password: str) -> None:
    user = require_user(user_id)

    if not verify_password(old_password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")

    user.password_hash = hash_password(new_password)
    db().flush()


def delete_user(user_id: int) -> None:
    user = require_user(user_id)
    db().delete(user)
    db().flush()


def list_users(*, limit: int = 50, offset: int = 0) -> list[User]:
    return db().execute(
        select(User).order_by(User.id).limit(limit).offset(offset)
    ).scalars().all()

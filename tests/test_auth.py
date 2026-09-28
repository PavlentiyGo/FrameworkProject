from auth import authorize_user
from models import User


def test_authorize_user_accepts_correct_credentials() -> None:
    user = User(1, "owner", "secret")

    assert authorize_user([user], "owner", "secret") is user


def test_authorize_user_rejects_wrong_password() -> None:
    user = User(1, "owner", "secret")

    assert authorize_user([user], "owner", "wrong") is None
    assert "secret" not in str(user)


from auth import authorize_user


def test_authorize_user_accepts_correct_credentials() -> None:
    assert authorize_user("owner", "secret", "owner", "secret")


def test_authorize_user_rejects_wrong_password() -> None:
    assert not authorize_user("owner", "secret", "owner", "wrong")

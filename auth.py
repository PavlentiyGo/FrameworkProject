from models import User


def authorize_user(
    users: list[User],
    entered_login: str,
    entered_password: str,
) -> User | None:
    for user in users:
        login_matches = user.login == entered_login
        password_matches = user.check_password(entered_password)
        if login_matches and password_matches:
            return user
    return None

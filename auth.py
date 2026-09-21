def authorize_user(
    saved_login: str,
    saved_password: str,
    entered_login: str,
    entered_password: str,
) -> bool:
    return (
        entered_login == saved_login
        and entered_password == saved_password
    )

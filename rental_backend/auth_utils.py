def authenticate_user(validated_token):
    """
    This function must return the user instance if valid,
    or raise an exception if invalid.
    """
    try:
        # simplejwt passes the user directly here
        if validated_token.is_active:
            return validated_token
        else:
            raise Exception("User account is not active")
    except AttributeError:
        raise Exception("Invalid token")
from itsdangerous import URLSafeTimedSerializer
from credentials import secret_key, security_password_salt

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt=security_password_salt)

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = serializer.loads(token, salt=security_password_salt,
            			 max_age=expiration)
    except:
        return False
    return email

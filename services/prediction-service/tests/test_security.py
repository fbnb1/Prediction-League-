from app.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("super-secret")
    assert hashed != "super-secret"
    assert verify_password("super-secret", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_token_roundtrip():
    token = create_token("usr_abc123")
    assert decode_token(token) == "usr_abc123"

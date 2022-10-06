from datetime import datetime
from os import environ, urandom
from jwcrypto.jws import JWS, JWK, json_encode, JWException   # type: ignore
from dotenv import load_dotenv
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt, InvalidKey, UnsupportedAlgorithm
from base64 import b64decode
from bases.JSONTokenBase import JSONTokenBase, Dict
from sqlite import init_db, get_user, add_demo_user

db = init_db(f"users.db")
add_demo_user(db)

load_dotenv()


class JSONToken(JSONTokenBase):
    token: JWS = JWS()
    __private_key: JWK
    public_key: JWK

    def __init__(self, private_key_path: str, public_key_path: str):
        super(JSONToken, self).__init__()
        self.__private_key = self.__load_private_key(
            path=private_key_path, passphrase=environ.get("PRIVATE_KEY_PASSPHRASE"))  # type: ignore
        self.public_key = self.__load_public_key(path=public_key_path)

    def __load_key(self, path: str, passphrase: str = None):
        jwk = JWK()
        f = open(file=path, mode="rb")
        data = f.read()
        f.close()
        pw: bytes | None = None
        if passphrase:
            pw = passphrase.encode("utf8")
        jwk.import_from_pem(data=data, password=pw)
        return jwk

    def __load_public_key(self, path: str):
        return self.__load_key(path)

    def __load_private_key(self, path: str, passphrase: str):
        return self.__load_key(path, passphrase)

    def sign(self, payload: Dict[str, str]) -> JWS:
        payload["nonce"] = urandom(32).hex()
        t = JWS(json_encode(payload))
        iat = datetime.utcnow().timestamp().__trunc__()
        t.add_signature(
            key=self.__private_key,
            alg=None,
            protected=json_encode({
                "alg": "EdDSA",
                "typ": "jwt",
                "iat": iat,
                "exp": iat + 3600,
                "nbf": iat - 120
            })
        )
        return t

    @staticmethod
    def verify(token_string: str, public_key: JWK) -> None:
        t = JWS()
        t.deserialize(raw_jws=token_string, key=public_key)
        now = datetime.utcnow().timestamp().__trunc__()
        headers = t.jose_header
        is_valid = False
        for x in headers:
            if x == "exp" and headers["exp"] < now:
                raise JWException("Token has expired")
            elif x == "exp" and headers["exp"] > now:
                is_valid = True
            if x == "nbf" and headers["nbf"] > now:
                raise JWException("Token is not yet valid")
            elif x == "nbf" and headers["nbf"] < now:
                is_valid = True
        if not is_valid:
            raise JWException("Headers did not pass validation")


def validate_credentials(username: str, password: str):
    encoded_hash = get_user(db, username)
    if not encoded_hash:
        return False
    algo, n, r, p, salt, key = encoded_hash.split(":")
    if algo != "SCRYPT":
        raise UnsupportedAlgorithm("Only SCRYPT is supported")
    key_len = len(b64decode(key))
    scrypt = Scrypt(b64decode(salt), key_len, int(n), int(r), int(p))
    try:
        scrypt.verify(password.encode("utf8"), b64decode(key))
        return True
    except InvalidKey:
        return False

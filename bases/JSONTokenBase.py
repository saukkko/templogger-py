from abc import ABC
from jwcrypto.jws import JWS, JWK  # type: ignore
from typing import Dict


class JSONTokenBase(ABC):
    __private_key: JWK
    __public_key: JWK
    token: JWS

    def __load_key(self, path: str, passphrase: str = None) -> JWK:
        pass

    def __load_private_key(self, path: str, passphrase: str) -> JWK:
        pass

    def __load_public_key(self, path: str) -> JWK:
        pass

    def sign(self, payload: Dict[str, str]) -> JWS:
        pass

    @staticmethod
    def verify(token_string: str, public_key: JWK) -> None:
        """
        verifies the token
        :param token_string:    raw jws token string
        :param public_key:      public key to verify the token against
        :raises JWKeyNotFound
        :raises InvalidJWSSignature
        :raises InvalidJWSObject
        :raises JWException
        """
        pass

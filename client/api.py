from __future__ import annotations
import requests
from typing import Optional, Dict, Any

class ApiError(RuntimeError):
    pass

class LicensingApi:
    def __init__(self, base_url: str, timeout: float = 8.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def register(self, email: str, password: str) -> None:
        r = requests.post(
            self._url("/auth/register"),
            json={"email": email, "password": password},
            timeout=self.timeout,
        )
        if r.status_code not in (200, 201):
            raise ApiError(f"register failed: {r.status_code} {r.text}")

    def login(self, email: str, password: str, hwid_hash: str) -> Dict[str, Any]:
        r = requests.post(
            self._url("/auth/login"),
            json={"email": email, "password": password, "hwid_hash": hwid_hash},
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise ApiError(f"login failed: {r.status_code} {r.text}")
        return r.json()

    def logout(self, token: str) -> None:
        r = requests.post(
            self._url("/auth/logout"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise ApiError(f"logout failed: {r.status_code} {r.text}")

    def get_product(self, product_code: str) -> Dict[str, Any]:
        r = requests.get(self._url(f"/products/{product_code}"), timeout=self.timeout)
        if r.status_code != 200:
            raise ApiError(f"get_product failed: {r.status_code} {r.text}")
        return r.json()

    def redeem_license(self, token: str, product_code: str, license_code: str, hwid_hash: str) -> Dict[str, Any]:
        r = requests.post(
            self._url("/license/redeem"),
            headers={"Authorization": f"Bearer {token}"},
            json={"product_code": product_code, "license_code": license_code, "hwid_hash": hwid_hash},
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise ApiError(f"redeem failed: {r.status_code} {r.text}")
        return r.json()

    def validate_license(self, token: str, product_code: str, hwid_hash: str) -> Dict[str, Any]:
        r = requests.post(
            self._url("/license/validate"),
            headers={"Authorization": f"Bearer {token}"},
            json={"product_code": product_code, "hwid_hash": hwid_hash},
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise ApiError(f"validate failed: {r.status_code} {r.text}")
        return r.json()

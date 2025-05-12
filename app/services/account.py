"""
Account service: maintains Suno account authentication, token refresh, and credit info.
"""
import threading
import time
from loguru import logger

from app.config import settings
from app.utils.http_client import do_request


class AccountService:
    """
    Singleton service to manage Suno account credentials and keep-alive.
    """
    def __init__(self):
        self.session_id = settings.session_id
        self.cookie = settings.cookie
        self.jwt: str = ""
        self.last_update: float = 0.0
        self.credits_left: int = 0
        self.monthly_limit: int = 0
        self.monthly_usage: int = 0
        self.period: str = ""
        self.is_active: bool = False

    def update_token(self) -> None:
        """
        Exchange session token for JWT and refresh cookies, then update credit info.
        """
        if not self.cookie or not self.session_id:
            raise RuntimeError("Session ID and COOKIE must be set")
        url = settings.exchange_token_url.format(self.session_id)
        headers = {"Cookie": self.cookie, "Content-Type": "application/x-www-form-urlencoded"}
        resp = do_request("POST", url, headers=headers)
        data = resp.json()
        # Update JWT
        self.jwt = data.get("jwt", "")
        # Merge Set-Cookie headers
        set_cookies = resp.headers.get_list("set-cookie") if hasattr(resp.headers, 'get_list') else resp.headers.get_all("set-cookie", default=[])
        cookies = {kv.split("=")[0].strip(): kv.split("=")[1].strip() for cookie in set_cookies for kv in [cookie.split(";", 1)[0]] if "=" in kv}
        # Parse existing cookies
        for part in self.cookie.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookies.setdefault(k, v)
        # Rebuild cookie string
        self.cookie = "; ".join(f"{k}={v}" for k, v in cookies.items())
        # Update credit info
        self.get_credits()
        self.last_update = time.time()

    def get_credits(self) -> None:
        """
        Retrieve billing info from Suno billing endpoint.
        """
        url = f"{settings.base_url}/api/billing/info/"
        headers = {"Authorization": f"Bearer {self.jwt}", "Content-Type": "application/json"}
        resp = do_request("GET", url, headers=headers)
        info = resp.json()
        self.credits_left = int(info.get("credits_left", 0))
        self.monthly_limit = int(info.get("monthly_limit", 0))
        self.monthly_usage = int(info.get("monthly_usage", 0))
        self.period = info.get("period", "")
        self.is_active = bool(info.get("is_active", False))

    def keep_alive_loop(self) -> None:
        """
        Background loop to refresh token periodically.
        """
        while True:
            try:
                self.update_token()
            except Exception as e:
                logger.error(f"Suno Keep-alive failed: {e}")
            time.sleep(5)

    def get_account_info(self) -> dict:
        """
        Return current account credentials and usage info.
        """
        return {
            "session_id": self.session_id,
            "cookie": self.cookie,
            "jwt": self.jwt,
            "last_update": self.last_update,
            "credits_left": self.credits_left,
            "monthly_limit": self.monthly_limit,
            "monthly_usage": self.monthly_usage,
            "period": self.period,
            "is_active": self.is_active,
        }

# Singleton instance
account_service = AccountService()

def start_account_keepalive():
    """
    Start background thread for token refresh.
    """
    thread = threading.Thread(target=account_service.keep_alive_loop, daemon=True)
    thread.start()
import arrow
import base64
import hashlib
import requests

from functools import cached_property
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_time(ts):
    return arrow.get(ts).to("Asia/Shanghai")


class JiushiAuth(requests.auth.AuthBase):
    def __init__(self, app_id, sign_key):
        self.app_id = app_id
        self.sign_key = sign_key

    def __call__(self, req):
        hexdigest = hashlib.md5(req.body + self.sign_key).hexdigest()
        js_sign = base64.b64encode(hexdigest.encode("UTF-8")).decode("UTF-8")
        req.headers.update({
            "gw_channel": "api",
            "app_id": self.app_id,
            "js_sign": js_sign
        })
        return req


class JiushiClient(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="JS_",
        extra="ignore"
    )

    app_id: str
    sign_key: bytes

    @cached_property
    def session(self):
        session = requests.session()
        session.auth = JiushiAuth(self.app_id, self.sign_key)
        return session

    def call(self, api, data):
        resp = self.session.post(
            f"https://jsapp.jussyun.com/jiushi-core/venue{api}",
            json=data
        )
        result = resp.json()
        return result["data"]

    def get_venue_book_time(self, venue_id):
        result = self.call("/getVenueBookTime", {"venueId": venue_id})
        return result

    def get_venue_hours(self, venue_id, date):
        date = arrow.get(date).replace(tzinfo="Asia/Shanghai")
        ts = date.int_timestamp * 1000
        result = self.call(
            "/getVenueGround",
            {"venueId": venue_id, "bookTime": ts},
        )
        out = []
        for status in result["statusList"]:
            interval = int(status["minHour"])
            start = get_time(int(status["startTime"]))
            end = get_time(int(status["endTime"]))

            for ground in status["blockModel"]:
                for hour in range(start.hour, end.hour, interval):
                    out.append({
                        "date": date.date(),
                        "venue_id": venue_id,
                        "ground_id": int(ground["groundId"]),
                        "ground_name": ground["groundName"],
                        "hour": hour,
                        "available": ground["status"] == "1",
                        "price": float(ground["price"]),
                    })
        return out

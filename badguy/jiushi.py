import arrow
import aiohttp
import base64
import json
import hashlib

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_time(ts):
    return arrow.get(ts).to("Asia/Shanghai")


class JiushiClient(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="JS_",
        extra="ignore"
    )

    app_id: str
    sign_key: bytes

    async def call(self, api, payload):
        data = json.dumps(payload).encode("UTF-8")
        hexdigest = hashlib.md5(data + self.sign_key).hexdigest()
        js_sign = base64.b64encode(hexdigest.encode("UTF-8")).decode("UTF-8")

        headers = {
            "content-type": "application/json",
            "gw_channel": "api",
            "app_id": self.app_id,
            "js_sign": js_sign
        }
        url = f"https://jsapp.jussyun.com/jiushi-core/venue{api}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as resp:
                result = await resp.json()
        return result["data"]

    async def get_venue_book_time(self, venue_id):
        result = await self.call("/getVenueBookTime", {"venueId": venue_id})
        return result

    async def get_venue_hours(self, venue_id, date):
        date = arrow.get(date).replace(tzinfo="Asia/Shanghai")
        ts = date.int_timestamp * 1000
        result = await self.call(
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

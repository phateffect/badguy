import requests

from pydantic_settings import BaseSettings, SettingsConfigDict


class DingTalk(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DING_",
        extra="ignore"
    )

    token: str

    def send(self, content):
        resp = requests.post(
            "https://oapi.dingtalk.com/robot/send",
            params={"access_token": self.token},
            json={"msgtype": "text", "text": {"content": content}}
        )

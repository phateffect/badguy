import arrow
import click
import requests
import tomli

from pathlib import Path


base_url = "https://jsapp.jussyun.com/jiushi-core/venue"
cfg = tomli.load(open("config.toml", "rb"))

session = requests.session()
session.headers.update(cfg["headers"])


def execute(req):
    resp = session.post(
        f"{base_url}/{req['method']}",
        headers=req.get("headers", {}),
        data=req["data"]
    )
    return resp.json()["data"]


def list_dates():
    result = execute(cfg["list"])
    book_list = result["venueBookModelList"]
    for element in book_list:
        date = arrow.get(int(element["date"])).to("Asia/Shanghai").format("YYYY-MM-DD")
        file = Path(f"dates/{date}.txt")
        if file.is_file():
            pass
        else:
            send(date)
            file.touch()


def send(date):
    resp = requests.post(
        "https://oapi.dingtalk.com/robot/send",
        params=cfg["dingtalk"]["params"],
        json={"msgtype": "text", "text": {"content": f"可以订 {date} 的场子了"}}
    )
    print(resp.json())


list_dates()

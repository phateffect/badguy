import arrow
import asyncio
import click

from itertools import product

from .db import Database
from .jiushi import JiushiClient
from .dingtalk import DingTalk

db = Database()
js = JiushiClient()
ding = DingTalk()


@click.group()
def cli():
    pass


async def aget_hours(venue_ids, dates):
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(js.get_venue_hours(venue_id, date))
            for venue_id, date in product(venue_ids, dates)
        ]
    return [hour for task in tasks for hour in task.result()]


@cli.command()
@click.option("--venue-ids", prompt=True)
@click.option("--date")
def update_ground_hours(venue_ids, date):
    venue_ids = [
        int(vid.strip())
        for vid in venue_ids.split(",")
        if vid.strip()
    ]
    if date is None:
        now = arrow.now()
        days = 8 if now.hour >= 12 else 7
        dates = [now.shift(days=n).date() for n in range(days)]
    else:
        dates = [arrow.get(date).date()]

    hours = asyncio.run(aget_hours(venue_ids, dates))

    with db.connect() as conn:
        db.upsert_ground_hours(conn, hours)


@cli.command()
@click.option("--hours", prompt=True)
def find(hours):
    hours = [int(h.strip()) for h in hours.split(",") if h.strip()]
    with db.connect() as conn:
        for result in db.find_venue(conn, hours):
            tip = [
                "漏网之鱼",
                f"{result.date}/周{result.date.isoweekday()}: {result.hours}"
            ]
            for hour, ground in result.get_best():
                tip.append(f"{hour:02}:\t{ground}")
            content = "\n".join(tip)

            if db.update_notification(conn, result.key, content):
                continue
            ding.send(content)


if __name__ == "__main__":
    cli()

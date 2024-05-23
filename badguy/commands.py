import arrow
import click

from itertools import product

from .db import Database
from .jiushi import JiushiClient

db = Database()
js = JiushiClient()


@click.group()
def cli():
    pass


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

    for venue_id, date in product(venue_ids, dates):
        hours = js.get_venue_hours(venue_id, date)
        print(venue_id, date, len([h for h in hours if h["available"]]))



if __name__ == "__main__":
    cli()

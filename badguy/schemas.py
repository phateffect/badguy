import datetime
import uuid

from collections import Counter, defaultdict
from pydantic import BaseModel


class GroundResult(BaseModel):
    hour: int
    name: str


class VenueResult(BaseModel):
    key: uuid.UUID
    venue_id: int
    date: datetime.date
    hours: list[int]
    grounds: list[GroundResult]

    def get_best(self):
        best = []
        by_hour = defaultdict(lambda: [])
        by_name = Counter()
        for gr in self.grounds:
            by_hour[gr.hour].append(gr.name)
            by_name[gr.name] += 1
        for hour in self.hours:
            for name, __ in by_name.most_common():
                if name in by_hour[hour]:
                    best.append((hour, name))
                    break
        return best

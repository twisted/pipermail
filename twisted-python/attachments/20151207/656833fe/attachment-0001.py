import re
from yaml import safe_dump
from twisted.python.versions import Version

with open('NEWS') as news:
    lines = news.readlines()

versions = {}
current_version = None

for line in lines:
    matches = re.match(r"(?:Twisted )?[A-Z][a-z]+ ([0-9]+).([0-9]+).([0-9]+) \(([0-9]{4,4}-[0-9]{2,2}-[0-9]{2,2})\)", line)
    if matches:
        major, minor, micro, date = matches.groups()
        version_number = Version('Twisted', int(major), int(minor), int(micro))
        current_version = versions.setdefault((major, minor, micro), dict(
            number=version_number,
            date=date,
            tickets=set(),
        ))

    if current_version is not None:
        matches = re.findall(r"#([0-9]+)", line)
        current_version['tickets'].update(map(int, matches))


# for _1, v1 in versions.items():
#     for _2, v2 in versions.items():
#         if v1 is v2: continue
#         int = v1.tickets.intersection(v2.tickets)
#         if int: print int, _1, _2

for version  in sorted(versions.values(), key=lambda _:_['number']):
    print "{number} ({date}):".format(number=version['number'].short(), date=version['date'])
    for ticket in sorted(version['tickets']):
        print " - #{ticket}".format(ticket=ticket)

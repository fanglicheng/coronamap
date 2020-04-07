#!/usr/bin/env python3

import csv
from copy import deepcopy
import json

ENTRIES = []

class Entry:
    def __init__(self, line):
        (self.date,
         self.county,
         self.state,
         self.fips,
         self.cases,
         self.deaths) = line
        self.cases = int(self.cases)
        self.deaths = int(self.deaths)

    def __str__(self):
        return '%s %s %s %s' % (self.date, self.county, self.state, self.cases)


def maybe_new_york(entry):
    if entry.county == 'New York City':
        for name, fips in [('Richmond', '36085'), ('Kings', '36047'), ('Queens',
            '36081'), ('Bronx', '36005'), ('New York', '36061')]:
            e = deepcopy(entry)
            e.county = name
            e.fips = fips
            yield e
    else:
        yield entry


def entries():
    if ENTRIES:
        for e in ENTRIES:
            yield e
    else:
        with open('../us-counties.csv') as f:
            reader = csv.reader(f)
            for i, line in enumerate(reader):
                if i == 0:
                    continue
                entry = Entry(line)
                for e in maybe_new_york(entry):
                    ENTRIES.append(e)
                    yield e


def latest():
    fips = {}
    for entry in entries():
        fips[entry.fips] = entry
    return fips


def top(k=10):
    return [x[0] for x in sorted(
        latest().items(), key=lambda x: - x[1].cases)[:k]]


def increase(entries):
    last = 0
    for entry in entries:
        if last == 0:
            rate = float('inf')
        else:
            rate = float(entry.cases)/last - 1
        yield entry, rate
        last = entry.cases


def trend():
    result = {}
    for fips in latest().keys():
        s = ''
        for e, rate in list(increase([
            e for e in entries() if e.fips == fips]))[-10:]:
            s += '<br>%s %s %2.f%%' % (e.date, e.cases, rate*100)
        result[fips] = s
    return result


for fips in top(5):
    print()
    for entry, rate in increase([entry for entry in entries()
        if entry.fips == fips]):
        print(entry, '%2.f%%' % (rate*100))


Brackets = [(1, 9), (10, 99), (100, 999), (1000, 9999), (10000, 99999)]


def bracket(n):
    for i, (low, high) in enumerate(Brackets):
        if low <= n <= high:
            return i


def fips_bracket():
    for f, e in latest().items():
        yield f, bracket(e.cases)


def bracket_fips():
    # Prefill all brackets so that empty lists are included.
    result = {i : [] for i in range(len(Brackets))}
    for f, b in fips_bracket():
        if b is None:
            print('Warning: bad bracket')
            continue
        result[b].append(f)
    return result


def write_js():
    s = open('map-base.js').read()
    s += ('\nCountyColor = %s\nLatest = %s\nTrend = %s' %
            (bracket_fips(),
             latest(), 
             trend()))
    with open('map.js', 'w') as f:
        f.write(s)
    print('js written.')


latest_cases = latest()


def write_geojson():
    with open('gz_2010_us_050_00_20m.json', encoding='ISO-8859-1') as fin:
        data = json.load(fin)
        for f in data['features']:
            p = f['properties']
            fips = p['GEO_ID'][-5:]
            entry = latest_cases.get(fips)
            p['cases'] = latest_cases[fips].cases if entry else 0

        with open('county-cases.json', 'w') as fout:
            json.dump(data, fout)
    print('geojson written.')


write_geojson()

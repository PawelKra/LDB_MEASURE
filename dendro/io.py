"""File-format registry for tree-ring data.

Every format is a ``Format(reader, writer, multi)``:

    reader(path)               -> {name: Sequence}
    writer(path, {name: Seq})  -> None
    multi                      -> True  one file holds many series (fh, rwl,
                                        csv, json)
                                  False one series per file (pos, avr, txt)

The readers / writers themselves stay in ``classes.py``; this module only
adapts their signatures to the uniform contract and lets load / save
dispatch by extension instead of an ``if ext == ...`` ladder.
"""
import csv
import json
import os

import classes


class Format:
    __slots__ = ('reader', 'writer', 'multi')

    def __init__(self, reader=None, writer=None, multi=False):
        self.reader = reader
        self.writer = writer
        self.multi = multi


_REGISTRY = {}


def register(ext, reader=None, writer=None, multi=False):
    _REGISTRY[ext.lstrip('.').lower()] = Format(reader, writer, multi)


def format_for(ext):
    return _REGISTRY.get(ext.lstrip('.').lower())


def readable_extensions():
    return sorted(e for e, f in _REGISTRY.items() if f.reader)


def writable_extensions():
    return sorted(e for e, f in _REGISTRY.items() if f.writer)


def read(path):
    '''Read one file into {name: Sequence}, dispatching on its extension.'''
    fmt = format_for(os.path.splitext(path)[1])
    if fmt is None or fmt.reader is None:
        raise ValueError('no reader registered for %r' % path)
    return fmt.reader(path)


def write(path, sequences):
    '''Write {name: Sequence} to one file, dispatching on its extension.'''
    fmt = format_for(os.path.splitext(path)[1])
    if fmt is None or fmt.writer is None:
        raise ValueError('no writer registered for %r' % path)
    fmt.writer(path, sequences)


# --- adapters over the classes.py readers / writers --------------------

def _read_fh_one(path):
    return classes.read_fh([path])


def _one_series_writer(fn):
    '''Wrap a single-Sequence writer so it takes {name: Sequence}.'''
    def _w(path, sequences):
        seqs = list(sequences.values())
        if seqs:
            fn(path, seqs[0])
    return _w


# --- year x sample exports (S4.2) ------------------------------------

def _year_matrix(sequences):
    seqs = list(sequences.values())
    lo = min(s.DateBegin() for s in seqs)
    hi = max(s.DateEnd() for s in seqs)
    names = [s.KeyCode() for s in seqs]
    rows = []
    for year in range(lo, hi + 1):
        row = [year]
        for s in seqs:
            v = s.measure_from_year(year)
            row.append('' if v is False else v)
        rows.append(row)
    return names, rows


def write_csv(path, sequences):
    '''Wide table: a `year` column plus one column per series.'''
    names, rows = _year_matrix(sequences)
    with open(path, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['year'] + names)
        w.writerows(rows)


def write_json(path, sequences):
    '''{name: {DateBegin, measurements, <other metadata>}} - round-trippable.'''
    out = {}
    for name, s in sequences.items():
        rec = {k: v for k, v in s.sample.items() if k not in s.forb_keys}
        rec['DateBegin'] = s.DateBegin()
        rec['measurements'] = list(s.measurements())
        out[name] = rec
    with open(path, 'w') as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write('\n')


def read_json(path):
    with open(path) as fh:
        data = json.load(fh)
    return {name: classes.Sequence(dict(rec)) for name, rec in data.items()}


# --- built-in registrations ----------------------------------------

register('fh', reader=_read_fh_one, writer=classes.write_fh, multi=True)
register('rwl', reader=classes.read_rwl, writer=classes.write_rwl, multi=True)
register('pos', reader=classes.read_pos, multi=False)
register('txt', writer=_one_series_writer(classes.write_txt), multi=False)
for _e in ('avr', 'av0', 'avs', 'r', 'r0', 'r1', 'r2', 'r3'):
    register(_e, reader=classes.read_r,
             writer=_one_series_writer(classes.write_r), multi=False)
register('csv', writer=write_csv, multi=True)
register('json', reader=read_json, writer=write_json, multi=True)

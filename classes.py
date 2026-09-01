from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import logging
import os
import math
import struct
import numpy as np

logger = logging.getLogger(__name__)


def _intlike(v):
    '''True if v is an int or a string of one - accepts a leading '-', unlike
    str.isdigit(), so BC / negative calendar years are allowed.'''
    try:
        int(v)
    except (TypeError, ValueError):
        return False
    return True


def _year_at_offset(begin, offset):
    '''The calendar year `offset` rings after the year `begin`.

    There is no year 0: 1 BC (== -1) is immediately followed by 1 AD (== 1),
    so a span that crosses the era boundary skips the 0 slot.
    '''
    y = begin + offset
    if begin < 0 and y >= 0:
        y += 1
    return y


def _offset_of_year(year, begin):
    '''Ring index of calendar `year` in a series starting at `begin` -
    the inverse of _year_at_offset (year 0 does not exist).'''
    off = year - begin
    if begin < 0 < year:
        off -= 1
    return off


def year_span(begin, length):
    '''The `length` consecutive calendar years starting at `begin`, skipping
    the non-existent year 0.'''
    return [_year_at_offset(begin, k) for k in range(length)]


def shift_year(year, delta):
    '''Move `year` by `delta` calendar years, stepping over the missing
    year 0 (so shift_year(1, -1) == -1 and shift_year(-1, 1) == 1).'''
    y = year + delta
    if year < 0 <= y:
        y += 1
    elif year > 0 >= y:
        y -= 1
    return y


def _fast_r(x, y):
    '''Pearson r of two equal-length float64 arrays.

    Returns nan for a degenerate input (too short, or a zero-variance /
    constant series) without going through numpy's divide-by-zero
    RuntimeWarning - pytest.ini turns those into errors.
    '''
    if x.shape[0] < 2:
        return float('nan')
    xm = x - x.mean()
    ym = y - y.mean()
    sxy = np.dot(xm, ym)
    sxx = np.dot(xm, xm)
    syy = np.dot(ym, ym)
    denom = sxx * syy
    if denom <= 0.0:
        return float('nan')
    return float(sxy / math.sqrt(denom))


def _standardize(meas):
    '''Build the offset-independent derived series for one measurement list.

    Returns (raw, BP, H, GLK) as float64 / int64 arrays, bit-compatible with
    the per-element loop it replaces:
      raw  - measurements as float64
      BP   - Baillie-Pilcher: log(ring / centred 5-yr mean), [0, 0]-padded
      H    - Hollstein: log10(ring / next ring)
      GLK  - 1 where the next ring is >= the current one
    '''
    f = np.asarray(meas, dtype=np.float64)
    n = f.shape[0]

    if n >= 5:
        win = f[:-4] + f[1:-3] + f[2:-2] + f[3:-1] + f[4:]
        bp = np.concatenate(([0.0, 0.0], np.log(5.0 * f[2:-2] / win)))
    else:
        bp = np.zeros(2, dtype=np.float64)

    if n >= 2:
        h = np.log(f[:-1] / f[1:]) / np.log(10.0)
        g = (np.diff(f) >= 0).astype(np.int64)
    else:
        h = np.zeros(0, dtype=np.float64)
        g = np.zeros(0, dtype=np.int64)

    return f, bp, h, g


def _stats_row(cc_ab, r_bp, r_h, n_raw, n_bp, n_h, glk, dl_a):
    '''Assemble one result row [crosscoef, TBP, TH, T, GLK, GSL, CDI] from the
    raw / BP / H Pearson coefficients and the GLK count: t-values via _T, the
    GLK percentage, the Eckstein-Bauch GSL stars, the 0.00001 no-overlap
    sentinel and the TSAP CDI. Shared by corellate and corellate_position.
    '''
    row = [
        round(cc_ab, 2),
        round(_T(n_bp, r_bp), 1),
        round(_T(n_h, r_h), 1),
        round(_T(n_raw, cc_ab), 1),
    ]

    if glk > 0:
        glkr = round((float(glk) / (n_raw - 1)) * 100)
        row.append(glkr)
        fr1 = 50 + (82.7 / math.sqrt(n_raw))
        fr2 = 50 + (116.3 / math.sqrt(n_raw))
        fr3 = 50 + (154 / math.sqrt(n_raw))
        if fr1 <= glkr < fr2:
            row.append("*")
        elif fr2 <= glkr < fr3:
            row.append("**")
        elif glkr >= fr3:
            row.append("***")
        else:
            row.append("")
    else:
        row.append(0.00001)
        row.append("")

    row.append(int(cdi(row[4], n_raw, dl_a, row[1], row[2])))
    return row


def _prefix(v):
    '''[0, cumsum(v)...] - length len(v) + 1, so a window sum over [beg, end)
    is prefix[end] - prefix[beg].'''
    out = np.empty(v.shape[0] + 1, dtype=np.float64)
    out[0] = 0.0
    np.cumsum(v, out=out[1:])
    return out


def _r_curve(n, sx, sxx, sy, syy, sxy):
    '''Pearson r for every lag from centred window moments (arrays).

    A zero-variance window (constant rings) has no defined correlation and
    comes back as nan. Catastrophic cancellation can leave such a window's
    variance product a hair below zero, so guard the sqrt / divide rather
    than let numpy raise a RuntimeWarning (pytest.ini promotes those to
    errors); see test_corellate_edge.'''
    cov = np.asarray(sxy - sx * sy / n, dtype=np.float64)
    vx = sxx - sx * sx / n
    vy = syy - sy * sy / n
    denom = np.asarray(vx * vy, dtype=np.float64)
    r = np.full(denom.shape, np.nan)
    ok = denom > 0.0
    r[ok] = cov[ok] / np.sqrt(denom[ok])
    return r


def _offset_curves(af, bf, bpa, bpb, ha, hb, ga, gb, lags):
    '''Vectorised replacement for the per-offset loop of corellate().

    For every lag in `lags` (b-index = a-index + lag) return arrays
    (r_raw, r_bp, r_h, glk, m, ovl). The three Pearson curves come from one
    np.correlate per metric plus prefix sums; GLK from a binary
    cross-correlation. Inputs are the _standardize() outputs of each series.
    '''
    na, nb = af.shape[0], bf.shape[0]

    # aligned windows - the four alignment cases of the original code reduce
    # to this (verified against the case-by-case beg/end/ovl)
    beg_a = np.maximum(0, -lags)
    end_a = np.minimum(na, nb - lags)
    beg_b = np.maximum(0, lags)
    m = end_a - beg_a
    # ovl == m everywhere except case III (sample strictly inside a longer
    # ref, shifted right), where the original reports m - 1
    ovl = m - ((lags > 0) & (na + lags - 1 < nb)).astype(np.int64)

    # centre each series once (global mean) - keeps the moment sums well
    # conditioned; the additive constant cancels in a Pearson r
    afc, bfc = af - af.mean(), bf - bf.mean()
    bpac, bpbc = bpa - bpa.mean(), bpb - bpb.mean()
    hac, hbc = ha - ha.mean(), hb - hb.mean()

    # --- raw: window is exactly the natural a/b overlap ---
    ca, ca2 = _prefix(afc), _prefix(afc * afc)
    cb, cb2 = _prefix(bfc), _prefix(bfc * bfc)
    xr = np.correlate(afc, bfc, mode='full')
    sx, sxx = ca[end_a] - ca[beg_a], ca2[end_a] - ca2[beg_a]
    sy, syy = cb[beg_b + m] - cb[beg_b], cb2[beg_b + m] - cb2[beg_b]
    r_raw = _r_curve(m, sx, sxx, sy, syy, xr[nb - 1 - lags])

    # --- H: window is also the natural overlap, one shorter ---
    n_h = m - 1
    cha, cha2 = _prefix(hac), _prefix(hac * hac)
    chb, chb2 = _prefix(hbc), _prefix(hbc * hbc)
    xh = np.correlate(hac, hbc, mode='full')
    sx, sxx = cha[beg_a + n_h] - cha[beg_a], cha2[beg_a + n_h] - cha2[beg_a]
    sy, syy = chb[beg_b + n_h] - chb[beg_b], chb2[beg_b + n_h] - chb2[beg_b]
    r_h = _r_curve(n_h, sx, sxx, sy, syy, xh[nb - 2 - lags])

    # --- BP: natural overlap minus its first two positions (the [0,0] pad /
    #     the 2 rings BP cannot use); subtract those two products by hand ---
    n_bp = m - 4
    cba, cba2 = _prefix(bpac), _prefix(bpac * bpac)
    cbb, cbb2 = _prefix(bpbc), _prefix(bpbc * bpbc)
    xb = np.correlate(bpac, bpbc, mode='full')
    lo_a, lo_b = beg_a + 2, beg_b + 2
    sx, sxx = cba[lo_a + n_bp] - cba[lo_a], cba2[lo_a + n_bp] - cba2[lo_a]
    sy, syy = cbb[lo_b + n_bp] - cbb[lo_b], cbb2[lo_b + n_bp] - cbb2[lo_b]
    drop = (bpac[beg_a] * bpbc[beg_b] +
            bpac[beg_a + 1] * bpbc[beg_b + 1])
    r_bp = _r_curve(n_bp, sx, sxx, sy, syy, xb[nb - 3 - lags] - drop)

    # --- GLK: agreements = (m-1) - Σga - Σgb + 2 Σ ga·gb ---
    gaf, gbf = ga.astype(np.float64), gb.astype(np.float64)
    cga, cgb = _prefix(gaf), _prefix(gbf)
    xg = np.correlate(gaf, gbf, mode='full')
    sga = cga[beg_a + n_h] - cga[beg_a]
    sgb = cgb[beg_b + n_h] - cgb[beg_b]
    glk = np.rint(n_h - sga - sgb + 2.0 * xg[nb - 2 - lags]).astype(np.int64)

    return r_raw, r_bp, r_h, glk, m, ovl


def read_fh(arg):  # noqa
    '''
    Fuction to read measurements from fh file and put it in Sequence object
    arg - list of paths to files
    Returns dict with Sequence objects
    '''

    # Which part of sample we in:
    # 0-first sample, 1-HEADER, 2-DATA
    partOfSample = 0
    # header definition of measurement part with data formating
    dataTypeLine = {
        "DATA:HalfChrono": 2, "DATA:Tree": 1, "DATA:Chrono": 3,
        "DATA:Quadro": 3, "DATA:Single": 1, "DATA:Double": 2}

    MeasureType = ''  # data type from dataTypeLine
    # which part of sample
    #  0 - outside sample
    #  1 - in header section
    #  2 - in measuremetn section
    partOfSample = 0

    meas_list = []  # measurements
    seq_dict = {}  # dict with ready Sequence objects
    beginTrig = 0  # trigg for avoid first line of definition
    dateEnd = 1  # date end to set in last moment

    for fn in arg:
        with open(fn, 'r') as meas_file:
            file_lines = meas_file.readlines()

        for line in file_lines:
            line = line.rstrip('\r\n\t ')

            if len(line) > 0:
                if line == 'HEADER:' and \
                        (partOfSample == 0 or partOfSample == 1):
                    # '0' new sample - set all meta to defaluts
                    # '1' sample without meas. ignore readed metadatas
                    sample = Sequence()
                    sample.source = fn  # set meas_file path in metadatas
                    partOfSample = 1
                    beginTrig = 1

                if line == 'HEADER:' and partOfSample == 2:
                    # new sample starts, old will be added to dict

                    partOfSample = 1
                    sample.update_measurements(meas_list)
                    meas_list = []
                    # add previosu sample to dict, no duplicate in dict
                    if sample.KeyCode() not in seq_dict.keys():
                        sample.setDateEnd(dateEnd)
                        seq_dict[sample.KeyCode()] = sample

                    # duplicate, or another sample with this name in dict, add
                    # number in brackets to avoid confilcts
                    else:
                        uniqe = False
                        i = 0
                        while uniqe is False:
                            i += 1
                            new_keycode = sample.KeyCode() + "(" + str(i) + ")"
                            if new_keycode not in seq_dict.keys():
                                # update sample name and add it to dict
                                logger.info(
                                    "renamed duplicate sample to %s",
                                    new_keycode)
                                sample.set_meta("KeyCode", new_keycode)
                                seq_dict[sample.KeyCode()] = sample
                                uniqe = True

                    # set new Sequence object
                    sample = Sequence()
                    sample.source = fn  # add meas_file path to meta
                    beginTrig = 1

                if line in dataTypeLine.keys() and partOfSample == 1:
                    # measurement section
                    MeasureType = dataTypeLine[line]  # check data type
                    meas_list = []   # list with measuremetns
                    partOfSample = 2
                    beginTrig = 1

                if partOfSample == 1 and beginTrig == 0:
                    # read metadata to Sequence object
                    lin = line.split('=')
                    if lin[0] == "DateEnd":
                        # sample.setDateEnd(int(lin[1]))
                        dateEnd = int(lin[1])
                    else:
                        sample.set_meta(str(lin[0]), str(lin[1]))

                if partOfSample == 2 and beginTrig == 0:
                    # if there is less than 5 signs in line one measurement per
                    # line
                    if len(line) < 5:
                        if int(line) != 0 and line.isdigit():
                            meas_list.append(int(line))
                    else:
                        ml = line.split(' ')
                        ml = list(filter(lambda a: a != '', ml))

                        # diffrent types of saving for tree, halfchrono and
                        # chrono, for details go to rinntech tsap manual
                        if MeasureType == 1:
                            for measure in ml:
                                if int(measure) != 0 and measure.isdigit():
                                    meas_list.append(int(measure))

                        elif MeasureType == 2:
                            for m in range(len(ml)):
                                if m % 2 == 0 and int(ml[m]) != 0 and \
                                        ml[m].isdigit():
                                    meas_list.append(int(ml[m]))

                        elif MeasureType == 3:
                            for m in range(len(ml)):
                                if m % 4 == 0 and int(ml[m]) != 0 and \
                                        ml[m].isdigit():
                                    meas_list.append(int(ml[m]))
                beginTrig = 0

    sample.update_measurements(meas_list)  # dopisujemy measurement
    seq_dict[str(sample.KeyCode())] = sample

    return seq_dict


def read_pos(fn):
    '''
    Read measurements from pos file and and puts them to Sequence object
    fn - path to file
    '''
    sample = Sequence()
    first = []
    dateEnd = 0
    measurements = []

    with open(fn, 'r') as pos_file:
        pos_lines = pos_file.readlines()

    for line in pos_lines:
        line = line.rstrip('\r\n')
        if line.split(" ")[0] == "#DPI":
            sample.set_meta('DPI', line.split(" ")[1].split((","))[0])
        if line.split(" ")[0] == "#Imagefile":
            sample.set_meta(
                'KeyCode',
                line.split(" ")[-1].rstrip("\r\n").split(os.sep)[-1])

        lin_split = line.split(" ")
        if len(lin_split) > 1:
            if lin_split[1] == "DATED":
                dateEnd = int(line.split(" ")[-1])

        line = line.replace("D", "")
        line = line.replace(" #%gap", "")
        if line[0].isdigit():
            measurement = line.split("  ")
            w = measurement[0].split(",")
            w = list(map(float, w))
            if len(measurement) == 1:
                if len(first) != 0:
                    measurements.append(
                        int(math.sqrt(
                            (first[0] - w[0])**2 + (first[1] - w[1])**2)*100))
                first = w
            elif len(measurement) == 2:
                measurements.append(int(math.sqrt(
                    (first[0] - w[0])**2 + (first[1] - w[1])**2)*100))
                first = list(map(float, measurement[1].split(",")))

    measurements.reverse()
    sample.update_measurements(measurements)
    if dateEnd != 0:
        sample.setDateEnd(dateEnd)
    return {str(sample.KeyCode()): sample}


def write_fh(fn, arg):
    '''
    Saves Sequence objects passed in dict in file on disk.
    fn - path to file
    arg - dict with Sequence objects
    '''

    out = ''
    for seq in arg.values():
        out += 'HEADER:\n'
        out += seq.export_meta_all()
        out += 'DATA:Tree\n'

        # format measurements in poroper
        for i, meas in enumerate(seq.measurements()):
            out += (6 - len(str(meas))) * " " + str(meas)
            if i > 0 and (i + 1) % 10 == 0:
                out += '\n'

        # update zeros in las row of measurements to be compatible with tsap
        if len(seq.measurements()) % 10 != 0:
            out += (10 - len(seq.measurements()) % 10) * '     0'
            out += '\n'

    with open(fn, 'w') as p:
        p.write(out)


def read_r(fn):
    '''
    Read data from Cracow format [avr, avs, r0, av0, etc.]
    fn - path to file
    returns dict with Sequence obj without metadata becase Cracow format
    dont store them, datebegin is alway set to 1
    '''
    sample = Sequence()
    kc = str(os.path.basename(fn).split('.')[0])
    sample.set_meta("KeyCode", kc)

    stat = os.stat(fn)
    dl = int(stat.st_size)

    i = 0
    meas_list = []
    with open(fn, "rb") as meas_file:
        while i < (dl/2):
            meas_file.seek(i*2)
            t = struct.unpack('bb', meas_file.read(2))

            t = (t[0]*100)+t[1]

            if i > 2:
                meas_list.append(t)
            elif i == 1:
                # zapisujemy poczatek bielu
                if t != 0:
                    pocz = t
            elif i == 2:
                # Sapwood
                if t != 0:
                    t = t - pocz
                    sample.set_meta("SapWood", t)
            i += 1

    sample.update_measurements(meas_list)

    return {str(sample.KeyCode()): sample}


def write_r(fn, arg):
    """
    fn - path to file,
    arg - Sequence object (NOT DICT)
    Saves sample as binary file in Cracow format [avr, avs, r0, av0, etc.]
    Please consider not using it, very old format add it for backcompability
    """
    seq = ""
    i = 0

    # header of list which will be saved to file, places with zeros designed
    # for sapwood storage
    seq = struct.pack("bbbbbb", 0, 0, 0, 0, 0, 0)

    # list with measurements
    a = arg.measurements()

    while i < len(a):
        part_1 = int(a[i] / 100)
        part_2 = int(int(a[i]) - (part_1 * 100))
        seq += struct.pack('bb', part_1, part_2)
        i += 1

    with open(fn, 'wb') as meas_file:
        meas_file.write(seq)


def _rwl_strip_terminator(meas):
    """Drop the trailing Tucson end-of-series marker (999 or -9999)."""
    if meas and meas[-1] in (999, -9999):
        return meas[:-1]
    return meas


def read_rwl(fn):
    """
    Reads rwl files saved in tucson format, no metadata will be stored in
    sample file
    fn - path to file with samples
    return dict with Sequence objects
    """
    sample = None  # sample currently being read
    meas_list = []  # its measurements so far
    name = ''  # its 8-char name prefix
    seq_dict = {}  # dict with processed samples

    with open(fn, 'r') as meas_file:
        rwl_lines = meas_file.readlines()

    for line in rwl_lines:
        line = line.rstrip('\n\r')

        # split on spaces, drop empty fields; skip blank / whitespace lines
        val = list(filter(None, line.split(" ")))
        if not val:
            continue

        if len(val[0]) < 9:  # name field is separated from the first value
            ww = val
        else:  # name is glued to the year / values, split by column
            ww = [line[:8], int(line[8:12].replace(' ', ''))]
            i = 12
            while i < len(line):
                ww.append(str(int(line[i:i+6])))
                i = i + 6

        if ww[0] != name:
            # a new sample starts: close the previous one first
            if sample is not None:
                sample.update_measurements(_rwl_strip_terminator(meas_list))
                seq_dict[str(sample.KeyCode())] = sample
            name = ww[0]
            sample = Sequence({"KeyCode": ww[0], "DateBegin": ww[1]})
            meas_list = [int(x) for x in ww[2:]]
        else:
            meas_list += [int(x) for x in ww[2:]]

    # close the final sample
    if sample is not None:
        sample.update_measurements(_rwl_strip_terminator(meas_list))
        seq_dict[str(sample.KeyCode())] = sample

    return seq_dict


def write_rwl(fn, arg):
    '''
    fn - path to file
    arg - Sequence objects as dict
    Saves Sequence object to rwl (tucson format)
    '''

    write_in = ''  # sting to save to file
    duplicates = set()  # set to check duplictaes in shorten names

    for a in arg.values():
        # set first column with sample name
        if len(a.KeyCode()) < 8:
            # if name is shorter than 9 add spaces
            name = a.KeyCode() + ((8 - len(a.KeyCode())) * " ")
            # list of unique names, will be usefull to check duplicates in
            # shorten names
            duplicates.add(name)
        else:
            # trim if longer than 8 signs, will check for duplictaes
            n = a.KeyCode()
            while True:
                if n[:8] not in duplicates:
                    name = n[:8]
                else:
                    j = 0
                    while True:
                        if n[:(8-j//10)] + str(j) not in duplicates:
                            name = n[:(8-j//10)] + str(j)
                            break
                        else:
                            j = j + 1
                # add name to unique set
                duplicates.add(name)
                break

        for i, meas in enumerate(a.measurements()):
            if i == 0:
                date_begin = (4-len(str(a.DateBegin()))) * ' ' \
                    + str(a.DateBegin())
                sp_meas = (6-len(str(meas))) * ' '
                imeas = str(int(meas))
                write_in += name + date_begin + sp_meas + imeas
            else:
                # if there is full decad start new line if file
                if (a.DateBegin()+i) % 10 == 0:
                    write_in += (
                        "\n" + name +
                        (4 - len(str(int(((a.DateBegin() /
                                           10+int(i/10)+1)*10)))))*" " +
                        str(int((a.DateBegin()/10+int(i/10)+1)*10)) +
                        ((6 - len(str(meas))) * " ") + str(meas))
                else:
                    write_in += ((6 - len(str(meas))) * " ") + str(meas)

        # add 999 as end of sample measurements
        if a.DateEnd() % 10 == 9:
            write_in += "\n" + name + ((4 - len(str(a.DateEnd()))) *
                                       " ") + str(a.DateEnd() + 1) + "   999\n"
        else:
            write_in += "   999\n"

    with open(fn, "w") as meas_file:
        meas_file.write(str(write_in))


def write_txt(fn, a):
    '''
    fn - path to file,
    a - Sequence object (not dict)
    '''
    write_in = a.KeyCode() + "\n"
    write_in += '\n'.join(map(str, a.measurements()))

    with open(fn, "w") as meas_file:
        meas_file.write(write_in)


def prepare_to_chart(a):
    a = math.log((int(a)))
    return a


def _T(n, r):
    # n - length of comparing sequence
    # r - coeff comparing seq
    try:
        t = (float(r)*math.sqrt(float(n)-2))/(math.sqrt(1-(float(r)*float(r))))
    except (ZeroDivisionError, ValueError):
        return 1
    return t


def _T_curve(n, r):
    '''Vectorised _T. Returns 1 exactly where the scalar catches a
    ValueError / ZeroDivisionError (|r| >= 1, or n < 2).'''
    n = np.asarray(n, dtype=np.float64)
    r = np.asarray(r, dtype=np.float64)
    with np.errstate(invalid='ignore', divide='ignore'):
        t = r * np.sqrt(n - 2.0) / np.sqrt(1.0 - r * r)
    return np.where(np.isfinite(t) & (n >= 2.0), t, 1.0)


def cdi(glk_value, section, sample_len, TBP, TH):
    t = (float(TBP)+float(TH))/2
    ret = (((float(glk_value)-50) +
            (50*math.sqrt(float(section)/float(sample_len))))*t)/10
    return round(ret, 0) if ret < 1000 else 1000


def corellate(sample, reference, count=10):  # noqa
    ''' Compute correlations between 2 samples (Sequence) object and returning
    list with computations (default 10 best statistical results)
    returns [[crosscoef, TBP, TH, T, GLK, GSL, CDI,
             beg_from_ref, ovl, sample_name, ref_name], ...]
    '''
    a_name, am = str(sample.KeyCode()), sample.measurements()
    b_name, bm = str(reference.KeyCode()), reference.measurements()
    na, nb = len(am), len(bm)

    lags = np.arange(25 - na, nb - 25, dtype=np.int64)
    if lags.shape[0] == 0 or na < 5 or nb < 5:
        return []

    max_ovl = nb if nb < na else na  # max overlay (needed for cdi)

    af, bpa, ha, ga = _standardize(am)
    bf, bpb, hb, gb = _standardize(bm)

    r_raw, r_bp, r_h, glk, m, ovl = _offset_curves(
        af, bf, bpa, bpb, ha, hb, ga, gb, lags)
    n_bp = m - 4
    n_h = m - 1

    # rank every offset by CDI with a vectorised copy of the _stats_row math
    # (verified equal to the scalar path to the last digit), then build only
    # the `count` winning rows through the scalar _stats_row so their exact
    # rounding / GSL / cdi values stay identical to the golden
    tbp = np.round(_T_curve(n_bp, r_bp), 1)
    th = np.round(_T_curve(n_h, r_h), 1)
    glkr = np.round(glk / (m - 1) * 100)
    glk_for_cdi = np.where(glk > 0, glkr, 0.00001)
    tmean = (tbp + th) / 2.0
    ret = (((glk_for_cdi - 50) + 50 * np.sqrt(m / max_ovl)) * tmean) / 10.0
    cdi_curve = np.where(ret < 1000, np.round(ret, 0), 1000.0)

    order = np.argsort(-cdi_curve, kind='stable')[:count]

    results = []
    for k in order:
        k = int(k)
        row = _stats_row(
            float(r_raw[k]), float(r_bp[k]), float(r_h[k]),
            int(m[k]), int(n_bp[k]), int(n_h[k]),
            int(glk[k]), max_ovl)
        row.append(int(lags[k]))     # offset from ref
        row.append(int(ovl[k]))      # overlap
        row.append(a_name)
        row.append(b_name)
        results.append(row)

    return results


def _mirror_rows(rows):
    '''The reverse view of a result list: offset sign flipped, the two name
    columns swapped.'''
    return [r[:7] + [-r[7], r[8], r[10], r[9]] for r in rows]


def _cd_batch(rname, rmeas, sample_names, samples, count):
    '''corellate one reference against every named sample. `samples` maps
    name -> measurement list.'''
    ref = Sequence({'KeyCode': rname, 'measurements': list(rmeas)})
    out = []
    for sname in sample_names:
        smp = Sequence({'KeyCode': sname,
                        'measurements': list(samples[sname])})
        out.append((sname, corellate(smp, ref, count)))
    return out


_CD_SAMPLES = None


def _cd_init(sample_data):
    '''Pool initializer: keep the shared sample measurements in each worker
    so per-reference tasks only carry the reference itself.'''
    global _CD_SAMPLES
    _CD_SAMPLES = sample_data


def _cd_worker(task):
    rname, rmeas, sample_names, count = task
    return _cd_batch(rname, rmeas, sample_names, _CD_SAMPLES, count)


def crossdate_pairs(refs, smps, count=10, max_workers=None):
    '''Crossdate every distinct smp/ref pair, optionally across processes.

    refs, smps - lists of Sequence. Returns the res_dict the serial double
    loop built: {name: {other: rows}}, each unordered pair stored both ways
    (the reverse view via _mirror_rows). Key insertion order matches the
    serial `for ref: for smp:` walk, so the result is identical whatever the
    worker count. Work is batched one task per reference; max_workers=1 (or a
    small job) runs in-process.
    '''
    order = []          # (rname, ref_measurements, [sample_name, ...])
    seen = set()
    for ref in refs:
        rname = ref.KeyCode()
        todo = []
        for smp in smps:
            sname = smp.KeyCode()
            if sname == rname or (sname, rname) in seen:
                continue
            seen.add((rname, sname))
            todo.append(sname)
        if todo:
            order.append((rname, ref.measurements(), todo))

    if not order:
        return {}

    samples = {s.KeyCode(): s.measurements() for s in smps}
    total = sum(len(names) for _, _, names in order)

    # A pool only pays off once the compute clearly beats spawn + IPC; below
    # that stay in-process. An explicit max_workers > 1 forces the pool.
    if max_workers is None:
        parallel = total >= 2000 and len(order) > 1
    else:
        parallel = max_workers != 1

    if not parallel:
        batches = [_cd_batch(r, rm, names, samples, count)
                   for r, rm, names in order]
    else:
        tasks = [(rname, rmeas, names, count)
                 for rname, rmeas, names in order]
        with ProcessPoolExecutor(max_workers=max_workers,
                                 initializer=_cd_init,
                                 initargs=(samples,)) as ex:
            batches = list(ex.map(_cd_worker, tasks))

    res_dict = {}
    for (rname, _, _), batch in zip(order, batches):
        for sname, crslt in batch:
            res_dict.setdefault(rname, {})
            res_dict.setdefault(sname, {})
            res_dict[rname][sname] = crslt
            res_dict[sname][rname] = _mirror_rows(crslt)
    return res_dict


def corellate_position(a, b):  # noqa
    '''
    computes statistics for 2 samples at their current position defined as
    DateBegin.
    a, b - Sequence objects
    returns [crosscoef, TBP, TH, T, GLK, GSL, CDI, ]
    '''
    if not isinstance(a, Sequence) or not isinstance(b, Sequence):
        return False

    # the sample that starts earlier is the reference
    younger, older = a, b
    if a.DateBegin() < b.DateBegin():
        younger, older = b, a

    end_date = min(int(younger.DateEnd()), int(older.DateEnd()))
    offset = abs(older.DateBegin() - younger.DateBegin())
    length = end_date - younger.DateBegin() + 1

    # less than 30 overlapping years - no statistics
    if length < 30:
        return ['xxx', 'xxx', 'xxx', 'xxx', 'xxx', 'xxx', 'xxx']

    x = np.asarray(younger.measurements()[:length], dtype=np.float64)
    y = np.asarray(older.measurements()[offset:offset + length],
                   dtype=np.float64)

    _, bpx, hx, gx = _standardize(x)
    _, bpy, hy, gy = _standardize(y)

    glk = int(np.count_nonzero(gx == gy))

    return _stats_row(
        _fast_r(x, y),
        _fast_r(bpx[2:], bpy[2:]),
        _fast_r(hx[1:], hy[1:]),
        x.shape[0], bpx[2:].shape[0], hx[1:].shape[0],
        glk, min(younger.Length(), older.Length()))


def format_text_spaces(text, text_len=6):
    '''Returns string with spaces after space, it text is longer than limit,
    trims exceeding signs
    '''
    text = str(text)

    if len(text) < text_len:
        a = text + (text_len - len(text)) * " "
    else:
        a = text[:text_len]
    return a


class Sequence:
    '''
    class for keeping one measurement with metadata
    all items saved as dict: self.sample[keys] = {}
    On creation there is option to add dict with data which will be added to
    sample metadata otherwise will be generated minimal set of data for samp.
    '''
    def __init__(self, dic=None):

        self.sample = {}
        if isinstance(dic, dict):
            self.sample.update(dic)
        else:
            self.sample = {"KeyCode": "Unknown",
                           "DateBegin": 1,
                           "measurements": []}

        if "DateBegin" not in self.sample.keys():
            self.sample["DateBegin"] = 1
        try:
            if int(self.sample["DateBegin"]) == 0:     # there is no year 0
                self.sample["DateBegin"] = 1
        except (TypeError, ValueError):
            self.sample["DateBegin"] = 1

        # DateEnd / Length are always derived (DateBegin + measurements is the
        # single source of truth); normalise away any that came in with `dic`
        # so the getters can stay side-effect free
        self.sample.pop("Length", None)
        if "DateEnd" in self.sample:
            end = self.sample.pop("DateEnd")
            meas = self.sample.get("measurements") or []
            if meas:
                try:
                    end = int(end)
                    if end == 0:
                        end = 1
                    begin = end - (len(meas) - 1)
                    if begin <= 0 < end:              # crosses the era boundary
                        begin -= 1
                    self.sample["DateBegin"] = begin
                except (TypeError, ValueError):
                    pass

        self.forb_keys = {'measurements', 'DateEnd', 'Length'}
        self._edited = 0  # edited=1, not edited=0

    def __str__(self):
        return '\n'.join(['KeyCode: '+self.KeyCode(),
                          'DateBegin: '+str(self.DateBegin()),
                          'Len: '+str(self.Length()),
                          ])

    # metody zwracajace warotsci klasy
    def KeyCode(self):
        if 'KeyCode' in self.sample.keys():
            return self.sample['KeyCode']
        else:
            logger.warning("No metadata: KeyCode")

    def DateBegin(self):
        '''First calendar year. Pure getter: DateBegin is the single stored
        source of truth, DateEnd and Length are derived from it.'''
        return int(self.sample['DateBegin'])

    def DateEnd(self):
        '''Last calendar year, derived from DateBegin + Length (skipping the
        non-existent year 0).'''
        lde = self.Length() - 1 if self.Length() > 0 else 0
        return _year_at_offset(self.DateBegin(), lde)

    def years(self):
        '''Calendar year of every ring, in order - never contains 0.'''
        return year_span(self.DateBegin(), self.Length())

    def Length(self):
        '''Return len(measurements) of sample'''
        if 'measurements' in self.sample:
            return len(self.sample['measurements'])
        return 0

    def SapWood(self):
        # not checking if sapwood is int, should be checked upon creation
        if 'SapWood' in self.sample.keys():
            try:
                return int(self.sample['SapWood'])
            except ValueError:
                return 0
        else:
            return 0

    def Bark(self):
        if 'Bark' in self.sample.keys():
            return str(self.sample['Bark'])
        else:
            return("")

    def pith_growth(self):
        # not fully growth last ring (in year of cutdown of tree)
        if 'pith_growth' in self.sample.keys():
            return str(self.sample['pith_growth'])
        else:
            return("")

    def set_measurement(self):
        return self.sample['measurements']

    def export_meta(self, header):
        # zwracamy val dla podanej definicji pola o ile istnieje
        if isinstance(header, str) and header in self.sample.keys():
            return self.sample[header]
        else:
            return ''

    def export_meta_all(self):
        # zwraca cala tablice z danymi opisowymi
        out = ''
        for k in self.sample.keys():
            if k not in self.forb_keys:
                out += k + "=" + str(self.sample[k]) + "\n"
        out += "DateEnd=" + str(self.DateEnd()) + "\n"
        out += "Length=" + str(self.Length()) + "\n"
        return out

    def measurements(self):
        ''' return measurements list'''
        if 'measurements' in self.sample:
            return self.sample['measurements']
        return 0

    def measure_from_year(self, year):
        year = int(year)
        if year == 0 or not self.DateBegin() <= year <= self.DateEnd():
            return False
        try:
            return self.sample['measurements'][
                _offset_of_year(year, self.DateBegin())]
        except IndexError:
            return False

    # update methods
    def set_meta(self, header, val):
        '''Set a metadata field. DateEnd / Length / measurements are derived
        and cannot be set here - use setDateEnd / update_measurements.'''
        if header not in self.forb_keys:
            self.sample[header] = val
            self._edited = 1

    def setDateBegin(self, val):
        # ustawiamy date poczatku, przyjmuje tylko wartosci int
        try:
            v = int(val)
        except (TypeError, ValueError):
            logger.warning("Only integer values are respected for DateBegin")
            return
        if v == 0:                       # there is no year 0
            v = 1
        self.sample['DateBegin'] = v
        self._edited = 1

    def setDateEnd(self, val):
        '''Set the last year - DateBegin is back-derived from it (skipping the
        non-existent year 0) so DateBegin stays the single source of truth.'''
        try:
            end = int(val)
        except (TypeError, ValueError):
            logger.warning("Only integer values are respected as DateEnd")
            return
        if end == 0:
            end = 1
        begin = end - (self.Length() - 1)
        if begin <= 0 < end:             # the span crosses the era boundary
            begin -= 1
        self.sample['DateBegin'] = begin
        self._edited = 1

    def update_measurements(self, val):
        self.sample['measurements'] = val
        self._edited = 1

    def add_measurement(self, val):
        if str(val).isdigit():
            self.sample['measurements'].append(val)
        else:
            logger.warning("Only numerical values are respected as measurements")

    def delete_last_measurement(self):
        meas_list = self.sample['measurements']
        meas_list.pop()
        self.sample['measurements'] = meas_list

    def update_year_measurement(self, year, val):
        '''Updates increment in provided year'''
        if not _intlike(year) or not str(val).isdigit() or int(year) == 0:
            return False
        if self.DateBegin() <= int(year) <= self.DateEnd():
            self.sample['measurements'][
                _offset_of_year(int(year), self.DateBegin())] = int(val)

    def add_year_measurement(self, year, val):
        '''Adds increment in year provided by user'''
        if not _intlike(year) or not str(val).isdigit() or int(year) == 0:
            return False

        if self.DateBegin() <= int(year) <= self.DateEnd():
            self.sample['measurements'].insert(
                _offset_of_year(int(year), self.DateBegin()), int(val))
            return True
        return False

    def delete_year_measurement(self, year):
        '''Deletes measurement in year, if year beyond datebegin or dateend
        reutns False
        '''
        if not _intlike(year) or int(year) == 0:
            return False

        if self.DateBegin() <= int(year) <= self.DateEnd():
            del self.sample['measurements'][
                _offset_of_year(int(year), self.DateBegin())]
            return True
        return False


class recursivedefaultdict(defaultdict):
    def __init__(self):
        self.default_factory = type(self)


class DataBase:
    '''
    database factory to organize samples in stacks
    stack_name - (str, list of strings)
    '''
    def __init__(self, stack_name=False):
        self.base = recursivedefaultdict()

        if isinstance(stack_name, str):
            self.base[stack_name] = recursivedefaultdict()
        if isinstance(stack_name, list):
            for it in stack_name:
                self.base[it] = recursivedefaultdict()

    def __getitem__(self, it):
        ''' Returns all samples from stack as dict'''
        return self.base[it]

    def clear(self):
        self.base = recursivedefaultdict()

    def add_seq(self, stack, samples):
        """
        method keep dict with sequences, checking duplicates in stacks, and
        adding sequences to stack
        samples = dict with sequences
        stack = str with name of stack to add samples
        """
        for seq in samples.values():
            if seq.KeyCode() not in self.base[stack].keys():
                self.base[stack][seq.KeyCode()] = seq
            else:
                val = 1  # value in brackets which will be added to keycode
                while True:
                    if seq.KeyCode() + "(" + str(val) + ")" \
                            not in self.base[stack].keys():
                        seq.set_meta("KeyCode",
                                     seq.KeyCode() + "(" + str(val) + ")")
                        break
                    else:
                        val += 1
            self.base[stack][seq.KeyCode()] = seq

    def del_seq(self, stack, seq):
        if stack in self.base.keys():
            for s in seq:
                if s in self.base[stack].keys():
                    del self.base[stack][s]
                else:
                    logger.warning("No sequence by that name (%s)", s)
            return True
        else:
            logger.warning("No stack by that name")
        return False

    def seq_from_stack(self, stack, selected=[]):
        '''
        returning dict with Sequence objects from pointed stack.
        if list with sequence names was submited only pointed will be returned.
        stack = str
        selected = []
        '''

        if not isinstance(selected, list):
            return False
        if len(selected) == 0:
            selected = self.base[stack].keys()

        tab = {k: self.base[stack][k] for k in selected
               if k in self.base[stack]}

        return tab

    def get(self, stack, key, default=None):
        '''O(1) lookup of a single Sequence. Returns `default` when the
        stack or key is missing - unlike a bare `self.base[stack][key]`
        it does not auto-create an empty entry on a typo.
        '''
        return self.base.get(stack, {}).get(key, default)

    def count_seqs(self, stack):
        return len(self.base[stack].keys())

    def calculate_mean(self, stack, samps):
        '''computes mean calculation from selected samples in stack and returns
        Sequence object
        '''

        seqs = self.seq_from_stack(stack, samps)
        if not seqs:
            raise ValueError(
                'calculate_mean: no matching samples in stack %r' % stack)
        miny = min([x.DateBegin() for x in seqs.values()])
        maxy = max([x.DateEnd() for x in seqs.values()])

        data = []
        for i in range(miny, maxy + 1):
            if i == 0:                       # there is no year 0
                continue
            year_vals = [m for m in (val.measure_from_year(i)
                                     for val in seqs.values())
                         if m is not False]
            data.append(year_vals)

        # calculate sapwood
        sapw = [x.DateEnd()-x.SapWood() for x in seqs.values()
                if x.SapWood() != 0]
        if len(sapw) > 0:
            sapwm = maxy - round(sum(sapw) / len(sapw))
        else:
            sapwm = 0

        mean = [round(sum(x)/len(x)) if len(x) > 0 else 0.01 for x in data]
        stmp = Sequence({'KeyCode': 'Mean',
                         'DateBegin': miny,
                         'measurements': mean,
                         'SapWood': sapwm,
                         'Refs': ','.join(samps)})
        return stmp

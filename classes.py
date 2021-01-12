from collections import defaultdict
import os
import math
import struct
from numpy import corrcoef as crosscoef
from numpy import add
from collections import Counter


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
        meas_file = open(fn, 'r')

        for line in meas_file:
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
                            new_keycode = sample.KeyCode() + "(" + i + ")"
                            if new_keycode not in seq_dict.keys():
                                # update sample name and add it to dict
                                print(
                                    "Nadano nowa nazwe zdublowanej probie: " +
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
        meas_file.close()

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

    for line in open(fn, 'r'):
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

        p = open(fn, 'w')
        p.write(out)
        p.close()


def read_r(fn):
    '''
    Read data from Cracow format [avr, avs, r0, av0, etc.]
    fn - path to file
    returns dict with Sequence obj without metadata becase Cracow format
    dont store them, datebegin is alway set to 1
    '''
    meas_file = open(fn, "rb")
    sample = Sequence()
    kc = str(os.path.basename(fn).split('.')[0])
    sample.set_meta("KeyCode", kc)

    stat = os.stat(fn)
    dl = int(stat.st_size)

    i = 0
    meas_list = []
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

    meas_file = open(fn, 'wb')
    meas_file.write(seq)
    meas_file.close()


def read_rwl(fn):
    """
    Reads rwl files saved i tucson format, no metadata wil be stored in
    sample file
    fn - path to file with samples
    return dict with Sequence objects
    """
    first = 0  # trigg for first sample
    sample = Sequence({})
    meas_list = []  # measurement list
    name = ''  # name of current sample
    seq_dict = {}  # dict with processed samples

    meas_file = open(fn, 'r')

    for line in meas_file:
        line = line.rstrip('\n\r')

        # filter all None values from list
        val = list(filter(None, line.split(" ")))

        if len(val[0]) < 9:  # if seq name is less than 9 signs
            ww = val    # let assume name is ok
        else:  # if not, we should do it by slices
            ww = []
            ww.append(line[:8])  # name of sample
            ww.append(int(line[8:12].replace(' ', '')))  # Date begin
            i = 12
            while i < len(line):
                ww.append(str(int(line[i:i+6])))
                i = i+6

        if ww[0] != name and len(ww) > 0:
            # if first sample, we need to set evrything up
            if first == 1:
                sample.update_measurements(meas_list[:-1])
                seq_dict[str(sample.KeyCode())] = sample
                first = 1
            name = ww[0]

            # set new sample
            sample = Sequence({"KeyCode": ww[0], "DateBegin": ww[1]})
            meas_list = [int(x) for x in ww[2:]]  # add meas from current line
        else:
            meas_list += list(map(int, ww[2:]))  # add meas from another lines

        # add meas without last 999, which is end of measurements
        sample.update_measurements(meas_list[:-1])
        seq_dict[str(sample.KeyCode())] = sample

    meas_file.close()
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

    meas_file = open(fn, "w")
    meas_file.write(str(write_in))
    meas_file.close()


def write_txt(fn, a):
    '''
    fn - path to file,
    a - Sequence object (not dict)
    '''
    write_in = a.KeyCode() + "\n"
    write_in += '\n'.join(map(str, a.measurements()))

    meas_file = open(fn, "w")
    meas_file.write(write_in)
    meas_file.close()


def prepare_to_chart(a):
    a = math.log((int(a)))
    return a


def _T(n, r):
    # n - length of comparing sequence
    # r - coeff comparing seq
    try:
        t = (float(r)*math.sqrt(float(n)-2))/(math.sqrt(1-(float(r)*float(r))))
    except ZeroDivisionError:
        return 1
    return t


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
    # a-sample
    # b-ref
    results = []
    beg_a = 0
    beg_b = 0
    end_a = 0
    end_b = 0
    ovl = 0
    # list of standarisations data
    standBPa = [0, 0]
    standBPb = [0, 0]
    standHa = []
    standHb = []
    glka = []
    glkb = []
    # prepare lists with meas
    a = [sample.KeyCode(), sample.measurements()]
    b = [reference.KeyCode(), reference.measurements()]

    max_ovl = int(len(a[1]))  # max overlay set to length of sample

    # if ref is shorther then change acordingly
    if int(len(b[1])) < int(len(a[1])):
        max_ovl = int(len(b[1]))

    # compute standarizations
    longer_sample = len(b[1])
    if len(a[1]) > longer_sample:
        longer_sample = len(a[1])

    for i in range(longer_sample):
        # BP standarization
        if i < len(a[1]) - 2 and i > 1:
            standBPa.append((math.log(
                (5 * float(a[1][i]))/sum(list(map(float, a[1][i-2:i+3])))
            )))
        if i < len(b[1]) - 2 and i > 1:
            standBPb.append((math.log(
                (5 * float(b[1][i]))/sum(list(map(float, b[1][i-2:i+3])))
            )))

        # H standarization
        if i < (len(a[1]) - 1):
            standHa.append(
                (math.log((float(a[1][i]) / float(a[1][i+1])), 10))
            )
        if i < (len(b[1]) - 1):
            standHb.append(
                (math.log((float(b[1][i]) / float(b[1][i + 1])), 10))
            )

        # GLK
        if i < len(a[1]) - 1:
            if (float(a[1][i + 1]) - float(a[1][i]) >= 0):
                glka.append(1)
            else:
                glka.append(0)
        if i < len(b[1]) - 1:
            if (float(b[1][i + 1]) - float(b[1][i]) >= 0):
                glkb.append(1)
            else:
                glkb.append(0)

    i = 25 - len(a[1])
    while i < len(b[1]) - 25:
        # I: sample on left side and is shorter than ref
        if i <= 0 and (len(a[1]) + i - 1) < len(b[1]):
            beg_b = 0
            end_b = i + len(a[1])
            beg_a = len(a[1]) - (len(a[1]) + i)
            end_a = len(a[1])
            ovl = i + len(a[1])
            glk_sklad = list(add(glka[beg_a:end_a - 1], glkb[beg_b:end_b - 1]))
            # compute compatibility of sequences
            glk = Counter(glk_sklad)[0] + Counter(glk_sklad)[2]

        # II: sample on left size and is longer than ref
        if i <= 0 and (len(a[1]) + i - 1) >= len(b[1]):
            beg_b = 0
            end_b = len(b[1])
            beg_a = len(a[1]) - (len(a[1]) + i)
            end_a = beg_a + len(b[1])
            ovl = len(b[1])
            glk_sklad = list(add(glka[beg_a:end_a - 1], glkb[beg_b:end_b - 1]))
            glk = Counter(glk_sklad)[0] + Counter(glk_sklad)[2]

        # III: sample has begining younger than ref beg and is shorter than ref
        if i > 0 and (len(a[1]) + i - 1) < len(b[1]):
            beg_b = i
            end_b = len(a[1]) + i
            beg_a = 0
            end_a = len(b[1])
            ovl = len(a[1]) - 1
            glk_sklad = list(add(glka[beg_a:end_a - 1], glkb[beg_b:end_b - 1]))
            glk = Counter(glk_sklad)[0] + Counter(glk_sklad)[2]

        # IV: sample has begining younger than ref beg and is longer than ref
        if i > 0 and (len(a[1]) + i - 1) >= len(b[1]):
            beg_b = i
            end_b = len(b[1])
            beg_a = 0
            end_a = len(b[1]) - i
            ovl = len(b[1]) - i
            glk_sklad = list(add(glka[beg_a:end_a - 1], glkb[beg_b:end_b - 1]))
            glk = Counter(glk_sklad)[0] + Counter(glk_sklad)[2]

        work_res = correlation(
            a[1][beg_a: end_a],
            b[1][beg_b: end_b],
            max_ovl,
            standBPa[beg_a + 2: end_a - 2],
            standBPb[beg_b + 2: end_b - 2],
            standHa[beg_a: end_a - 1],
            standHb[beg_b: end_b - 1],
            glk)

        # movement from ref
        work_res.append(i)  # begining
        work_res.append(int(ovl))  # ovl
        i += 1

        # set keycodes
        work_res.append(str(a[0]))  # sample
        work_res.append(str(b[0]))  # ref

        results.append(work_res)

    res = sorted(results, key=lambda x: x[6], reverse=True)
    return res[:count]


def correlation(a, b, dl_a, standBPa, standBPb, standHa, standHb, glk):
    '''
    compute statistics for two samples of equal length (not necesarily full
    length od sample.

    a, b - list of measures, should have same length
    dl_a - max overaly of 2 samples (needed to cdi calcs)
    standBPa=[]
    standBPb=[]
    standHa=[]
    standHb=[]
    glk=0
    returns [crosscoef, TBP, TH, T, GLK, GSL, CDI, ]
    '''

    result = []
    # change measurements to floats
    a = list(map(float, a))
    b = list(map(float, b))

    # calculate crosscoef
    result.append(round(float(crosscoef(a, b)[1][0]), 2))

    # T for BP standarization
    val = round(_T(len(standBPa),
                   float(crosscoef(standBPa, standBPb)[1][0])
                   ), 1)
    result.append(val)

    # T for H standarization
    val = round(_T(len(standHa), crosscoef(standHa, standHb)[1][0]), 1)
    result.append(val)

    # T whithout standarization
    val = round(_T(len(a), float(crosscoef(a, b)[1][0])), 1)
    result.append(val)

    if glk > 0:
        # GLK
        glkr = round((float(glk)/(len(a)-1))*100)
        result.append(glkr)
        # GSL
        fr1 = 50 + (82.7/math.sqrt(len(a)))
        fr2 = 50 + (116.3/math.sqrt(len(a)))
        fr3 = 50 + (154/math.sqrt(len(a)))

        if fr1 <= glkr < fr2:
            result.append("*")
        elif fr2 <= glkr < fr3:
            result.append("**")
        elif glkr >= fr3:
            result.append("***")
        else:
            result.append("")

    else:
        result.append(0.00001)
        result.append("")

    # CDI
    result.append(int(cdi(result[4], len(a), dl_a, result[1], result[2])))

    return result


def corellate_position(a, b):  # noqa
    '''
    computes statistics for 2 samples at their current position defined as
    DateBegin.
    a, b - Sequence objects
    returns [crosscoef, TBP, TH, T, GLK, GSL, CDI, ]
    '''
    if not isinstance(a, Sequence) or not isinstance(b, Sequence):
        return False

    offset = 0  # offset in samp with older date of begin
    tab = [[], []]  # lists with data to calculate
    # structure to compute standaristation
    standBPa = [0, 0]
    standBPb = [0, 0]
    standHa = []
    standHb = []
    glka = []
    glkb = []

    # select older sample to be reference
    younger = a
    older = b
    if a.DateBegin() < b.DateBegin():  # swap samples to match criteria
        younger = b
        older = a

    # check for older date end to get proper data structure
    end_date = int(younger.DateEnd())
    if end_date > int(older.DateEnd()):
        end_date = int(older.DateEnd())

    # check for younger date begin, same reason as above
    offset = abs(older.DateBegin() - younger.DateBegin())

    # prepare structure for statistic computation
    i = 0
    while i < end_date - younger.DateBegin() + 1:
        # younger sample - with offset
        tab[0].append(younger.measurements()[i])
        tab[1].append(older.measurements()[i+offset])
        i += 1

    # if len of structure is less than 30 years, no statistics
    if len(tab[0]) < 30:
        return ['xxx', 'xxx', 'xxx', 'xxx', 'xxx', 'xxx', 'xxx']

    for i in range(len(tab[0])):
        # standarization BP
        if i < len(tab[1])-2 and i > 1:
            standBPa.append((math.log(
                (5 * float(tab[0][i]))/sum(list(map(float, tab[0][i-2:i+3])))
            )))
            standBPb.append((math.log(
                (5*float(tab[1][i]))/sum(list(map(float, tab[1][i-2:i+3])))
            )))

        # standarization H
        if i < (len(tab[0])-1):
            standHa.append(
                math.log(float(tab[0][i]) / float(tab[0][i+1]), 10)
            )
            standHb.append(
                math.log(float(tab[1][i])/float(tab[1][i+1]), 10)
            )

        # GLK
        if i < len(tab[0])-1:
            if (float(tab[0][i+1])-float(tab[0][i]) >= 0):
                glka.append(1)
            else:
                glka.append(0)
        if i < len(tab[1])-1:
            if (float(tab[1][i+1])-float(tab[1][i]) >= 0):
                glkb.append(1)
            else:
                glkb.append(0)

    glk = list(add(glka[:], glkb[:]))
    glk = Counter(glk)[0]+Counter(glk)[2]

    res = correlation(tab[0],
                      tab[1],
                      min(younger.Length(), older.Length()),
                      standBPa[2:],
                      standBPb[2:],
                      standHa[1:],
                      standHb[1:],
                      glk)
    return res


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
            print("No metadata: KeyCode")

    def DateBegin(self):
        if "DateEnd" in self.sample.keys() and \
                "measurements" in self.sample.keys():
            if len(self.sample['measurements']) > 0:
                self.setDateEnd(self.sample['DateEnd'])
            else:
                print("No measurements in sample, DateBegin set to 1")

        return int(self.sample['DateBegin'])

    def DateEnd(self):
        lde = self.Length() - 1 if self.Length() > 0 else 0
        return self.DateBegin() + lde

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
            if k != 'measurements':
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
        if not self.DateBegin() <= year <= self.DateEnd():
            return False
        try:
            return self.sample['measurements'][year-self.DateBegin()]
        except IndexError:
            return False

    # update methods
    def set_meta(self, header, val):
        if header not in self.forb_keys:
            self.sample[header] = val
            self._edited = 1

        if header == "DateEnd":
            self.setDateEnd(val)

    def setDateBegin(self, val):
        # ustawiamy date poczatku, przyjmuje tylko wartosci int
        try:
            self.sample['DateBegin'] = int(val)
            self._edited = 1
        except Exception:
            print("Only integer values are respected fot DateBegin")

    def setDateEnd(self, val):
        try:
            if 'measurements' in self.sample.keys():
                self.sample['DateBegin'] = (
                    int(val) + 1 - len(self.sample['measurements']))
                self._edited = 1
                if 'DateEnd' in self.sample.keys():
                    del self.sample['DateEnd']
            else:
                self.sample['DateEnd'] = int(val)
        except Exception:
            print("Only integer values are respected as DateEnd")

    def update_measurements(self, val):
        self.sample['measurements'] = val
        self._edited = 1

    def add_measurement(self, val):
        if str(val).isdigit():
            self.sample['measurements'].append(val)
        else:
            print("Only numerical values are resepected as measurements!")

    def delete_last_measurement(self):
        meas_list = self.sample['measurements']
        meas_list.pop()
        self.sample['measurements'] = meas_list

    def update_year_measurement(self, year, val):
        '''Updates increment in provided year'''
        if not str(year).isdigit() and not str(val).isdigit():
            return False
        if self.DateBegin() <= int(year) <= self.DateEnd():
            self.sample['measurements'][int(year)-self.sample['DateBegin']] =\
                int(val)

    def add_year_measurement(self, year, val):
        '''Adds increment in year provided by user'''
        if not str(year).isdigit() and not str(val).isdigit():
            return False

        if self.DateBegin() <= int(year) <= self.DateEnd():
            self.sample['measurements'].insert(
                int(year)-self.sample['DateBegin'], int(val))
            return True
        return False

    def delete_year_measurement(self, year):
        '''Deletes measurement in year, if year beyond datebegin or dateend
        reutns False
        '''
        if not str(year).isdigit():
            return False

        if self.DateBegin() <= int(year) <= self.DateEnd():
            del self.sample['measurements'][year-self.sample['DateBegin']]
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
                    print('No sequence by that name ('+s+')')
            return True
        else:
            print("No stack by that name")
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

    def count_seqs(self, stack):
        return len(self.base[stack].keys())

    def calculate_mean(self, stack, samps):
        '''computes mean calculation from selected samples in stack and returns
        Sequence object
        '''

        seqs = self.seq_from_stack(stack, samps)
        miny = min([x.DateBegin() for x in seqs.values()])
        maxy = max([x.DateEnd() for x in seqs.values()])

        data = [[val.measure_from_year(i) for val in seqs.values()
                 if val.measure_from_year(i) is not False]
                for i in range(miny, maxy+1)]

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

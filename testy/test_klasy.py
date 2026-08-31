import pytest  # noqa
import os
import classes


def test_read_fh():
    ff = classes.read_fh(['dane_test/deska1_3.fh', ])
    assert len(ff) == 1
    assert list(ff.keys()) == ['IMG_8409.JPG', ]
    assert ff['IMG_8409.JPG'].Length() == 35
    assert ff['IMG_8409.JPG'].DateBegin() == 166


def test_read_pos():
    ff = classes.read_pos('dane_test/deska1_3.pos')
    assert len(ff) == 1
    assert list(ff.keys()) == ['IMG_8409.JPG', ]
    assert ff['IMG_8409.JPG'].Length() == 35
    assert ff['IMG_8409.JPG'].DateBegin() == 166


def test_read_r():
    ff = classes.read_r('dane_test/LW11.R2')
    assert len(ff) == 1
    assert list(ff.keys()) == ['LW11', ]
    assert ff['LW11'].Length() == 81
    assert ff['LW11'].DateBegin() == 1


def test_read_rwl():
    ff = classes.read_rwl('dane_test/proba.rwl')
    assert len(ff) == 1
    assert list(ff.keys()) == ['proba001', ]
    assert ff['proba001'].Length() == 101
    assert ff['proba001'].DateBegin() == 1911


def test_write_fh():
    fin = classes.read_pos('dane_test/deska1_3.pos')
    classes.write_fh('dane_test/save_test_fh_file.fh', fin)
    fout = classes.read_fh(['dane_test/save_test_fh_file.fh'])
    os.remove('dane_test/save_test_fh_file.fh')

    assert fin['IMG_8409.JPG'].KeyCode() == fout['IMG_8409.JPG'].KeyCode()
    assert fin['IMG_8409.JPG'].DateBegin() == fout['IMG_8409.JPG'].DateBegin()
    assert fin['IMG_8409.JPG'].Length() == fout['IMG_8409.JPG'].Length()


def test_write_r():
    dic = {'KeyCode': 'test_save_r_file',
           'DateBegin': 1,
           'measurements': [x for x in range(20, 121)]
           }
    sample = classes.Sequence(dic)

    classes.write_r('dane_test/save_test_r_file.r', sample)
    fout = classes.read_r('dane_test/save_test_r_file.r')
    os.remove('dane_test/save_test_r_file.r')

    assert 'save_test_r_file' == fout['save_test_r_file'].KeyCode()
    assert 1 == fout['save_test_r_file'].DateBegin()
    assert 101 == fout['save_test_r_file'].Length()
    assert dic['measurements'] == fout['save_test_r_file'].measurements()


def test_write_rwl():
    dic = {'KeyCode': 'tsrwl_file',
           'DateBegin': 7,
           'measurements': [x for x in range(20, 121)]
           }
    sample = classes.Sequence(dic)
    dic2 = {'KeyCode': 'tsrwl_f2',
            'DateBegin': 1903,
            'measurements': [x for x in range(50, 121)]
            }
    sample2 = classes.Sequence(dic2)

    samp_dic = {sample.KeyCode(): sample,
                sample2.KeyCode(): sample2
                }

    classes.write_rwl('dane_test/save_test_rwl_file.rwl', samp_dic)
    fout = classes.read_rwl('dane_test/save_test_rwl_file.rwl')
    os.remove('dane_test/save_test_rwl_file.rwl')

    assert len(fout) == 2
    assert fout['tsrwl_f2'].Length() == 71
    assert fout['tsrwl_f2'].measurements() == dic2['measurements']


def test_corellate():
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          ])

    cor = classes.corellate(f1['proba_a'], f1['proba_b'])
    assert len(cor) == 10
    assert cor[0][2] == 3.5
    assert cor[0][4:7] == [70, '**', 21, ]
    assert cor[0][8] == 57


def test_corellate_position():
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          ])
    f1['proba_a'].setDateBegin(1688)
    f1['proba_b'].setDateBegin(1745)

    cor = classes.corellate_position(f1['proba_a'], f1['proba_b'])
    # assert f1['proba_a'].DateBegin() == 1745
    # assert f1['proba_b'].DateBegin() == 1687
    assert len(cor) == 7
    assert cor[6] == 21


def test_measure_in_year():
    f1 = classes.read_fh(['dane_test/proba_a.fh'])
    samp = f1['proba_a']
    samp.setDateBegin(1)
    assert samp.measure_from_year(2) == 183


def test_mean_calculation():
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh',
                          ])
    f1['proba_a'].setDateBegin(1)
    f1['proba_b'].setDateBegin(120)
    f1['IMG_8409.JPG'].setDateBegin(1)

    base = classes.DataBase('s')
    base.add_seq('s', f1)

    mean = base.calculate_mean('s', ['proba_a', 'proba_b', 'IMG_8409.JPG'])
    assert mean.KeyCode() == 'Mean'
    assert mean.DateBegin() == 1
    assert mean.measure_from_year(117) == 0.01
    assert mean.measure_from_year(1) == 189
    assert f1['proba_b'].measurements()[-1] == mean.measurements()[-1]


def test_read_fh_duplicate_keycode(tmp_path):
    '''A repeated KeyCode in a multi-sample .fh gets a numbered suffix
    instead of raising TypeError on the int concatenation.'''
    fh = tmp_path / 'dup.fh'
    fh.write_text(
        'HEADER:\nKeyCode=DUP\nDateBegin=1\nDATA:Tree\n   10   20   30\n'
        'HEADER:\nKeyCode=DUP\nDateBegin=1\nDATA:Tree\n   40   50   60\n'
        'HEADER:\nKeyCode=OTHER\nDateBegin=1\nDATA:Tree\n   70   80   90\n'
    )
    ff = classes.read_fh([str(fh)])
    assert set(ff.keys()) == {'DUP', 'DUP(1)', 'OTHER'}
    assert ff['DUP'].measurements() == [10, 20, 30]
    assert ff['DUP(1)'].measurements() == [40, 50, 60]


def test_year_measurement_bad_input():
    '''add/update_year_measurement reject the call when *either* argument
    is non-numeric (guard is `or`, not `and`).'''
    s = classes.Sequence({'KeyCode': 'x', 'DateBegin': 1,
                          'measurements': [10, 20, 30, 40, 50]})

    assert s.update_year_measurement(3, 'abc') is False
    assert s.update_year_measurement('abc', 99) is False
    assert s.add_year_measurement(3, 'abc') is False
    assert s.add_year_measurement('abc', 99) is False
    assert s.measurements() == [10, 20, 30, 40, 50]

    s.update_year_measurement(3, 99)
    assert s.measure_from_year(3) == 99


def test_delete_year_str_input():
    '''delete_year_measurement casts year to int before indexing, so a
    string year deletes the right element instead of raising TypeError.'''
    s = classes.Sequence({'KeyCode': 'x', 'DateBegin': 1,
                          'measurements': [10, 20, 30, 40, 50]})

    assert s.delete_year_measurement('3') is True
    assert s.measurements() == [10, 20, 40, 50]


MULTI_RWL = os.path.join(os.path.dirname(__file__), 'data', 'multi.rwl')


def test_read_rwl_multi_sample():
    '''Three concatenated Tucson series with different DateBegin, plus blank
    separator lines, all read back with the right span and measurements.'''
    ff = classes.read_rwl(MULTI_RWL)
    assert sorted(ff) == ['MULTI_AA', 'MULTI_BB', 'MULTI_CC']

    assert ff['MULTI_AA'].DateBegin() == 1801
    assert ff['MULTI_AA'].Length() == 45
    assert ff['MULTI_BB'].DateBegin() == 1850
    assert ff['MULTI_BB'].Length() == 63
    assert ff['MULTI_CC'].DateBegin() == 1795
    assert ff['MULTI_CC'].Length() == 120

    # 999 terminator is stripped, not counted, and not left in the data
    for seq in ff.values():
        assert 999 not in seq.measurements()[-1:]


def test_read_rwl_skips_blank_lines(tmp_path):
    rwl = tmp_path / 'blanks.rwl'
    rwl.write_text(
        'SMPL_X 1900    50    51    52    53    54\n'
        'SMPL_X 1905    55    56    57   999\n'
        '\n'
        '   \n'
        'SMPL_Y 1800    10    11    12    13\n'
        'SMPL_Y 1804    14    15   999\n'
    )
    ff = classes.read_rwl(str(rwl))
    assert sorted(ff) == ['SMPL_X', 'SMPL_Y']
    assert ff['SMPL_X'].DateBegin() == 1900
    assert ff['SMPL_X'].measurements() == [50, 51, 52, 53, 54, 55, 56, 57]
    assert ff['SMPL_Y'].measurements() == [10, 11, 12, 13, 14, 15]


def test_read_rwl_without_terminator_keeps_last_value(tmp_path):
    rwl = tmp_path / 'noend.rwl'
    rwl.write_text(
        'NOEND  1700    20    21    22\n'
        'NOEND  1703    23    24    25\n'
    )
    ff = classes.read_rwl(str(rwl))
    assert ff['NOEND'].measurements() == [20, 21, 22, 23, 24, 25]


def test_rwl_strip_terminator():
    assert classes._rwl_strip_terminator([1, 2, 999]) == [1, 2]
    assert classes._rwl_strip_terminator([1, 2, -9999]) == [1, 2]
    assert classes._rwl_strip_terminator([1, 2, 3]) == [1, 2, 3]
    assert classes._rwl_strip_terminator([]) == []


def _db_with_one():
    db = classes.DataBase('s')
    db.add_seq('s', {'A': classes.Sequence(
        {'KeyCode': 'A', 'DateBegin': 1, 'measurements': [1, 2, 3]})})
    return db


def test_database_get_returns_the_sequence():
    db = _db_with_one()
    got = db.get('s', 'A')
    assert got is not None and got.KeyCode() == 'A'


def test_database_get_missing_key_returns_none_without_autoviv():
    db = _db_with_one()
    assert db.get('s', 'typo') is None
    assert db.get('s', 'typo', default=0) == 0
    # a bare self.base['s']['typo'] would have created an empty entry
    assert db.count_seqs('s') == 1
    assert 'typo' not in db.base['s']


def test_database_get_missing_stack_returns_default():
    db = _db_with_one()
    assert db.get('nope', 'A') is None
    assert 'nope' not in db.base

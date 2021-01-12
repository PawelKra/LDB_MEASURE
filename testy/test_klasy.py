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

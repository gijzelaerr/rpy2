import pytest
import math
import pytz
import sys
import rpy2.robjects as robjects
from rpy2.robjects import conversion
import rpy2.rinterface as rinterface

from collections import OrderedDict
from datetime import datetime

has_pandas = True
try:
    import pandas
    import numpy
    has_pandas = True
except:
    has_pandas = False

if has_pandas:
    import rpy2.robjects.pandas2ri as rpyp

from rpy2.robjects import default_converter
from rpy2.robjects.conversion import Converter, localconverter
    
@pytest.mark.skipif(not has_pandas, reason='Package pandas is not installed.')
class TestPandasConversions(object):

    def testActivate(self):
        #FIXME: is the following still making sense ?
        assert rpyp.py2rpy != robjects.conversion.py2rpy
        l = len(robjects.conversion.py2rpy.registry)
        k = set(robjects.conversion.py2rpy.registry.keys())
        rpyp.activate()
        assert len(conversion.py2rpy.registry) > l
        rpyp.deactivate()
        assert len(conversion.py2rpy.registry) == l
        assert set(conversion.py2rpy.registry.keys()) == k

    def testActivateTwice(self):
        #FIXME: is the following still making sense ?
        assert rpyp.py2rpy != robjects.conversion.py2rpy
        l = len(robjects.conversion.py2rpy.registry)
        k = set(robjects.conversion.py2rpy.registry.keys())
        rpyp.activate()
        rpyp.deactivate()
        rpyp.activate()
        assert len(conversion.py2rpy.registry) > l
        rpyp.deactivate()
        assert len(conversion.py2rpy.registry) == l
        assert set(conversion.py2rpy.registry.keys()) == k

    def test_dataframe(self):
        # Content for test data frame
        l = (
            ('b', numpy.array([True, False, True], dtype=numpy.bool_)),
            ('i', numpy.array([1, 2, 3], dtype='i')),
            ('f', numpy.array([1, 2, 3], dtype='f')),
            # ('s', numpy.array([b'b', b'c', b'd'], dtype='S1')),
            ('u', numpy.array([u'a', u'b', u'c'], dtype='U')),
            ('dates', [datetime(2012, 5, 2), 
                       datetime(2012, 6, 3), 
                       datetime(2012, 7, 1)])
        )
        od = OrderedDict(l)
        # Pandas data frame
        pd_df = pandas.core.frame.DataFrame(od)
        # Convert to R
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_df = robjects.conversion.py2rpy(pd_df)
        assert pd_df.shape[0] == rp_df.nrow
        assert pd_df.shape[1] == rp_df.ncol
        # assert tuple(rp_df.rx2('s')) == (b'b', b'c', b'd')
        assert tuple(rp_df.rx2('u')) == ('a', 'b', 'c')
        
    def test_series(self):
        Series = pandas.core.series.Series
        s = Series(numpy.random.randn(5), index=['a', 'b', 'c', 'd', 'e'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        assert isinstance(rp_s, rinterface.FloatSexpVector)

    @pytest.mark.parametrize('dtype',
                             ('i', numpy.int32, numpy.int64,
                              pandas.Int32Dtype, pandas.Int64Dtype))
    def test_series_int(self, dtype):
        Series = pandas.core.series.Series
        s = Series(range(5),
                   index=['a', 'b', 'c', 'd', 'e'],
                   dtype=dtype)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        assert isinstance(rp_s, rinterface.IntSexpVector)
    
    def test_series_obj_str(self):
        Series = pandas.core.series.Series
        s = Series(['x', 'y', 'z'], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        assert isinstance(rp_s, rinterface.StrSexpVector)

        s = Series(['x', 'y', None], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        assert isinstance(rp_s, rinterface.StrSexpVector)


    def test_series_obj_mixed(self):
        Series = pandas.core.series.Series
        s = Series(['x', 1, False], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            with pytest.raises(ValueError):
                rp_s = robjects.conversion.py2rpy(s)

        s = Series(['x', 1, None], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            with pytest.raises(ValueError):
                rp_s = robjects.conversion.py2rpy(s)


    def test_series_obj_bool(self):
        Series = pandas.core.series.Series
        s = Series([True, False, True], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        assert isinstance(rp_s, rinterface.BoolSexpVector)

        s = Series([True, False, None], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        assert isinstance(rp_s, rinterface.BoolSexpVector)


    def test_series_obj_allnone(self):
        Series = pandas.core.series.Series
        s = Series([None, None, None], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        assert isinstance(rp_s, rinterface.BoolSexpVector)


    def test_series_issue264(self):
        Series = pandas.core.series.Series
        s = Series(('a', 'b', 'c', 'd', 'e'),
                   index=pandas.Int64Index([0,1,2,3,4]))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        # segfault before the fix
        str(rp_s)
        assert isinstance(rp_s, rinterface.StrSexpVector)

    def test_object2String(self):
        series = pandas.Series(["a","b","c","a"], dtype="O")
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(series)
            assert isinstance(rp_c, rinterface.StrSexpVector)

    def test_object2String_with_None(self):
        series = pandas.Series([None, "a","b","c","a"], dtype="O")
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(series)
            assert isinstance(rp_c, rinterface.StrSexpVector)

    def test_factor2Category(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a'))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.rpy2py(factor)
        assert isinstance(rp_c, pandas.Categorical)

    def test_factorwithNA2Category(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a', None))
        assert factor[3] == rinterface.na_values.NA_Integer
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.rpy2py(factor)
        assert isinstance(rp_c, pandas.Categorical)
        assert math.isnan(rp_c[3])

    def test_orderedFactor2Category(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a'), ordered=True)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.rpy2py(factor)
        assert isinstance(rp_c, pandas.Categorical)

    def test_category2Factor(self):
        category = pandas.Series(["a","b","c","a"], dtype="category")
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(category)
            assert isinstance(rp_c, robjects.vectors.FactorVector)

    def test_categorywithNA2Factor(self):
        category = pandas.Series(['a', 'b', 'c', numpy.nan], dtype='category')
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(category)
            assert isinstance(rp_c, robjects.vectors.FactorVector)
        assert rp_c[3] == rinterface.NA_Integer

    def test_orderedCategory2Factor(self):
        category = pandas.Series(pandas.Categorical(['a','b','c','a'],
                                                    categories=['a','b','c'],
                                                    ordered=True))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(category)
            assert isinstance(rp_c, robjects.vectors.FactorVector)

    def test_datetime2posixct(self):
        datetime = pandas.Series(
            pandas.date_range('2017-01-01 00:00:00.234',
                              periods=20, freq='ms', tz='UTC')
        )
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(datetime)
            assert isinstance(rp_c, robjects.vectors.POSIXct)
            assert int(rp_c[0]) == 1483228800
            assert int(rp_c[1]) == 1483228800
            assert rp_c[0] != rp_c[1]

    def test_timeR2Pandas(self):
        tzone = rpyp.get_timezone()
        dt = [datetime(1960, 5, 2),
              datetime(1970, 6, 3), 
              datetime(2012, 7, 1)]
        dt = [x.replace(tzinfo=tzone) for x in dt]
        # fix the time
        ts = [x.timestamp() for x in dt]
        # Create an R POSIXct vector.
        r_time = robjects.baseenv['as.POSIXct'](
            rinterface.FloatSexpVector(ts),
            origin=rinterface.StrSexpVector(('1970-01-01',))
        )

        # Convert R POSIXct vector to pandas-compatible vector
        with localconverter(default_converter + rpyp.converter) as cv:
            py_time = robjects.conversion.rpy2py(r_time)

        # Check that the round trip did not introduce changes
        for expected, obtained in zip(dt, py_time):
            assert expected == obtained.to_pydatetime()

    def test_repr(self):
        # this should go to testVector, with other tests for repr()
        l = (('b', numpy.array([True, False, True], dtype=numpy.bool_)),
             ('i', numpy.array([1, 2, 3], dtype="i")),
             ('f', numpy.array([1, 2, 3], dtype="f")),
             ('s', numpy.array(["a", "b", "c"], dtype="S")),
             ('u', numpy.array([u"a", u"b", u"c"], dtype="U")))
        od = OrderedDict(l)
        pd_df = pandas.core.frame.DataFrame(od)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_df = robjects.conversion.py2rpy(pd_df)
        s = repr(rp_df)  # used to fail with a TypeError.
        s = s.split('\n')
        repr_str = ('[BoolSex..., IntSexp..., FloatSe..., '
                    'ByteSex..., StrSexp...]')
        assert repr_str == s[1].strip()

        # Try again with the conversion still active.
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_df = robjects.conversion.py2rpy(pd_df)
            s = repr(rp_df)  # used to fail with a TypeError.
        s = s.split('\n')
        assert repr_str == s[1].strip()

    def test_ri2pandas(self):
        rdataf = robjects.r('data.frame(a=1:2, '
                            '           b=I(c("a", "b")), '
                            '           c=c("a", "b"))')
        with localconverter(default_converter + rpyp.converter) as cv:
            pandas_df = robjects.conversion.rpy2py(rdataf)

        assert isinstance(pandas_df, pandas.DataFrame)
        assert ('a', 'b', 'c') == tuple(pandas_df.keys())
        assert pandas_df['a'].dtype in (numpy.dtype('int32'),
                                        numpy.dtype('int64'))
        assert pandas_df['b'].dtype == numpy.dtype('O')
        assert isinstance(pandas_df['c'].dtype,
                          pandas.api.types.CategoricalDtype)

    def test_ri2pandas(self):
        rdataf = robjects.r('data.frame(a=1:2, '
                            '           row.names=c("a", "b"))')
        with localconverter(default_converter + rpyp.converter) as cv:
            pandas_df = cv.rpy2py(rdataf)
        assert all(x == y for x, y in zip(rdataf.rownames, pandas_df.index))

    def test_ri2pandas_issue207(self):
        d = robjects.DataFrame({'x': 1})
        with localconverter(default_converter + rpyp.converter) as cv:
            try:
                ok = True
                robjects.globalenv['d'] = d
            except ValueError:
                ok = False
            finally:
                if 'd' in robjects.globalenv:
                    del(robjects.globalenv['d'])
        assert ok

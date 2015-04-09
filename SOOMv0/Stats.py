#
#   The contents of this file are subject to the HACOS License Version 1.2
#   (the "License"); you may not use this file except in compliance with
#   the License.  Software distributed under the License is distributed
#   on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
#   implied. See the LICENSE file for the specific language governing
#   rights and limitations under the License.  The Original Software
#   is "NetEpi Analysis". The Initial Developer of the Original
#   Software is the Health Administration Corporation, incorporated in
#   the State of New South Wales, Australia.
#
#   Copyright (C) 2004,2005 Health Administration Corporation. 
#   All Rights Reserved.
#
# $Id: Stats.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Stats.py,v $

import Numeric, MA, math

def mask_nonpositive_weights(wgtvector):
    if MA.isMaskedArray(wgtvector):
        return MA.masked_where(MA.less_equal(wgtvector,0.0),wgtvector)
    else:
        return MA.masked_where(Numeric.less_equal(wgtvector,0.0),wgtvector)

def zero_nonpositive_weights(wgtvector):
    if MA.isMaskedArray(wgtvector):
        return MA.choose(MA.less(wgtvector,0.0),(wgtvector,0.0))
    else:
        return Numeric.choose(Numeric.less(wgtvector,0.0),(wgtvector,0.0))

def mask_where_masked(a, b):
    """
    Apply b's mask to a if b has a mask.
    """
    if MA.isMaskedArray(b):
        mask = b.mask()
        if mask is not None:
            return MA.masked_where(mask, a)
    return a

def mask_and_compress(datavector, wgtvector):
    """
    Mutually apply each other's masks and compress the resulting arrays.
    """
    datavector = mask_where_masked(datavector, wgtvector)
    wgtvector = mask_where_masked(wgtvector, datavector)
    if MA.isMaskedArray(datavector):
        datavector = datavector.compressed()
    if MA.isMaskedArray(wgtvector):
        wgtvector = wgtvector.compressed()
    assert len(wgtvector) == len(datavector), 'datavector and wgtvector are different lengths after compressing masked values'
    return datavector, wgtvector

def get_alpha(conflev):
    try:
        conflev = float(conflev)
        if conflev < 0.5 or conflev >= 1.0:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError('conflev (confidence level) must be a proportion between 0.5 and 1.0')
    return 1.0 - conflev

def nonmissing(datavector):
    """
    Returns the number of non-missing elements in the rank-1 Numpy
    or MA array (vector) passed as the only argument.
    """
    if MA.isMaskedArray(datavector):
        return datavector.count()
    else:
        return len(datavector)

def missing(datavector):
    """
    Returns the number of missing elements in the rank-1 MA array
    (vector) passed as the only argument. Numpy arrays do not have 
    missing values by definition.
    """
    if MA.isMaskedArray(datavector):
        return datavector.size() - datavector.count()
    else:
        return 0

def assert_same_shape(datavector, wgtvector):
    if datavector.shape[0] != wgtvector.shape[0]:
        raise ValueError('datavector and wgtvector must have the same length (%d vs %d)' % 
                         (datavector.shape[0], wgtvector.shape[0]))


def wnonmissing(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the number of non-missing elements in the rank-1 Numpy
    or MA array (vector) passed as the first argument. Elements of
    datavector are regarded as missing if they are masked as missing
    (in the case of an MA array) or if the associated weight is
    missing or negative.  The optional second Boolean named argument
    causes non-positive weights to be regarded as missing.
    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector = mask_where_masked(datavector, wgtvector)

    if MA.isMaskedArray(datavector):
        return datavector.count()
    else:
        return len(datavector)

def wmissing(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the number of missing elements in the rank-1 Numpy or
    MA array (vector) passed as the first argument. Elements of
    datavector are regarded as missing if they are masked as missing
    (in the case of an MA array) or if the associated weight is
    missing or negative.  The optional second Boolean argument
    causes non-positive weights to be regarded as missing.
    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector = mask_where_masked(datavector, wgtvector)

    if MA.isMaskedArray(datavector):
        return datavector.size() - datavector.count()
    else:
        return 0

def aminimum(datavector):
    """
    Returns the minimum value of non-missing elements in the rank-1
    Numpy or MA array (vector) passed as the only argument.

    Note - Numeric.minimum compares two or more arrays returning
    an array, whereas MA.minimum works like the builtin min()
    and returns a scalar, but also copes with missing values,
    which is what we want.
    """
    if nonmissing(datavector) == 0:
        return None
    return float(MA.minimum(datavector))

def amaximum(datavector):
    """
    Returns the maximum value of non-missing elements in the rank-1
    Numpy array (vector) passed as the only argument.

    Note - see aminimum comment.
    """
    if nonmissing(datavector) == 0:
        return None
    return float(MA.maximum(datavector))

def wminimum(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the minimum value of non-missing elements in the rank-1
    Numpy or MA array (vector) passed as the only argument.

    Note - Numeric.minimum compares two or more arrays returning
    an array, whereas MA.minimum works like the builtin min()
    and returns a scalar, but also copes with missing values,
    which is what we want.

    Elements of datavector are 
    regarded as missing if they are masked as missing (in the case
    of an MA array) or if the associated weight is missing or negative. 
    The optional second Boolean argument causes non-positive weights
    to be regarded as missing.
    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector = mask_where_masked(datavector, wgtvector)

    if nonmissing(datavector) == 0:
        return None
    return float(MA.minimum(datavector))

def wmaximum(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the maximum value of non-missing elements in the rank-1
    Numpy array (vector) passed as the only argument.

    Note - see aminimum comment.

    Elements of datavector are 
    regarded as missing if they are masked as missing (in the case
    of an MA array) or if the associated weight is missing or negative. 
    The optional second Boolean argument causes non-positive weights
    to be regarded as missing.
    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector = mask_where_masked(datavector, wgtvector)

    if nonmissing(datavector) == 0:
        return None
    return float(MA.maximum(datavector))

def arange(datavector):
    "Returns the differences betwen the maximum and the minimum"
    if nonmissing(datavector) == 0:
        return None
    return float(MA.maximum(datavector)) - float(MA.minimum(datavector))

def wrange(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the difference between the maximum and the minimum

    Elements of datavector are 
    regarded as missing if they are masked as missing (in the case
    of an MA array) or if the associated weight is missing or negative. 
    The optional second Boolean argument causes non-positive weights
    to be regarded as missing.
    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector = mask_where_masked(datavector, wgtvector)

    if nonmissing(datavector) == 0:
        return None

    return float(MA.maximum(datavector)) - float(MA.minimum(datavector))

def asum(datavector):
    """
    Returns the sum of non-missing values in the Numpy or MA rank-1
    array passed as the only argument.
    """
    if nonmissing(datavector) == 0:
        return None
    return MA.add.reduce(datavector)

def wsum(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the weighted sum of the rank-1 array (vector) passed
    as the first argument, with a vector of weights with the same
    number of elements as the first argument.

    Elements of datavector are 
    regarded as missing if they are masked as missing (in the case
    of an MA array) or if the associated weight is missing or negative. 
    The optional second Boolean argument causes non-positive weights
    to be regarded as missing.

    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector = mask_where_masked(datavector, wgtvector)

    if nonmissing(datavector) == 0:
        return None

    if MA.isMaskedArray(datavector) or MA.isMaskedArray(wgtvector):
        return MA.add.reduce(datavector * wgtvector)
    else:
        return Numeric.add.reduce(datavector * wgtvector)

def amean(datavector):
    """
    Returns the arithmetic mean of the rank-1 Numpy array (vector)
    passed as the only argument.
    """
    n = nonmissing(datavector)
    if n == 0:
        return None
    return float(MA.add.reduce(datavector))/float(n)

def ameancl(datavector,conflev=0.95):
    """
    Returns a 3-tuple of a) the arithmetic mean of the rank-1 Numpy
    array (vector) passed as the first argument, b) and c) the lower
    and upper two-sided confidence limits using alpha of conflev.
    """
    alpha = get_alpha(conflev)

    n = nonmissing(datavector)
    if n == 0:
        return (None,None,None)
    elif n == 1:
        x = float(MA.add.reduce(datavector))/float(n)
        return (x,None,None)
    else:
        import rpy
        s = stderr(datavector)
        x = float(MA.add.reduce(datavector))/float(n)
        t = rpy.r.qt(1.0 - alpha/2.0, n - 1)
        return (x, x - t*s, x + t*s)

def geomean(datavector):
    """
    Returns the geometric mean of the rank-1 Numpy array (vector)
    passed as the only argument.
    """
    n = nonmissing(datavector)
    if n == 0:
        return None
    sum = MA.add.reduce(MA.log(datavector))
    return MA.power(MA.e,float(sum)/float(n))


def wamean(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the weighted arithmetic mean of the rank-1 array (vector)
    passed as the first argument, with a vector of weights with
    the same number of elements as the second argument.

    Elements of datavector are regarded as missing if they are masked
    as missing (in the case of an MA array) or if the associated
    weight is missing or negative.  The optional second Boolean
    argument causes non-positive weights to be regarded as missing.
    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector, wgtvector = mask_and_compress(datavector, wgtvector)

    if len(datavector) == 0:
        return None

    sum = float(Numeric.add.reduce(datavector * wgtvector))
    sumwgt = float(Numeric.add.reduce(wgtvector))
    if sumwgt != 0.0:
        return float(sum)/float(sumwgt)
    else:
        return None

def wameancl(datavector,wgtvector,conflev=0.95,exclude_nonpositive_weights=False):
    """
    Returns a 3-tuple of a) the weighted arithmetic mean of the
    rank-1 array (vector) passed as the first argument, with
    a vector of weights with the same number of elements as the
    second argument; b) the lower and upper confidence limits for
    the mean given the alpha level specified by conflev.

    Elements of datavector are regarded as missing if they are masked
    as missing (in the case of an MA array) or if the associated
    weight is missing or negative.  The optional second Boolean
    argument causes non-positive weights to be regarded as missing.
    """
    alpha = get_alpha(conflev)

    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector, wgtvector = mask_and_compress(datavector, wgtvector)

    n = len(datavector)
    if n == 0:
        return (None,None,None)

    sum = float(Numeric.add.reduce(datavector * wgtvector))
    sumwgt = float(Numeric.add.reduce(wgtvector))
    if sumwgt == 0.0:
        return (None,None,None)
    if n == 1:
        x = float(sum)/float(sumwgt)
        return (x,None,None)
    else:
        x = float(sum)/float(sumwgt)
        import rpy
        s = wstderr(datavector,wgtvector,exclude_nonpositive_weights=exclude_nonpositive_weights)
        t = rpy.r.qt(1.0 - alpha/2.0, n - 1)
        return (x, x - t*s, x + t*s)

def wgeomean(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the weighted geometric mean of the rank-1 array (vector)
    passed as the first argument, with a vector of weights with
    the same number of elements as the second argument.

    Elements of datavector are 
    regarded as missing if they are masked as missing (in the case
    of an MA array) or if the associated weight is missing or negative. 
    The optional second Boolean argument causes non-positive weights
    to be regarded as missing.

    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector, wgtvector = mask_and_compress(datavector, wgtvector)

    n = len(datavector)
    if n == 0:
        return None

    sum = MA.add.reduce(MA.log(datavector))
    return MA.power(MA.e,float(sum)/float(n))

def wn(wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the sum of the non-negative weights passed as the
    first argument. The optional second Boolean argument causes
    non-positive weights to be considered as missing - should give
    the same answers.
    """

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    if nonmissing(wgtvector) == 0:
        return 0

    return float(MA.add.reduce(wgtvector))


def quantiles(datavector,p=None,defn=5):
    """
    Returns the p quantiles of the rank-1 passed array.

    p is a list or tuple of values between 0 and 1, 
    a tuple of corresponding quantiles is returned.

    Optional arguments are:
    1) definitions of quantiles are as used by SAS, defaults to
    definition 1 (as does SAS).
    See http://v9doc.sas.com/cgi-bin/sasdoc/cgigdoc?file=../proc.hlp/tw5520statapp-formulas.htm
    Default is 5 as used by SAS
    """

    p_error = "p argument must be a number between 0 and 1 (inclusive), or a list or tuple of such numbers."
    pvals = []
    for p_val in p:
        try:
            pval = float(p_val)
        except:
            raise ValueError, p_error 
        if pval < 0.0 or pval > 1.0:
            raise ValueError, p_error
        pvals.append(pval) 
    quantiles = [None] * len(pvals)

    defn_error = "defn argument must be an integer between 1 and 5 inclusive"
    try:
        defn = int(defn)
    except:
        raise ValueError, defn_error
    if defn < 1 or defn > 5:
        raise ValueError, defn_error


    if MA.isMaskedArray(datavector):
        datavector = datavector.compressed()

    datavector = Numeric.sort(datavector)

    n = datavector.shape[0]
    if n == 0:
        return tuple(quantiles)
    if n == 1:
        d = datavector[0]
        return tuple([d for i in quantiles])

    for p_index, p in enumerate(pvals):
        if defn == 4:
            np = (n + 1) * p
        else:
            np = n * p

        j = int(np)
        g = np - j

        if defn == 1:
            if j > 0:
                j -= 1
                if j <= n - 2:
                    quantile = float(((1-g)*datavector[j]) + (g*datavector[j+1]))
                else:
                    quantile = float(datavector[j])
            else:
                # quantile = float(((1-g)*datavector[j]) + (g*datavector[j]))
                quantile = float(datavector[j])
        elif defn == 2:
            i = int(np + 0.5)
            if i > 0:
                i -= 1
            if g != 0.5:
                quantile = float(datavector[i])
            elif g == 0.5 and j % 2 == 0:
                if j > 0:
                    j -= 1
                quantile = float(datavector[j])
            elif g == 0.5 and j % 2 != 0:
                quantile = float(datavector[j])
        elif defn == 3:
            if g == 0.0:
                if j > 0:
                    j -= 1
                quantile = float(datavector[j])
            else:
                quantile = float(datavector[j])
        elif defn == 4:
            if j > 0:
                j -= 1
                if j <= n - 2:
                    quantile = float(((1-g)*datavector[j]) + (g*datavector[j+1]))
                elif j <= n-1:
                    quantile = float(datavector[j])
                else:
                    quantile = float(datavector[j-1])
            else:
                quantile = float(datavector[j])
        elif defn == 5:
            if j > 0:
                j -= 1
                if j <= n - 2:
                    if g == 0.0:
                        quantile = 0.5 * ( datavector[j] + datavector[j+1] )       
                    else:
                        quantile = float(datavector[j+1])
                else:
                    quantile = float(datavector[j])
            else:
                quantile = float(datavector[j])
        quantiles[p_index] = quantile
    return tuple(quantiles)    

def quantile(datavector,p=None,defn=5):
    """
    Returns the p quantile(s) of the rank-1 passed array.

    If p is a single value between 0 and 1, a single quantile
    is returned.

    If p is a list or tuple of values between 0 and 1, a tuple of
    corresponding quantiles is returned.

    Optional arguments are:
    1) definitions of quantiles are as used by SAS, defaults to
    definition 1 (as does SAS).
    See http://v9doc.sas.com/cgi-bin/sasdoc/cgigdoc?file=../proc.hlp/tw5520statapp-formulas.htm
    Default is 5 as used by SAS
    """
    return quantiles(datavector,p=(p,),defn=defn)[0]

def median(datavector,defn=5):
    return quantile(datavector,p=0.5,defn=defn)

def wquantiles(datavector,wgtvector,p=None,exclude_nonpositive_weights=False):
    """
    Returns the weighted p quantile(s) of the rank-1 passed array,
    where wgtvector gives the weights.

    p is a list or tuple of values between 0 and 1
    a tuple of corresponding quantiles is returned.

    Formula is as used by SAS.
    See http://v9doc.sas.com/cgi-bin/sasdoc/cgigdoc?file=../proc.hlp/tw5520statapp-formulas.htm

    Optional boolean argument exclude_nonpositive_weights causes
    non-positive weights to be treated as missing if True. The
    default (False) causes treats negative weights like zero weights
    and includes them in the calculations.
    """
    p_error = "p argument must be a number between 0 and 1 (inclusive), or a list or tuple of such numbers."
    pvals = []
    for p_val in p:
        try:
            pval = float(p_val)
        except:
            raise ValueError, p_error 
        if pval < 0.0 or pval > 1.0:
            raise ValueError, p_error
        pvals.append(pval) 
    quantiles = [None] * len(pvals)

    assert_same_shape(datavector, wgtvector)

    if datavector.shape[0] == 0:
        return quantiles

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector, wgtvector = mask_and_compress(datavector, wgtvector)

    sort_arg = Numeric.argsort(datavector)
    datavector = Numeric.take(datavector,sort_arg)
    wgtvector = Numeric.take(wgtvector,sort_arg)

    n = datavector.shape[0]

    if n == 1:
        d = float(datavector[0])
        return tuple([d for i in quantiles])

    # Now accumulate the weights
    accumulated_wgtvector = Numeric.add.accumulate(wgtvector)
    if type(accumulated_wgtvector) not in (float,int,long): 
        W = accumulated_wgtvector[-1] # sum of weights
    else:
        W = accumulated_wgtvector

    for p_index in range(len(pvals)):
        p = pvals[p_index]

        if float(W) == 0.0:
            quantiles[p_index] = None
        else:    

            pW = p * W

            ge_vector = Numeric.greater_equal(accumulated_wgtvector, pW)
            le_vector = Numeric.less_equal(accumulated_wgtvector, pW)

            if Numeric.sum(ge_vector) > 0:
                # we have an exact match...
                first_two_accum_wgts = (Numeric.compress(le_vector,accumulated_wgtvector)[-1],
                                        Numeric.compress(ge_vector,accumulated_wgtvector)[0])
                first_two_accum_values = (Numeric.compress(le_vector,datavector)[-1],
                                        Numeric.compress(ge_vector,datavector)[0])
                if first_two_accum_wgts[0] == pW:
                    quantiles[p_index] = 0.5 * float(Numeric.sum(first_two_accum_values))
                elif first_two_accum_wgts[0] < pW and first_two_accum_wgts[1]:
                    quantiles[p_index] = float(first_two_accum_values[1])
    return tuple(quantiles)    

def wquantile(datavector,wgtvector,p=None,exclude_nonpositive_weights=False):
    """
    Returns the weighted p quantile of the rank-1 passed array,
    where wgtvector gives the weights.

    Formula is as used by SAS.
    See http://v9doc.sas.com/cgi-bin/sasdoc/cgigdoc?file=../proc.hlp/tw5520statapp-formulas.htm

    Optional boolean argument exclude_nonpositive_weights causes
    non-positive weights to be treated as missing if True. The
    default (False) causes treats negative weights like zero weights
    and includes them in the calculations.
    """
    return wquantiles(datavector,wgtvector,p=(p,),exclude_nonpositive_weights=exclude_nonpositive_weights)[0]

def wmedian(datavector,wgtvector,exclude_nonpositive_weights=False):
    return wquantile(datavector,wgtvector,p=0.5,exclude_nonpositive_weights=exclude_nonpositive_weights)

def variance(datavector,df=None):
    """ 
    Returns the sample or population variance - same as variance
    in SAS with VARDEF=DF or VARDEF=N, depending on whether df='DF'
    (sample) or 'N' (population)
    """
    if df not in ('DF','N'):
        raise ValueError, 'DF argument must be DF or N'

    # first calculate n
    n = nonmissing(datavector)
    if (n < 2 and df == 'DF') or n is None:
        return None
    elif n < 1:
        return None
    else:
        pass

    # then calculate the mean
    mean = amean(datavector)

    if mean is None:
        return None

    # now the sum of squares about the mean

    if MA.isMaskedArray(datavector):
        sumsquares = MA.add.reduce(MA.power((datavector - mean),2))
    else:
        sumsquares = Numeric.add.reduce(Numeric.power((datavector - mean),2))

    if df == 'DF':
        return sumsquares/float((n-1))
    else:
        return sumsquares/float(n)

def samplevar(datavector):
    """
    Returns sample variance - same as variance in SAS with VARDEF=DF
    """
    return variance(datavector,df='DF')

def populationvar(datavector):
    """
    Returns population variance - same as variance in SAS with VARDEF=N
    """
    return variance(datavector,df='N')

def wvariance(datavector,wgtvector,df=None,exclude_nonpositive_weights=False):
    """
    Returns the weighted sample or population variance - same as
    variance in SAS with VARDEF=WDF or VARDEF=WEIGHT, depending on
    whether df = 'WDF' (sample) or 'WEIGHT' (population)
    """

    if df not in ('WDF','WEIGHT'):
        raise ValueError, 'DF argument must be WDF or WEIGHT'

    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector, wgtvector = mask_and_compress(datavector, wgtvector)

    # first calculate n
    n = len(datavector)
    if n < 1  or n is None:
        return None

    # then calculate the weighted mean
    sum = float(Numeric.add.reduce(datavector * wgtvector))
    sumwgt = float(Numeric.add.reduce(wgtvector))
    if sumwgt != 0.0:
        wmean = float(sum)/float(sumwgt)
    else:
        return None
    # now the squares about the mean
    squaresaboutmean = Numeric.power((datavector - wmean),2)
    # Now the weighted squares about the mean
    sumsquares = Numeric.add.reduce(wgtvector * squaresaboutmean)
    # now d
    if df == 'WDF':
        d = float(Numeric.add.reduce(wgtvector)) - 1.0
    else:
        d = float(Numeric.add.reduce(wgtvector))
    if d > 0:
        return float(sumsquares)/d
    else:
        return None

def wsamplevar(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the weighted sample variance - - same as variance in
    SAS with VARDEF=WDF
    """
    return wvariance(datavector,wgtvector,df='WDF',exclude_nonpositive_weights=exclude_nonpositive_weights)

def wpopulationvar(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns the weighted population variance - - same as variance
    in SAS with VARDEF=WEIGHT
    """
    return wvariance(datavector,wgtvector,df='WEIGHT',exclude_nonpositive_weights=exclude_nonpositive_weights)

def sample_stddev(datavector):
    svar = variance(datavector,df='DF')
    if svar is None:
        return None
    else:
        return svar**0.5

def wsample_stddev(datavector,wgtvector,exclude_nonpositive_weights=False):

    wsvar = wvariance(datavector,wgtvector,df='WDF',exclude_nonpositive_weights=exclude_nonpositive_weights)

    if wsvar is None:
        return None
    else:
        return wsvar**0.5

def population_stddev(datavector):
    pvar = variance(datavector,df='N')
    if pvar is None:
        return None
    else:
        return pvar**0.5

def wpopulation_stddev(datavector,wgtvector,exclude_nonpositive_weights=False):

    wpvar = wvariance(datavector,wgtvector,df='WEIGHT',exclude_nonpositive_weights=exclude_nonpositive_weights)

    if wpvar is None:
        return None
    else:
        return wpvar**0.5

def cv(datavector,df=None):
    """ 
    Returns the percent co-efficient of variation - same as CV in
    SAS with VARDEF=DF or VARDEF=N, depending on whether df='DF'
    (sample) or 'N' (population)
    """
    if df not in ('DF','N'):
        raise ValueError, 'DF argument must be DF or N'

    # first calculate s
    s2 = variance(datavector,df=df)
    if s2 == None:
        return None
    else:
        s = s2**0.5

    # then calculate the mean
    mean = amean(datavector)

    if mean is None or mean == 0:
        return None

    # now the CV
    return (100.0 * s)/float(mean)

def sample_cv(datavector):
    return cv(datavector,df="DF")

def population_cv(datavector):
    return cv(datavector,df="N")

def wcv(datavector,wgtvector,df=None,exclude_nonpositive_weights=True):

    if df not in ('WDF','WEIGHT'):
        raise ValueError, 'DF argument must be WDF or WEIGHT'

    # first calculate s
    s2 = wvariance(datavector,wgtvector,df=df,exclude_nonpositive_weights=exclude_nonpositive_weights)
    if s2 == None:
        return None
    else:
        s = s2**0.5

    # then calculate the mean
    mean = wamean(datavector,wgtvector,exclude_nonpositive_weights=exclude_nonpositive_weights)

    if mean is None or mean == 0:
        return None

    # now the CV
    return (100.0 * s)/float(mean)

def wsample_cv(datavector,wgtvector,exclude_nonpositive_weights=False):
    return wcv(datavector,wgtvector,df="WDF",exclude_nonpositive_weights=exclude_nonpositive_weights)

def wpopulation_cv(datavector,wgtvector,exclude_nonpositive_weights=False):
    return wcv(datavector,wgtvector,df="WEIGHT",exclude_nonpositive_weights=exclude_nonpositive_weights)

def stderr(datavector):
    """
    Returns standard error of the sample mean.
    """
    s2 = variance(datavector,df="DF")
    n = nonmissing(datavector)
    if s2 == None or n == None or n == 0:
        return None
    else:
        return s2**0.5 / n**0.5    

def wstderr(datavector,wgtvector,exclude_nonpositive_weights=False):
    """
    Returns weighted standard error of the sample mean.
    """
    assert_same_shape(datavector, wgtvector)

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    datavector, wgtvector = mask_and_compress(datavector, wgtvector)

    # first calculate n
    n = len(datavector)
    if n < 1  or n is None:
        return None

    # then calculate the weighted mean
    sum = float(Numeric.add.reduce(datavector * wgtvector))
    sumwgt = float(Numeric.add.reduce(wgtvector))
    if sumwgt != 0.0:
        wmean = float(sum)/float(sumwgt)
    else:
        return None
    # now the squares about the mean
    squaresaboutmean = Numeric.power((datavector - wmean),2)
    # Now the weighted squares about the mean
    sumsquares = Numeric.add.reduce(wgtvector * squaresaboutmean)
    # now d
    d = float(len(wgtvector)) - 1.0
    if d > 0:
        s2 = float(sumsquares)/d
    else:
        return None

    sumwgt = float(Numeric.add.reduce(wgtvector))

    if s2 == None or n == None or sumwgt == 0:
        return None
    else:
        return s2**0.5 / sumwgt**0.5    

def t(datavector,muzero=0.0):
    """
    Returns Student's T statistic for datavector, given muzero
    (optional, defaults to zero).
    """
    se = stderr(datavector)
    if se == None or se == 0:
        return None
    mean = amean(datavector)
    return float(mean - muzero) / se

def probit(p):
    """
    Returns the inverse of the standard normal cumulative
    distribution function. That is, given probability p (between
    0.0 and 1.0 inclusive), returns standardised deviate z.

    This function was adapted from Python code which appears in a
    paper by Dridi (2003).  The programme code is copyright 2003
    Dridi and Regional Economics Applications Laboratory, University
    of Illinois and is used here with the permission of its author.

    The code in the above paper was in turn based on an algorthim
    developed by Odeh and Evan (1974) as described by Kennedy and
    Gentle (1980). The method uses rational fractions derived from
    Taylor series to approximate the desired value.

    References:

    Dridi, C. (2003): A Short Note on the Numerical Aproximation of
    the Standard Normal Cumulative Distribution and its Inverse,
    Regional Economics Applications Laboratory, University of
    Illinois and Federal Reserve Bank of Chicago. Available at
    http://www2.uiuc.edu/unit/real/d-paper/real03-t-7.pdf or at
    http://econwpa.wustl.edu/eps/comp/papers/0212/0212001.pdf

    Kennedy, W.J and Gentle J.E. (1980): Statistical Computing,
    Marcel Dekker, New York. p93-95.

    Odeh, R.R and Evan, J.O (1974): "Algorithm AS 70: Percentage
    Points of the Normal Distribution", Applied Statistics 23, 96-97
    """

    xp = 0.0
    lim = 1.e-20
    p0 = -0.322232431088
    p1 = -1.0
    p2 = -0.342242088547
    p3 = -0.0204231210245
    p4 = -0.453642210148e-4
    q0 = 0.0993484626060
    q1 = 0.588581570495
    q2 = 0.531103462366
    q3 = 0.103537752850
    q4 = 0.38560700634e-2
    p = float(p)
    if p < 0.0 or p > 1.0:
        raise ValueError, "p must be between 0.0 and 1.0 inclusive"
    elif p < lim or p == 1.0:
        xp = -1.0 / lim
    elif p == 0.5:
        xp = 0.0
    elif p > 0.5:
        p = 1.0 - p
        y = math.sqrt(math.log(1.0 / p**2.0))
        xp = y + ((((y*p4+p3)*y+p2)*y+p1)*y+p0)/((((y*q4+q3)*y+q2)*y+q1)*y+q0)
    elif p < 0.5:
        y = math.sqrt(math.log(1.0 / p**2.0))
        xp = -(y + ((((y*p4+p3)*y+p2)*y+p1)*y+p0)/((((y*q4+q3)*y+q2)*y+q1)*y+q0))
    else:
        raise ValueError, "p must be between 0.0 and 1.0 inclusive"

    if p > 0.5:
        return -xp
    else:
        return xp    

def cdf_gauss_GL(x):
    """
    Returns the probability that an observation from the standard
    normal distribution is less than or equal to x (that is, x must
    be a standard normal deviate).

    The following function was adapted from Python code which appears
    in a paper by Dridi (2003).  The programme code is copyright 2003
    Dridi and Regional Economics Applications Laboratory, University
    of Illinois and is used here with the permission of its author.

    This function uses Gauss-legendre quadrature to provide good
    accuracy in the tails of the distribution, at the expense of
    speed - this function is very slow due to its iterative nature.
    A faster version can be be found in the Cstats.pyx module which
    accompanies this (Stats.py) module.

    References:

    Dridi, C. (2003): A Short Note on the Numerical Aproximation of
    the Standard Normal Cumulative Distribution and its Inverse,
    Regional Economics Applications Laboratory, University of
    Illinois and Federal Reserve Bank of Chicago. Available at
    http://www2.uiuc.edu/unit/real/d-paper/real03-t-7.pdf or at
    http://econwpa.wustl.edu/eps/comp/papers/0212/0212001.pdf
    """
    if x >= 0.0:
        return (1.0 + _GL(0,  x/math.sqrt(2.0))) / 2.0
    else:
        return (1.0 - _GL(0, -x/math.sqrt(2.0))) / 2.0

def _GL(a,b):
    """
    Support function for the cdf_gauss_GL() function, which returns
    the standard normal cumulative distribution using Gauss-Legendre
    quadrature.

    The following function was adapted from Python code which appears
    in a paper by Dridi (2003).  The programme code is copyright 2003
    Dridi and Regional Economics Applications Laboratory, University
    of Illinois and is used here with the permission of its author.

    References:

    Dridi, C. (2003): A Short Note on the Numerical Aproximation of
    the Standard Normal Cumulative Distribution and its Inverse,
    Regional Economics Applications Laboratory, University of
    Illinois and Federal Reserve Bank of Chicago. Available at
    http://www2.uiuc.edu/unit/real/d-paper/real03-t-7.pdf or at
    http://econwpa.wustl.edu/eps/comp/papers/0212/0212001.pdf
    """
    y1=0.0
    y2=0.0
    y3=0.0
    y4=0.0
    y5=0.0

    x1=-math.sqrt(245.0 + 14.0 * math.sqrt(70.0)) / 21.0
    x2=-math.sqrt(245.0 - 14.0 * math.sqrt(70.0)) / 21.0
    x3=0.0
    x4=-x2
    x5=-x1

    w1=(322.0 - 13.0 * math.sqrt(70.0)) / 900.0
    w2=(322.0 + 13.0 * math.sqrt(70.0)) / 900.0
    w3=128.0/225.0
    w4=w2
    w5=w1

    # n=4800 # Original number of iterations used by Dridi
    n = 120 
    s=0.0
    h=(b-a)/n

    for i in range(0,n,1):
        y1=h*x1/2.0+(h+2.0*(a+i*h))/2.0
        y2=h*x2/2.0+(h+2.0*(a+i*h))/2.0
        y3=h*x3/2.0+(h+2.0*(a+i*h))/2.0
        y4=h*x4/2.0+(h+2.0*(a+i*h))/2.0
        y5=h*x5/2.0+(h+2.0*(a+i*h))/2.0
        s=s+h*(w1*_f(y1)+w2*_f(y2)+w3*_f(y3)+w4*_f(y4)+w5*_f(y5))/2.0;
    return s;

def _f(x):
    """
    Support function for the cdf_gauss_GL() function, which returns
    the standard normal cumulative distribution using Gauss-Legendre
    quadrature.

    The following function was adapted from Python code which appears
    in a paper by Dridi (2003).  The programme code is copyright 2003
    Dridi and Regional Economics Applications Laboratory, University
    of Illinois and is used here with the permission of its author.

    References:

    Dridi, C. (2003): A Short Note on the Numerical Aproximation of
    the Standard Normal Cumulative Distribution and its Inverse,
    Regional Economics Applications Laboratory, University of
    Illinois and Federal Reserve Bank of Chicago. Available at
    http://www2.uiuc.edu/unit/real/d-paper/real03-t-7.pdf or at
    http://econwpa.wustl.edu/eps/comp/papers/0212/0212001.pdf
    """
    return (2.0/math.sqrt(math.pi))*math.exp(-x**2.0);

def cdf_gauss_RA(x):
    """
    Returns the standard normal cumulative distribution
    function. That is, given a standardised deviate z, returns a
    probability. The cdf is 0 for all z < -8.29314441 and is 1 for
    all z > 8.29314441.

    The following function was adapted from Python code which appears
    in a paper by Dridi (2003).  The programme code is copyright 2003
    Dridi and Regional Economics Applications Laboratory, University
    of Illinois and is used here with the permission of its author.

    This function uses rational fraction approximations given by
    Cody (1969), using co-efficients provided by Kennedy and Gentle
    (1980, pp91-92). This function is fast, but is only accurate
    for values between -0.5 and 0.75.

    References:

    Cody, W.J. (1969): "Rational Chebyshev Approximations for the
    Error Function", Mathematical Computation 23, 631-638

    Dridi, C. (2003): A Short Note on the Numerical Aproximation of
    the Standard Normal Cumulative Distribution and its Inverse,
    Regional Economics Applications Laboratory, University of
    Illinois and Federal Reserve Bank of Chicago. Available at
    http://www2.uiuc.edu/unit/real/d-paper/real03-t-7.pdf or at
    http://econwpa.wustl.edu/eps/comp/papers/0212/0212001.pdf

    Kennedy, W.J and Gentle J.E. (1980): Statistical Computing,
    Marcel Dekker, New York. p93-95.
    """
    if x > 0.0:
        y=x
    else:
        y=-x

    if y >= 0.0 and y <= 1.5:
        p=(1.0 + erf(y/math.sqrt(2.0)))/2.0
    if y > 1.5:
        p=1.0 - erfc(y/math.sqrt(2.0))/2.0
    if x > 0.0:
        return p
    else:
        return 1.0-p

def erf(x):
    " for 0<x<=0.5 "
    return x*_R1(x)

def erfc(x):
    " for 0.46875<=x<=4.0 "
    if x > 0.46875 and x < 4.0:
        return math.exp(-x**2.0)*(0.5*_R1(x**2.0)+0.2*_R2(x**2.0)+0.3*_R3(x**2.0))
    if x >= 4.0:
        " for x>=4.0 "
        return (math.exp(-x**2.0)/x)*(1.0/math.sqrt(math.pi)+_R3(x**-2.0)/(x**2.0))

def _R1(x):
    N=0.0
    D=0.0
    p=[2.4266795523053175e2,2.1979261618294152e1,6.9963834886191355,-3.5609843701815385e-2]
    q=[2.1505887586986120e2,9.1164905404514901e1,1.5082797630407787e1,1.]
    for i in range(0,3,1):
        N=N+p[i]*x**(2.0*i)
        D=D+q[i]*x**(2.0*i)
    return N/D

def _R2(x):
    N=0.0
    D=0.0
    p=[3.004592610201616005e2,4.519189537118729422e2,3.393208167343436870e2,
       1.529892850469404039e2,4.316222722205673530e1,7.211758250883093659,
       5.641955174789739711e-1,-1.368648573827167067e-7]
    q=[3.004592609569832933e2,7.909509253278980272e2,
       9.313540948506096211e2,6.389802644656311665e2,
       2.775854447439876434e2,7.700015293522947295e1,1.278272731962942351e1,1.]
    for i in range(0,7,1):
        N=N+p[i]*x**(-2.0*i)
        D=D+q[i]*x**(-2.0*i)
    return N/D

def _R3(x):
    N=0.0
    D=0.0
    p=[-2.99610707703542174e-3,-4.94730910623250734e-2,
       -2.26956593539686930e-1,-2.78661308609647788e-1,-2.23192459734184686e-2]
    q=[1.06209230528467918e-2,1.91308926107829841e-1,1.05167510706793207,1.98733201817135256,1.]
    for i in range(0,4,1):
        N=N+p[i]*x**(-2.0*i)
        D=D+q[i]*x**(-2.0*i)
    return N/D

def acceptbin(x, n, p):
    """Support function used by Blaker method in clprop()
       - computes Blaker acceptibility of p when x is observed and X is bin(n, p).
         based on R code by Alan Agresti at 
         http://www.stat.ufl.edu/~aa/cda/R/one_sample/R1/index.html
       """
    import rpy
    p1 = 1.0 - rpy.r.pbinom(x - 1.0, n, p)
    p2 = rpy.r.pbinom(x, n, p)
    a1 = p1 + rpy.r.pbinom(rpy.r.qbinom(p1, n, p) - 1.0, n, p)
    a2 = p2 + 1.0 - rpy.r.pbinom(rpy.r.qbinom(1.0 - p2, n, p), n, p)
    return min(a1, a2)

def propcl(num, den, conflev=0.95, method='blaker',noninteger='reject',epsilon=1e-05):
    """
    Returns a three-tuple of proportion and lower and upper
    confidence limits for a proportion.

    num is the numerator for the proportion, must be zero or a
    positive value

    den is the denominator for the proportion, must be a positive
    value

    nondiscrete= controls what types of values are acceptable for
        num and den if nondiscrete='reject' (the default), then both
        num and den must be integers. If nondiscrete='accept', then
        floating point values are accepted, if nondiscrete='round',
        then values are rounded to the nearest integer, and if
        nondiscrete='truncate', they are truncated to the nearest
        integer.

    conflev= is the two-sided confidence level as a proportion
        (defaults to 0.95).  Must be between 0.5 and 1.0 exclusive

    method= selects the calculation method, must be one of 'wald',
        'modwald', 'wilsonscore', 'fleissquadratic', 'exact',
        'geigy' or 'blaker' Default is 'blaker'

    epsilon= comparison tolerance for Blaker method

    Method details:
        wald - Wald normal aproximation

        modwald - Agresti-Coull modifications of Wald approximation -
            see Agresti A, Coull BA. Approximate is better than exact
            for interval estimation of binomial proportions. The
            American Statistician, 1998.

        wilsonscore - Wilson score approximation,
            based on R code by Alan Agresti at
            http://www.stat.ufl.edu/~aa/cda/R/one_sample/R1/index.html

        fleissquadratic - Score with continuity correction -
            see Fleiss JL. Statustical methods for rates and
            proportions, 2nd Ed. New York: John Wiley and Sons,
            1981. pp (get page numbers)

        exact - Fisher's exact method, based
            on R code by Alan Agresti at
            http://www.stat.ufl.edu/~aa/cda/R/one_sample/R1/index.html

        blaker - method described in Blaker, H. Confidence curves
            and improved exact confidence intervals for discrete
            distributions. Canadian Journal of Statistics 2000;
            28(4):783-798 based on R code by Alan Agresti at
            http://www.stat.ufl.edu/~aa/cda/R/one_sample/R1/index.html

        geigy -  method given in Geigy Scientific Tables Vol
            2 (edited by C. Lentner), Ciba-Geigy Ltd, Basle,
            Switzerland, p221, as reported in Daly, L. Simple SAS
            macros for the calculation of exact binomial and Poisson
            confidence limits. Comput Biol Med 1992; 22(5):351-61

    """
    try:
        if num < 0 or den <= 0 or den < num :
            raise ValueError, "num (numerator) must be zero or a positive integer, and den (denominator) must be a positive integer, and den must be greater than or equal to num"
        num = float(num)
        den = float(den)
    except:
        raise ValueError, "num (numerator) must be zero or a positive integer, and den (denominator) must be a positive integer, and den must be greater than or equal to num"
    nonint = num - int(num) != 0 or den - int(den) != 0
    if noninteger=='reject' and nonint:
        raise ValueError, "When noninteger='reject', num (numerator) and den (denominator) must be integers"
    elif noninteger=='round' and nonint:
        num = round(num)
        den = round(den)
    elif noninteger=='truncate' and nonint:
        num = float(int(num))
        den = float(int(den))
    elif noninteger not in ('accept','reject','round','float'):
        raise ValueError, "noninteger argument must be one of 'reject', 'accept', 'round' or 'truncate'"
    else:
        pass

    alpha = get_alpha(conflev)
    phat = num / den

    if method=='blaker':
        import rpy
        lower = 0.0
        upper = 1.0
        if num != 0.0:
            lower = rpy.r.qbeta(alpha/2.0, num, den - num + 1.0)
            while acceptbin(num, den, lower + epsilon) < alpha:
                lower += epsilon
        if num != den:
            upper = rpy.r.qbeta(1.0 - (alpha/2.0), num + 1.0, den - num)
            while acceptbin(num, den, upper - epsilon) < alpha:
                upper -= epsilon
        return (phat, lower, upper)
    if method=='geigy':
        alpha /= 2.0
        if num == 0.0:
            LL = 0.0
            UL = 1.0 - 10.0**(math.log10(alpha) / den)
            return (phat, LL, UL)
        elif num == den:
            LL = 10.0**(math.log10(alpha) / den)
            UL = 1.0
            return (phat, LL, UL)
        else:
            calpha = probit(1.0 - alpha)
            calphasq = calpha**2
            calpha4thpower = calpha**4
            a = calpha4thpower/18.0 + calphasq*(2.0*den + 1.0)/6.0 + (den + 1.0/3.0)**2.0
            al = num
            ar = num + 1.0
            bl = calpha4thpower/18.0 + calphasq*(4.0*(num - al) + 3.0)/6.0 + 2.0*(al*(3.0*den + 1.0)-den)/3.0 - 2.0/9.0
            cl = calpha4thpower/18.0 + (al-1.0/3.0)**2.0 - calphasq*(2.0*al - 1.0)/6.0
            LL = bl/(2.0*a) - ((bl/(2.0*a))**2.0 - cl/a)**0.5
            br = calpha4thpower/18.0 + (ar-1.0/3.0)**2.0 - calphasq*(2.0*ar-1)/6.0 + 2.0*(ar*(3.0*den + 1.0)-den)/3.0 - 2.0/9.0
            cr = calpha4thpower/18.0 + (ar - 1.0/3.0)**2.0 - calphasq*(2.0*ar - 1)/6.0
            UL = br/(2.0*a) + ((br/(2.0*a))**2.0 - cr/a)**0.5
            return (phat, LL, UL)
    elif method=='exact':
        import rpy
        if num == 0.0:
            LL = 0.0
            UL = 1.0 - (alpha/2.0)**(1.0/den)
        elif num == den:
            LL = (alpha/2.0)**(1.0/den)
            UL = 1.0
        else:
            LL = 1.0 / (1.0 + (den - num + 1) / (num * rpy.r.qf(alpha/2.0, 2.0 * num, 2.0 * (den - num + 1.0))))
            UL = 1.0 / (1.0 + (den - num) / ((num + 1.0) * rpy.r.qf(1.0 - alpha/2.0, 2.0 * (num + 1.0), 2.0 * (den - num))))        
        if LL < 0.0:
            LL = 0.0
        if UL > 1.0:
            UL = 1.0
        return (phat, LL, UL)
    elif method=='wilsonscore':
        zalpha = abs(probit(alpha/2.0))
        zalphasq = zalpha**2
        bound = (zalpha*((phat*(1-phat)+zalphasq/(4*den))/den)**0.5)/(1+zalphasq/den)
        midpoint = (phat+zalphasq/(2*den))/(1+zalphasq/den)
        LL = midpoint - bound
        UL = midpoint + bound
        if LL < 0.0:
            LL = 0.0
        if UL > 1.0:
            UL = 1.0
        return (phat, LL, UL)
    elif method=='fleissquadratic':
        zalpha = abs(probit(alpha/2.0))
        zalphasq = zalpha**2
        LL =  ((2.0*den*phat + zalphasq - 1.0) - zalpha*(zalphasq - (2.0 + 1.0/den) + 4.0*phat*(den*(1.0-phat) + 1.0))**0.5) /  \
              (2.0*(den + zalphasq))
        UL =  ((2.0*den*phat + zalphasq + 1.0) + zalpha*(zalphasq + (2.0 - 1.0/den) + 4.0*phat*(den*(1.0-phat) - 1.0))**0.5) / \
              (2.0*(den + zalphasq))
        if LL < 0.0 or phat == 0.0:
            LL = 0.0
        if UL > 1.0 or phat == 1.0:
            UL = 1.0
        return (phat, LL, UL)
    elif method=='modwald':
        zed = abs(probit(alpha/2.0))
        zedsq = zed**2
        mphat = (num + (zedsq/2.0)) / (den + zedsq)
        qhat = 1.0 - mphat
        semiinterval = zed * ((mphat * qhat / (den + zedsq))**0.5)
        LL = mphat - semiinterval
        UL = mphat + semiinterval
        if LL < 0.0:
            LL = 0.0
        if UL > 1.0:
            UL = 1.0
        return (phat, LL, UL)
    elif method=='wald':
        zed = abs(probit(alpha/2.0))
        qhat = 1.0 - phat
        semiinterval = zed * ((phat * qhat / den)**0.5)
        LL = phat - semiinterval
        UL = phat + semiinterval
        if LL < 0.0:
            LL = 0.0
        if UL > 1.0:
            UL = 1.0
        return (phat, LL, UL)
    else:
        raise ValueError, "method parameter must be one of 'wald', 'modwald', 'wilsonscore', 'fleissquadratic', 'exact', 'geigy' or 'blaker'" 

def ratecl(num, den, conflev=0.95, basepop=100000, method='daly'):
    """
    Returns a 3-tuple of rate and lower and upper confidence limits for a rate (that is
    a number of events divided by the person-time during which the events were observed.
    num is the numerator for the rate, must be zero or a positive value
    den is the denominator for the rate, must be greater than zero
    conflev= is the two-sided confidence level as a proportion (defaults to 0.95). Must be between 0.5 and 1.0 exclusive
    method= selects the calculation method, must be one of 'rg', 'byar','daly' or 'normal'
            Default is 'daly'
    basepop= person-time multiplier, defaults to 100000

    Method details:
        rg - Rothman-Greenland method - see Rothman KJ, Greenland S. Modern Epidemiology. 2nd Ed. Philadelphia:
             Lippincott-Raven, 1998. ppp247-248
        byar - Poisson approximation by Byar, as described in Rothman KJ and Boice JD. Epidemiologic analysis with a 
               programmable calculator. US National Institues of Health Publication No. 79 (find complete reference)
        normal - normal approximation as described in every textbook of epidemiology and biostatistics
        daly - exact Poisson method as described in: Daly, L. Simple SAS macros for the calculation
               of exact binomial and Poisson confidence limits. Comput Biol Med 1992; 22(5):351-61
    """
    try:
        if num - int(num) != 0 or den - int(den) != 0 or num < 0 or den <= 0.0:
            raise ValueError, "num (numerator) must be an integer greater than or equal to zero, and den (denominator) must be an integer greater than zero"
        num = float(num)
        den = float(den)
    except:
        raise ValueError, "num (numerator) must be an integer greater than or equal to zero, and den (denominator) must be an integer greater than zero"

    alpha = get_alpha(conflev)
    try:
        if basepop <= 0:
            raise ValueError, "basepop must be a greater than zero"
    except:
        raise ValueError, "basepop must be a greater than zero"

    zalpha = abs(probit(1.0 - alpha/2.0))

    pt = basepop

    rate = (num / den) * pt

    if method=='rg':
        unitrate = num / den
        bound = zalpha * (1.0 / num**0.5)
        lograte = math.log(unitrate)
        LL = math.e**(lograte - bound) * pt
        if LL < 0.0:
            LL = 0.0
        UL = math.e**(lograte + bound) * pt
        return (rate, LL, UL)        
    elif method=='byar':
        Lnum = num * (1.0 - (1.0/(9.0*num)) - ((zalpha / 3.0) * (1.0 / num)**0.5))**3.0
        Unum = (num + 1.0) * (1.0 - (1.0/(9.0*(num+1.0))) + ((zalpha / 3.0) * (1.0 / (num + 1.0))**0.5))**3.0
        LL = (Lnum / den) * pt
        if LL < 0.0:
            LL = 0.0
        UL = (Unum / den) * pt        
        return (rate, LL, UL)
    elif method=='normal':
        unitrate = num / den
        bound = zalpha * ((num / den**2.)**0.5)
        LL = (unitrate - bound) * pt
        if LL < 0.0:
            LL = 0.0
        UL = (unitrate + bound) * pt
        return (rate, LL, UL)
    elif method=='daly':
        import rpy
        alpha = alpha / 2.0
        if num > 0.0:
            Lnum = rpy.r.qgamma(alpha,num)
            Unum = rpy.r.qgamma(1.0 - alpha, num + 1.0)
        elif num == 0.0:
            Lnum = 0.0
            Unum = -math.log(alpha)
        else:
            raise ValueError, "num (numerator) must be greater than or equal to zero, and den (denominator) must be greater than zero"
        return (rate, (Lnum/den)*pt, (Unum/den)*pt)
    else:
        raise ValueError, "method parameter must be one of 'rg', 'byar', 'daly' or 'normal'" 

def freqcl(num,conflev=0.95,method='daly'):
    """
    Returns a 3-tuple of a Poisson count and lower and upper confidence limits for that count
    - num is the count of events - must be zero or a positive value
    - conflev= is the two-sided confidence level as a proportion (defaults to 0.95). Must be between 0.5 and 1.0 exclusive
    - method= selects the calculation method, must be one of 'byar' or 'daly', default is 'daly'

    Method details:
        byar - Poisson approximation by Byar, as described in Rothman KJ and Boice JD. Epidemiologic analysis with a 
               programmable calculator. US National Institues of Health Publication No. 79 (find complete reference)
        daly - exact Poisson method as described in: Daly, L. Simple SAS macros for the calculation
               of exact binomial and Poisson confidence limits. Comput Biol Med 1992; 22(5):351-61
    """
    try:
        if num - int(num) != 0 or num < 0:
            raise ValueError, "num (count) must be an integer greater than or equal to zero"
        num = float(num)
    except:
        raise ValueError, "num (numerator) must be an integer greater than or equal to zero"

    alpha = get_alpha(conflev)

    if method=='byar':
        zalpha = abs(probit(1.0 - alpha/2.0))
        if num > 0:
            Lnum = num * (1.0 - (1.0/(9.0*num)) - ((zalpha / 3.0) * (1.0 / num)**0.5))**3.0
        else:
            Lnum = 0.0
        Unum = (num + 1.0) * (1.0 - (1.0/(9.0*(num+1.0))) + ((zalpha / 3.0) * (1.0 / (num + 1.0))**0.5))**3.0
        if Lnum < 0.0:
            Lnum = 0.0
        return (num, Lnum, Unum)
    elif method=='daly':
        import rpy
        alpha = alpha / 2.0
        if num > 0.0:
            Lnum = rpy.r.qgamma(alpha,num)
            Unum = rpy.r.qgamma(1.0 - alpha, num + 1.0)
        elif num == 0.0:
            Lnum = 0.0
            Unum = -math.log(alpha)
        else:
            raise ValueError, "num (numerator) must be an integer greater than or equal to zero"
        return (num, Lnum, Unum)
    else:
        raise ValueError, "method parameter must be 'byar' or 'daly'" 

def wncl(wgtvector,conflev=0.95,method='daly',exclude_nonpositive_weights=False):
    """
    Returns a 3-tuple of the sum of the non-negative weights passed
    as the first argument, and the lower and upper Poisson confidence limits around that
    at alpha level specified by conflev. The optional third Boolean argument
    causes non-positive weights to be considered as missing - should give the same answers either way.

    - conflev= is the two-sided confidence level as a proportion (defaults to 0.95). Must be between 0.5 and 1.0 exclusive
    - method= selects the calculation method, must be one of 'byar' or 'daly', default is 'daly'

    Method details:
        byar - Poisson approximation by Byar, as described in Rothman KJ and Boice JD. Epidemiologic analysis with a 
               programmable calculator. US National Institues of Health Publication No. 79 (find complete reference)
        daly - exact Poisson method as described in: Daly, L. Simple SAS macros for the calculation
               of exact binomial and Poisson confidence limits. Comput Biol Med 1992; 22(5):351-61
    """

    if exclude_nonpositive_weights:
        wgtvector = mask_nonpositive_weights(wgtvector)
    else:
        wgtvector = zero_nonpositive_weights(wgtvector)

    n = nonmissing(wgtvector)

    unwgted_results = freqcl(n,conflev=conflev,method=method)

    # The following is incorrect but a rogh approximation pending resultion.
    if n == 0:
        sumwgts = 0.0
        return (0.0,0.0,0.0)
    else:
        sumwgts = float(MA.add.reduce(wgtvector))
        return (sumwgts, (unwgted_results[1]/unwgted_results[0])*sumwgts, (unwgted_results[2]/unwgted_results[0])*sumwgts)

def wfreqcl(wgtvector,conflev=0.95, method='daly',exclude_nonpositive_weights=False):
    """Same as wncl()"""
    return wncl(wgtvector,conflev=conflev,method=method,exclude_nonpositive_weights=exclude_nonpositive_weights)

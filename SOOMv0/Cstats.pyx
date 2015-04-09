#   Except where otherwise stated in comments below (text contained in triple quotes),
#   the contents of this file are subject to the HACOS License Version 1.2
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

import math

cdef double _fx(x):
    """
    Support function for cdf_gauss() function which returns the probability that an observation
    from the standard normal distribution is less than or equal to x (that is, x must be
    a standard normal deviate).

    The following function was adapted from Python code which appears in a paper by Dridi (2003).
    The programme code is copyright 2003 Dridi and Regional Economics Applications Laboratory,
    University of Illinois and is used here with the permission of its author.
    
    This function uses Gauss-legendre quadrature to provide good accuracy in the tails of the 
    distribution, at the expense of speed - this function is slower than the cdf_norm_RA() function
    in the accompanying Stats.py module which uses rational approximations, but is quite inaccurate.
    
    References:
    
    Dridi, C. (2003): A Short Note on the Numerical Aproximation of the Standard Normal
    Cumulative Distribution and its Inverse, Regional Economics Applications Laboratory,
    University of Illinois and Federal Reserve Bank of Chicago. Availsble at
    http://www2.uiuc.edu/unit/real/d-paper/real03-t-7.pdf or at 
    http://econwpa.wustl.edu/eps/comp/papers/0212/0212001.pdf 
    """
    return 1.1283791670955125585606992899556644260883*(2.718281828459045090795598298428**(-x**2.0));

cdef double _GLx(double a, double b):
    """
    Support function for cdf_gauss() function which returns the probability that an observation
    from the standard normal distribution is less than or equal to x (that is, x must be
    a standard normal deviate).

    The following function was adapted from Python code which appears in a paper by Dridi (2003).
    The programme code is copyright 2003 Dridi and Regional Economics Applications Laboratory,
    University of Illinois and is used here with the permission of its author.
    
    This function uses Gauss-legendre quadrature to provide good accuracy in the tails of the 
    distribution, at the expense of speed - this function is slower than the cdf_norm_RA() function
    in the accompanying Stats.py module which uses rational approximations, but is quite inaccurate.
    
    References:
    
    Dridi, C. (2003): A Short Note on the Numerical Aproximation of the Standard Normal
    Cumulative Distribution and its Inverse, Regional Economics Applications Laboratory,
    University of Illinois and Federal Reserve Bank of Chicago. Availsble at
    http://www2.uiuc.edu/unit/real/d-paper/real03-t-7.pdf or at 
    http://econwpa.wustl.edu/eps/comp/papers/0212/0212001.pdf 
    """
    cdef double y1, y2, y3, y4, y5, x1, x2, x3, x4, x5, w1, w2, w3, w4, w5, s, h
    cdef int n, i
    
    y1=0.0
    y2=0.0
    y3=0.0
    y4=0.0
    y5=0.0

    x1=-(245.0 + 14.0 * (70.0**0.5))**0.5 / 21.0
    x2=-(245.0 - 14.0 * (70.0**0.5))**0.5 / 21.0
    x3=0.0
    x4=-x2
    x5=-x1

    w1=(322.0 - 13.0 * (70.0**0.5)) / 900.0
    w2=(322.0 + 13.0 * (70.0**0.5)) / 900.0
    w3=128.0/225.0
    w4=w2
    w5=w1

    # n=4800
    n = 120
    s=0.0
    h=(b-a)/n

    for i from 0 <= i < n:
        y1=h*x1/2.0+(h+2.0*(a+i*h))/2.0
        y2=h*x2/2.0+(h+2.0*(a+i*h))/2.0
        y3=h*x3/2.0+(h+2.0*(a+i*h))/2.0
        y4=h*x4/2.0+(h+2.0*(a+i*h))/2.0
        y5=h*x5/2.0+(h+2.0*(a+i*h))/2.0
        s=s+h*(w1*_fx(y1)+w2*_fx(y2)+w3*_fx(y3)+w4*_fx(y4)+w5*_fx(y5))/2.0;
    return s;

def cdf_gauss(double x):
    """
    Returns the probability that an observation from the standard normal distribution
    is less than or equal to x (that is, x must be a standard normal deviate).

    The following function was adapted from Python code which appears in a paper by Dridi (2003).
    The programme code is copyright 2003 Dridi and Regional Economics Applications Laboratory,
    University of Illinois and is used here with the permission of its author.
    
    This function uses Gauss-legendre quadrature to provide good accuracy in the tails of the 
    distribution, at the expense of speed - this function is slower than the cdf_norm_RA() function
    in the accompanying Stats.py module which uses rational approximations, but is quite inaccurate.
    
    References:
    
    Dridi, C. (2003): A Short Note on the Numerical Aproximation of the Standard Normal
    Cumulative Distribution and its Inverse, Regional Economics Applications Laboratory,
    University of Illinois and Federal Reserve Bank of Chicago. Availsble at
    http://www2.uiuc.edu/unit/real/d-paper/real03-t-7.pdf or at 
    http://econwpa.wustl.edu/eps/comp/papers/0212/0212001.pdf 
    """
    if x >= 0.0:
        return (1.0 + _GLx(0,  x/(2.0**0.5))) / 2.0
    else:
        return (1.0 - _GLx(0, -x/(2.0**0.5))) / 2.0

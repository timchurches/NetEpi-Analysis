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
# $Id: twobytwo.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/SOOMv0/Analysis/twobytwo.py,v $
#
# twobytwo.py - calculates epidemiological measures of association for
# two-by-two tables. Largely, but not entirely, based on a translation of
# JavaScript code from the OpenEpi project (see http://www.openepi.com) - such
# translation and re-use is permited by the one source license under which
# OpenEpi is made available.

from SOOMv0 import Stats
from rpy import *
import math
import Numeric
use_cstats = True
try:
    import Cstats
except ImportError:
    use_cstats = False

__all__ = (
    'twobytwotable',
)

class NotAvailable(Exception): pass

MathError = (RException, ZeroDivisionError, NotAvailable)

class _ReportBase:
    float_fmt = '%.5f'
    rule = None

    def __init__(self, label):
        self.label = label
        self.contents = []

    def fmt(self, fmt, *args):
        strargs = []
        for arg in args:
            if isinstance(arg, float):
                strargs.append(self.float_fmt % arg)
            elif arg is None:
                strargs.append('undefined')
            else:
                strargs.append(str(arg))
        self.contents.append(fmt % tuple(strargs))

    def _lines(self):
        return [str(node) for node in self.contents]

    def __str__(self):
        return '\n'.join(self._lines())

class _ReportSubSection(_ReportBase):
    role = 'subsection'

    def _lines(self):
        lines = _ReportBase._lines(self)
        lines.insert(0, self.label+':')
        lines.append('-----------------------')
        return lines

class _ReportSection(_ReportBase):
    role = 'section'
    rule = '='

    def new_subsection(self, label):
        subsection = _ReportSubSection(label)
        self.contents.append(subsection)
        return subsection

    def _lines(self):
        lines = _ReportBase._lines(self)
        lines[0:0] = ['', self.label, '=' * len(self.label)]
        return lines


# Wrapper function around R's fisher.exact() function to retry with various
# options if it fails due to the values being too large.
def fisher_exact_test(rmatrix, conf_level=0.95, conf_int=True,
                      alternative='two.sided'):
    kwargs = dict(conf_level=conf_level, conf_int=conf_int,
                  alternative=alternative)
    while True:
        try:
            return r.fisher_test(rmatrix, **kwargs)
        except RException, e:
            if 'workspace' in kwargs:
                del kwargs['workspace']
                kwargs['hybrid'] = True
            elif 'hybrid' in kwargs:
                # run out of options
                return None
            elif 'Out of workspace' in str(e) or 'FEXACT error 40' in str(e):
                # increase network algorithm workspace
                kwargs['workspace'] = 2000000
            else:
                kwargs['hybrid'] = True


# create a function in the R environment to calculate mid-p exact OR and
# confidence limits.  This code is adapted from the EpiTools package, used with
# permission from Tomas Aragon
# See http://www.medepi.net/epitools/
r("""midpcl <- function(x, conf.level=0.95, interval=c(0, 1000)) {
            mm<-x
            mue <- function(mm, or) {
                fisher.test(mm, or=or, alternative="less")$p -
                fisher.test(x=x, or=or, alternative="greater")$p }
            midp <- function(mm, or=1) {
                lteqtoa1 <- fisher.test(mm, or=or, alternative="less")$p.val
                gteqtoa1 <- fisher.test(mm, or=or, alternative="greater")$p.val
                0.5 * (lteqtoa1 - gteqtoa1 + 1.0) }
            alpha <- 1.0 - conf.level
            EST <- uniroot(function(or) {
                           mue(mm, or)
                   }, interval = interval)$root
            LCL <- uniroot(function(or) {
                     1.0 - midp(mm, or) - alpha/2.0
                   }, interval = interval)$root
            UCL <- 1.0/uniroot(function(or) {
                     midp(mm, or = 1.0/or) - alpha/2.0
                   }, interval = interval)$root
            midporcl<-c(EST, LCL, UCL)
            return(midporcl) }
        """)

class TwoByTwoStratum(object):

    def __init__(self, e1d1, e0d1, e1d0, e0d0,
                 label=None,
                 conflev=0.95, add_half_if_zeros=False,  khan=False):
        self.label = label
        self.conflev = conflev
        self.a = e1d1 # exposed and diseased
        self.b = e0d1 # unexposed and diseased
        self.c = e1d0 # exposed and undiseased
        self.d = e0d0 # unexposed and undiseased
        if self.a < 0 or self.b < 0 or self.c < 0 or self.d < 0:
            raise ValueError('a, b, c and d must all be greater than or equal to zero')
        self.khan = khan
        self.added_half = False
        self.has_cell_zeros = False
        if self.a == 0 or self.b == 0 or self.c == 0 or self.d == 0:
            if add_half_if_zeros:
                self.a += 0.5
                self.b += 0.5
                self.c += 0.5
                self.d += 0.5
                self.added_half = True
                self.has_cell_zeros = False
            else:
                self.has_cell_zeros = True

        self.r1 = self.a + self.b # total diseased
        self.r2 = self.c + self.d # total undiseased
        self.c1 = self.a + self.c # total exposed
        self.c2 = self.b + self.d # total unexposed
        self.t = self.a + self.b + self.c + self.d # grand total

        if self.c1 == 0 or self.c2 == 0 or self.r1 == 0 or self.r2 == 0:
            self.has_marginal_zeros = True
        else:
            self.has_marginal_zeros = False

        # Set flag for expected counts less than 5
        if self.t == 0:
            self.anyExpLT5 = True
        else:
            if (float(self.r1*self.c1)/float(self.t) < 5
                or float(self.r1*self.c2)/float(self.t) < 5
                or float(self.r2*self.c1)/float(self.t) < 5
                or float(self.r2*self.c2)/float(self.t) < 5):
                self.anyExpLT5 = True
            else:
                self.anyExpLT5 = False

        # chi square calculations
        if not self.has_marginal_zeros:
            self.cs = float(self.t * ((self.a*self.d) - (self.b*self.c))**2) / float(self.c1*self.c2*self.r1*self.r2)
            self.csc = (self.t * (abs((self.a*self.d) - (self.b*self.c)) - (float(self.t)/2.0))**2) \
                      / float(self.c1*self.c2*self.r1*self.r2)
            self.mhcs = (float((self.t - 1)*((self.a*self.d) - (self.b*self.c))**2)) / float(self.c1*self.c2*self.r1*self.r2)
            self.pcs = 1.0 - r.pchisq(self.cs, 1)
            self.pcsc = 1.0 - r.pchisq(self.csc, 1)
            self.pmhcs = 1.0 - r.pchisq(self.mhcs, 1)
        else:
            self.cs = None
            self.csc = None
            self.mhcs = None
            self.pcs = None
            self.pcsc = None
            self.pmhcs = None

        # critical value
        self.z = -Stats.probit((1.0 - self.conflev)/2)

        # risk/prevalence
        self.risk_exposed, self.risk_exposed_lower, self.risk_exposed_upper = self._modwald(self.a, self.c1, self.z)
        self.risk_unexposed, self.risk_unexposed_lower, self.risk_unexposed_upper = self._modwald(self.b, self.c2, self.z)
        self.risk_overall, self.risk_overall_lower, self.risk_overall_upper = self._modwald(self.r1, self.t, self.z)

        # risk/prevalence ratio
        if self.c1 == 0 or self.c2 == 0 or self.b == 0:
            self.rr = None
            self.rr_lower = None
            self.rr_upper = None
        else:
            self.rr = (float(self.a)/float(self.c1))/(float(self.b)/float(self.c2))
            # confidence limits for risk/prevalence ratio - Taylor series
            if self.a == 0:
                self.rr_lower = None
                self.rr_upper = None
            else:
                self.rr_lower = self.rr * math.exp(-self.z * (((1.0 - float(self.a)/float(self.c1))/float(self.a)) + \
                                                              ((1.0 - float(self.b)/float(self.c2)) / float(self.b)))**0.5)
                self.rr_upper = self.rr * math.exp( self.z * (((1.0 - float(self.a)/float(self.c1))/float(self.a)) + \
                                                              ((1.0 - float(self.b)/float(self.c2)) / float(self.b)))**0.5)

        # risk/prevalence difference
        if self.c1 == 0 or self.c2 == 0:
            self.rd = None
            self.rd_lower = None
            self.rd_upper = None
        else:
            self.rd = (float(self.a)/float(self.c1)) - (float(self.b)/float(self.c2) )
            # confidence limits for the risk/prevalence difference - Taylor
            # series
            rd_bound = ((float(self.a)*float(self.c)/(self.c1**3)) + (float(self.b)*float(self.d)/(self.c2**3)))**0.5
            self.rd_lower = self.rd - (self.z * rd_bound)
            self.rd_upper = self.rd + (self.z * rd_bound)

        # aetiological fraction in the population based on the risk/prevalance
        # ratio
        if self.t == 0 or self.c2 == 0 or self.r1 == 0:
            self.aefp = None
            self.aefp_upper = None
            self.aefp_lower = None
        else:
            self.aefp = (float(self.r1)/float(self.t) - float(self.b)/float(self.c2)) / (float(self.r1) / float(self.t))
            if self.aefp < -1.0:
                self.aefp = -1.0
            elif self.aefp > 1.0:
                self.aefp = 1.0
            else:
                pass
            # confidence limits for the aetiological fraction in the
            # population, based on the risk/prevalance ratio - Kahn/Sempos
            # method
            aefp_bound_num = self.b * self.t * (self.a * self.d * (self.t - self.b) + (self.c * self.b**2))
            aefp_bound_den =  ((self.r1**3) * (self.c2**3))
            aefp_bound = self.z * ((float(aefp_bound_num) / float(aefp_bound_den))**0.5)
            self.aefp_lower = self.aefp - aefp_bound
            if self.aefp_lower < -1.0:
                self.aefp_lower = -1.0
            self.aefp_upper = self.aefp + aefp_bound
            if self.aefp_upper > 1.0:
                self.aefp_upper = 1.0

        # aetiological fraction in the exposed based on the risk/prevalance
        # ratio
        if self.rr in (0.0, None):
            self.aefe = None
            self.aefe_lower = None
            self.aefe_upper = None
        else:
            self.aefe = float(self.rr - 1.0) / float(self.rr)
            if self.aefe < -1.0:
                self.aefe = -1.0
            elif self.aefe > 1.0:
                self.aefe = 1.0
            else:
                pass
            # confidence limits for the aetiological fraction in the exposed,
            # based on the risk/prevalance ratio
            if self.rr_lower ==0 or self.rr_lower == None:
                self.aefe_lower = None
            else:
                self.aefe_lower = float(self.rr_lower - 1.0) / self.rr_lower
                if self.aefe_lower < -1.0:
                    self.aefp_lower = -1.0
            if self.rr_upper ==0 or self.rr_upper == None:
                self.aefe_upper = None
            else:
                self.aefe_upper = float(self.rr_upper - 1.0) / self.rr_upper
                if self.aefe_upper > 1.0:
                    self.aefe_upper = 1.0

        # prevented fraction in the population based on the risk/prevalance
        # ratio
        if self.risk_unexposed in (0, None) or self.risk_overall == None:
            self.pfp = None
            self.pfp_lower = None
            self.pfp_upper = None
        else:
            self.pfp = float(self.risk_unexposed - self.risk_overall) / float(self.risk_unexposed)
            # confidence limits for the prevented fraction in the population,
            # based on the risk/prevalance ratio
            if 1.0 - self.aefp_upper == 0.0:
                self.pfp_lower = None
            else:
                self.pfp_lower = (1.0 - (1.0 / (1.0 - self.aefp_upper)))
            if 1.0 - self.aefp_lower == 0.0:
                self.pfp_upper = None
            else:
                self.pfp_upper = (1.0 - (1.0 / (1.0 - self.aefp_lower)))

        # prevented fraction in the exposed based on the risk/prevalance ratio
        if self.risk_unexposed in (0, None) or self.risk_exposed == None:
            self.pfe = None
            self.pfe_lower = None
            self.pfe_upper = None
        else:
            self.pfe = float(self.risk_unexposed - self.risk_exposed) / float(self.risk_unexposed)
            # confidence limits for the prevented fraction in the exposed,
            # based on the risk/prevalance ratio
            if self.rr_upper == None or self.rr_lower == None:
                self.pfe_lower = None
                self.pfe_upper = None
            else:
                self.pfe_lower = 1.0 - self.rr_upper
                self.pfe_upper = 1.0 - self.rr_lower

        # odds ratios
        if self.b == 0 or self.c == 0:
            self.oddsratio = None
            self.or_lower = None
            self.or_upper = None
        else:
            self.oddsratio = float(self.a*self.d) / float(self.b*self.c)
            # confidence limits for odds ratio - Taylor series
            if self.a == 0 or self.b == 0 or self.c == 0 or self.d == 0:
                self.or_lower = None
                self.or_upper = None
            else:
                self.or_lower = self.oddsratio * math.exp(-self.z * (1.0/float(self.a) + 1.0/float(self.b) + 1.0/float(self.c) + \
                                                              1.0/float(self.d))**0.5)
                self.or_upper = self.oddsratio * math.exp( self.z * (1.0/float(self.a) + 1.0/float(self.b) + 1.0/float(self.c) + \
                                                          1.0/float(self.d))**0.5)

        # aetiological fraction in the population based on the odds ratio
        # if self.c == 0 or self.r2 == 0 or self.oddsratio == None:
        self.aefpor = None
        self.aefpor_lower = None
        self.aefpor_upper = None
        if self.oddsratio is not None:
            try:
                self.aefpor = ((float(self.c)/float(self.r2))*(self.oddsratio - 1.0)) \
                            / ((float(self.c)/float(self.r2))*(self.oddsratio - 1.0) + 1.0)
                if self.aefpor < -1.0:
                    self.aefpor = -1.0
                elif self.aefpor > 1.0:
                    self.aefpor = 1.0
                else:
                    pass
                # confidence limits for the aetiological fraction in the
                # population, based on the odds ratio
                if self.b != 0 and self.d != 0 and self.r1 != 0:
                    aefpor_bound = self.z*(((float(self.b*self.r2)/float(self.d*self.r1))**2)*((float(self.a)/float(self.b*self.r1)) \
                                            + (float(self.c)/float(self.d*self.r2))))**0.5
                    self.aefpor_lower = self.aefpor - aefpor_bound
                    if self.aefpor_lower < -1.0:
                        self.aefpor_lower = -1.0
                    self.aefpor_upper = self.aefpor + aefpor_bound
                    if self.aefpor_upper > 1.0:
                        self.aefpor_upper = 1.0
            except MathError:
                pass

        # aetiological fraction in the exposed based on the odds ratio
        if self.oddsratio == 0.0 or self.oddsratio == None:
            self.aefeor = None
            self.aefeor_lower = None
            self.aefeor_upper = None
        else:
            self.aefeor = (self.oddsratio - 1.0) / float(self.oddsratio)
            if self.aefeor < -1.0:
                self.aefeor = -1.0
            elif self.aefeor > 1.0:
                self.aefeor = 1.0
            else:
                pass
            # confidence limits for the aetiological fraction in the exposed,
            # based on the odds ratio
            if self.or_lower == 0 or self.or_lower == None:
                self.aefeor_lower = None
            else:
                self.aefeor_lower = float(self.or_lower - 1.0) / self.or_lower
                if self.aefeor_lower < -1.0:
                    self.aefeor_lower = -1.0
            if self.or_upper == 0 or self.or_upper == None:
                self.aefeor_upper = None
            else:
                self.aefeor_upper = float(self.or_upper - 1.0) / self.or_upper
                if self.aefeor_upper > 1.0:
                    self.aefeor_upper = 1.0

        # prevented fraction in the population based on the odds ratio
        self.pfpor = None
        self.pfpor_lower = None
        self.pfpor_upper = None
        if self.r2 != 0 and self.oddsratio is not None:
            try:
                self.pfpor = (float(self.c)/float(self.r2))*(1.0 - self.oddsratio)
                # confidence limits for the prevented fraction in the population,
                # based on the odds ratio
                if self.aefpor_upper == None or (1.0 - self.aefpor_upper == 0.0):
                    self.pfpor_lower = None
                else:
                    self.pfpor_lower = (1.0 - (1.0 / float(1.0 - self.aefpor_upper)))
                if self.aefpor_lower == None or (1.0 - self.aefpor_lower == 0.0):
                    self.pfpor_upper = None
                else:
                    self.pfpor_upper = (1.0 - (1.0 / float(1.0 - self.aefpor_lower)))
            except MathError:
                pass

        # prevented fraction in the exposed based on the odds ratio
        if self.oddsratio == None:
            self.pfeor = None
            self.pfeor_lower = None
            self.pfeor_upper = None
        else:
            self.pfeor = 1.0 - self.oddsratio
            # confidence limits for the prevented fraction in the exposed,
            # based on the odds ratio
            if self.or_lower == None or self.or_upper == None:
                self.pfeor_lower = None
                self.pfeor_upper = None
            else:
                self.pfeor_lower = 1.0 - self.or_upper
                self.pfeor_upper = 1.0 - self.or_lower


        # Don't perform exact tests if numbers too large.
        if max(self.a, self.b, self.c, self.d) < 1000 or \
           (max(self.a, self.b, self.c, self.d) < 10000 and min(self.a, self.b, self.c, self.d) < 50):
            # Fisher's exact test and conditional MLE odds ratio via fisher.test()
            # in R
            if self.added_half:
                a = int(self.a - 0.5)
                b = int(self.b - 0.5)
                c = int(self.c - 0.5)
                d = int(self.d - 0.5)
            else:
                a = int(self.a)
                b = int(self.b)
                c = int(self.c)
                d = int(self.d)

            tab = with_mode(NO_CONVERSION, r.matrix)([a, b, c, d], nr=2)

            ft = fisher_exact_test(tab, conf_level=self.conflev, conf_int=True, alternative='two.sided')
            if ft is not None:
                self.exact_p_twosided_asextreme = ft['p.value']
                self.cmle_or = ft['estimate']['odds ratio']
                self.cmle_or_lower = ft['conf.int'][0]
                self.cmle_or_upper = ft['conf.int'][1]
            else:
                self.exact_p_twosided_asextreme = None
                self.cmle_or = None
                self.cmle_or_lower = None
                self.cmle_or_upper = None

            p_less = p_greater = None
            ft = fisher_exact_test(tab, conf_level=self.conflev, conf_int=False, alternative='less')
            if ft is not None:
                p_less = ft['p.value']
            else:
                p_less = None
            ft = fisher_exact_test(tab, conf_level=self.conflev, conf_int=False, alternative='greater')
            if ft is not None:
                p_greater = ft['p.value']
            else:
                p_greater = None

            if self.cmle_or <= 1.0:
                self.exact_p_onesided = p_less
            else:
                self.exact_p_onesided = p_greater

            if self.exact_p_onesided is not None:
                self.exact_p_twosided_twiceonesided = 2.0 * self.exact_p_onesided
            else:
                self.exact_p_twosided_twiceonesided = None

            if p_less is not None and p_greater is not None:
                pval1 = (0.5 * (p_less - (1.0 - p_greater)))  + (1.0 - p_greater)
                self.mid_p_onesided = min(pval1, 1.0 - pval1)
                self.mid_p_twosided = 2.0 * self.mid_p_onesided
                del pval1
            else:
                self.mid_p_onesided = None
                self.mid_p_twosided = None
            del ft

            # calculate mid-p confidence limits and median-unbiased estimate of
            # OR.  code adapted from EpiTools package, used with permission
            # from Tomas Aragon
            try:
                self.midp_or, self.midp_or_lower, self.midp_or_upper = r.midpcl(tab, conf_level=self.conflev)
            except MathError:
                self.midp_or, self.midp_or_lower, self.midp_or_upper = None, None, None
        else:
            self.exact_p_twosided_twiceonesided = None
            self.exact_p_onesided = None
            self.exact_p_twosided_asextreme = None
            self.cmle_or = None
            self.cmle_or_lower = None
            self.cmle_or_upper = None
            self.mid_p_onesided = None
            self.mid_p_twosided = None
            self.midp_or, self.midp_or_lower, self.midp_or_upper = None, None, None

        if khan:
            # Fisher's exact using method of Khan, HA. A Visual Basic Software
            # for computing Fisher's exact Probability.  Journal of Statistical
            # Software 2003; 8(21) (available at http://www.jstatsoft.org)
            # First find the minimum value in the table
            if self.added_half:
                a = self.a - 0.5
                b = self.b - 0.5
                c = self.c - 0.5
                d = self.d - 0.5
            else:
                a = self.a
                b = self.b
                c = self.c
                d = self.d
            x1 = int(a)
            x2 = int(b)
            x3 = int(c)
            x4 = int(d)
            t1 = int(x1 + x2)
            t2 = int(x3 + x4)
            t3 = int(x1 + x3)
            t4 = int(x2 + x4)
            x = int(x1 + x2 + x3 + x4)
            minval = min(x1, x2, x3, x4)
            if use_cstats: # try:
                self.khan_p1 = Cstats.exactcalc(minval, t1, t2, t3, t4, x, x1, x2, x3, x4, a, b, c, d)
            else: # except:
                mini = minval
                total_p = 0.0
                while minval >= 0.0:
                    subtotal = (self._khancalc(t1) + self._khancalc(t2) + self._khancalc(t3) + self._khancalc(t4)) \
                             - (self._khancalc(x) + self._khancalc(x1) + self._khancalc(x2) + self._khancalc(x3) + self._khancalc(x4))
                    delta = math.exp(subtotal)
                    if abs(delta) < 0.000001:
                        break
                    else:
                        total_p += delta
                    # print minval, subtotal, math.exp(subtotal), total_p
                    if mini == a:
                        x1 = x1 - 1
                        x2 = t1 - x1
                        x3 = t3 - x1
                        x4 = t2 - x3
                    if mini == b:
                        x2 = x2 - 1
                        x1 = t1 - x2
                        x4 = t4 - x2
                        x3 = t2 - x4
                    if mini == c:
                        x3 = x3 - 1
                        x1 = t3 - x3
                        x4 = t2 - x3
                        x2 = t4 - x4
                    if mini == d:
                        x4 = x4 - 1
                        x2 = t4 - x4
                        x3 = t2 - x4
                        x1 = t3 - x3
                    minval -= 1
                self.khan_p1 = total_p
            self.khan_p = self.khan_p1 * 2.0
            if self.khan_p > 1.0:
                self.khan_p = 0.9999999999999999999999999999999999999

    def _modwald(self, num, den, z):
        if den > 0:
            pointestimate = float(num) / float(den)
            vpp = (num + (z**2)/2.0) / (den + z**2)
            bound = z*((vpp*(1.0 - vpp) / (den + z**2))**0.5)
            lower = vpp - bound
            if lower < 0.0:
                lower = 0.0
            upper = vpp + bound
            if upper > 1.0:
                upper = 1.0
            return pointestimate, lower, upper
        else:
            return None, None, None

    def _khancalc(self, value):
        value = int(value)
        logvalue = 0.0
        if value == 0.0:
            pass
        else:
            for i in range(value):
                logvalue += math.log(i+1)
        return logvalue

    def informative(self):
        return (self.a * self.d != 0) or (self.b * self.c != 0)

    def report_counts(self, subsec, crude=False):
        if self.added_half:
            subsec.fmt('Note: 0.5 added to each table cell due to one of more zero counts')
        subsec.fmt('a (exposed, disease): %s', self.a)
        subsec.fmt('b (unexposed, disease): %s', self.b)
        subsec.fmt('c (exposed, no disease): %s', self.c)
        subsec.fmt('d (unexposed, no disease): %s', self.d)

    def report_measures_of_association(self, subsec, crude=False):
        subsec.fmt('Chi sq: %s, p=%s', self.cs, self.pcs)
        subsec.fmt('Yates-corrected Chi sq: %s, p=%s', self.csc, self.pcsc)
        subsec.fmt('M-H Chi sq: %s, p=%s', self.mhcs, self.pmhcs)
        if self.khan:
            subsec.fmt('Fisher\'s exact test (Khan method): one-sided p=%s, two-sided p=%s', self.khan_p1, self.khan_p)
        subsec.fmt('Fisher\'s exact test: one-sided p=%s, two-sided (twice one-sided): p=%s, two-sided (as extreme): p=%s', self.exact_p_onesided, self.exact_p_twosided_twiceonesided, self.exact_p_twosided_asextreme)
        subsec.fmt('mid-p: one-sided p=%s, two-sided p=%s', self.mid_p_onesided, self.mid_p_twosided)

    def report_risk_based(self, subsec, crude=False):
        subsec.fmt('Risk in exposed: %s (%s, %s)', self.risk_exposed, self.risk_exposed_lower, self.risk_exposed_upper)
        subsec.fmt('Risk in unexposed: %s (%s, %s)', self.risk_unexposed, self.risk_unexposed_lower, self.risk_unexposed_upper)
        subsec.fmt('Risk in overall population: %s (%s, %s)', self.risk_overall, self.risk_overall_lower, self.risk_overall_upper)
        subsec.fmt('Risk ratio: %s (%s, %s)', self.rr, self.rr_lower, self.rr_upper)
        subsec.fmt('Risk difference: %s (%s, %s)', self.rd, self.rd_lower, self.rd_upper)
        if crude:
            subsec.fmt('Aetiological fraction in the population: %s (%s, %s)', self.aefp, self.aefp_lower, self.aefp_upper)
            subsec.fmt('Aetiological fraction in the exposed: %s (%s, %s)', self.aefe, self.aefe_lower, self.aefe_upper)
            subsec.fmt('Prevented fraction in the population: %s (%s, %s)', self.pfp, self.pfp_lower, self.pfp_upper)
            subsec.fmt('Prevented fraction in the exposed: %s (%s, %s)', self.pfe, self.pfe_lower, self.pfe_upper)

    def report_odds_based(self, subsec, crude=False):
        subsec.fmt('Sample odds ratio: %s (%s, %s)', self.oddsratio, self.or_lower, self.or_upper)
        subsec.fmt('CMLE odds ratio: %s (%s, %s)', self.cmle_or, self.cmle_or_lower, self.cmle_or_upper)
        subsec.fmt('mid-p CMLE odds ratio: %s (%s, %s)', self.midp_or, self.midp_or_lower, self.midp_or_upper)
        if crude:
            subsec.fmt('Aetiological fraction in the population: %s (%s, %s)', self.aefpor, self.aefpor_lower, self.aefpor_upper)
            subsec.fmt('Aetiological fraction in the exposed: %s (%s, %s)', self.aefeor, self.aefeor_lower, self.aefeor_upper)
            subsec.fmt('Prevented fraction in the population: %s (%s, %s)', self.pfpor, self.pfpor_lower, self.pfpor_upper)
            subsec.fmt('Prevented fraction in the exposed :%s (%s, %s)', self.pfeor, self.pfeor_lower, self.pfeor_upper)

    def report(self, section, report, crude=False):
        subsec = report.new_subsection(self.label)
        getattr(self, 'report_' + section)(subsec, crude)


class twobytwotable(object):

    def __init__(self, conflev=0.95):
        self.conflev = conflev
        self.z = -Stats.probit((1.0 - conflev)/2)
        self.strata = [] # vector of strata
        self.unstratified = None

    def add_stratum(self, e1d1, e0d1, e1d0, e0d0, label=None):
        if label is None:
            label = 'Stratum %d' % (len(self.strata) + 1)
        self.strata.append(TwoByTwoStratum(e1d1, e0d1, e1d0, e0d0,
                                           label=label,
                                           conflev=self.conflev))

    def calc(self):
        # initialise variables

        # for crude table
        crude_e1d1, crude_e0d1, crude_e1d0, crude_e0d0 = 0, 0, 0, 0

        # for Mantel-Haenszel summary chi square
        sumMhChiSqNum = 0.0
        sumMhChiSqDen = 0.0

        self.expLT5 = []

        # for adjusted risk ratio
        RRarr = []
        wRRarr = []
        sumRRDirectwlnRR = 0.0
        sumwRR = 0.0

        # for Mantel-Haenszel adjusted risk ratio
        sumMhRRnum = 0.0
        sumMhRRden = 0.0
        sumRgbRRnum = 0.0
        sumRgbRRSE = 0.0

        # for risk difference
        RDarr = []
        wRDarr = []
        sumwtimesRD = 0.0
        sumwRD = 0.0

        # for directly adjusted OR
        ORarr = []
        wORarr = []
        sumwtimesOR = 0.0
        sumwOR = 0.0

        # for Mantel-Haenszel adjusted OR
        sumMhORnum = 0.0
        sumMhORden = 0.0

        # for Robins, Greenland and Breslow
        sumRgbPR = 0.0
        sumRgbPSplusQR = 0.0
        sumRgbQS = 0.0
        sumRgbSumR = 0.0
        sumRgbSumS = 0.0

        # Initialise flags which indicate whether various statistics can be
        # calculated
        MhChiSq_flag = True
        RRDirect_flag = True
        MhRR_flag = True
        RD_flag = True
        ORda_flag = True
        MhOR_flag = True
        RgbOR_flag = True
        exactOR_flag = True

        # accumulate various quantities across strata
        for stratum in self.strata:

            # for crude strata
            crude_e1d1 += stratum.a
            crude_e0d1 += stratum.b
            crude_e1d0 += stratum.c
            crude_e0d0 += stratum.d

            # aliases for compatibility with published formulae
            m1 = stratum.a + stratum.b
            m0 = stratum.c + stratum.d
            n1 = stratum.a + stratum.c
            n0 = stratum.b + stratum.d
            t = stratum.a + stratum.b + stratum.c + stratum.d

            self.expLT5.append(stratum.anyExpLT5)

            # for Mantel-Haenszel uncorrected Chi square acrss strata
            try:
                sumMhChiSqNum += float((stratum.a * stratum.d) - (stratum.b * stratum.c)) / float(t)
                sumMhChiSqDen += float(n0 * n1 * m0 * m1) / float((t - 1) * t**2)
            except MathError:
                MhChSq_flag = False

            # for directly adjusted risk ratio
            try:
                RR = (float(stratum.a)/float(n1)) / (float(stratum.b)/float(n0))
                RRarr.append(RR)
                w = 1.0 / ((float(stratum.c) / float(stratum.a * n1)) + (float(stratum.d) / (stratum.b * n0)))
                wRRarr.append(w)
                sumRRDirectwlnRR += w * math.log(RR)
                sumwRR += w
            except MathError:
                RRDirect_flag = False

            # for Mantel-Haenszel adjusted risk ratio
            try:
                sumMhRRnum += float(stratum.a * n0) / float(t)
                sumMhRRden += float(stratum.b * n1) / float(t)
                sumRgbRRnum += float((m1*n1*n0) - (stratum.a*stratum.b*t)) / float(t**2)
                sumRgbRRSE = 0.0
            except MathError:
                MhRR_flag = False

            # for risk difference
            try:
                RD = (float(stratum.a)/float(n1)) - (float(stratum.b)/float(n0))
                w = 1.0 / ((float(stratum.a*stratum.c)/float(n1**3)) + (float(stratum.b*stratum.d) / float(n0**3)))
                RDarr.append(RD)
                wRDarr.append(w)
                sumwtimesRD += w * RD
                sumwRD += w
            except MathError:
                RD_flag = False

            # for directly adjusted OR
            try:
                OR = float(stratum.a * stratum.d) / float(stratum.b * stratum.c)
                w = 1.0 / (1.0/float(stratum.a) + 1.0/float(stratum.b) + 1.0/float(stratum.c) + 1.0/float(stratum.d))
                ORarr.append(OR)
                wORarr.append(w)
                sumwtimesOR += w * math.log(OR)
                sumwOR += w
            except MathError:
                ORda_flag = False

            # for Mantel-Haenszel adjusted OR
            try:
                sumMhORnum += float(stratum.a) * float(stratum.d) / float(t)
                sumMhORden += float(stratum.b) * float(stratum.c) / float(t)
            except MathError:
                MhOR_flag = False

            # for Robins, Greenland and Breslow
            try:
                P = float(stratum.a + stratum.d) / float(t)
                Q = float(stratum.b + stratum.c) / float(t)
                R = float(stratum.a) * float(stratum.d) / float(t)
                S = float(stratum.b) * float(stratum.c) / float(t)
                sumRgbPR += P*R
                sumRgbPSplusQR += (P*S) + (Q*R)
                sumRgbQS += Q*S
                sumRgbSumR += R
                sumRgbSumS += S
            except MathError:
                RgbOR_flag = False

        # create a "crude" table if more than one strata
        if len(self.strata) > 1:
            self.unstratified = TwoByTwoStratum(crude_e1d1, crude_e0d1, crude_e1d0, crude_e0d0, conflev=self.conflev, label='Unstratified (crude)')

        # now calculate summary and adjusted values if more than one strata
        if len(self.strata) > 1:

            # uncorrected M-H summary
            if MhChiSq_flag and abs(sumMhChiSqDen) > 0.0 :
                self.MhUncorrSummaryChiSq = float(sumMhChiSqNum**2) / sumMhChiSqDen
                self.pMhUncorrSummaryChiSq = 1.0 - r.pchisq(self.MhUncorrSummaryChiSq, 1)
            else:
                self.MhUncorrSummaryChiSq = None
                self.pMhUncorrSummaryChiSq = None

            # directly adjusted RR and RD
            if RRDirect_flag:
                self.adjRRdirect = math.exp(float(sumRRDirectwlnRR) / float(sumwRR))
                self.lowerRRdirect = self.adjRRdirect * math.exp(-(self.z / sumwRR**0.5))
                self.upperRRdirect = self.adjRRdirect * math.exp((self.z / sumwRR**0.5))
            else:
                self.adjRRdirect = None
                self.lowerRRdirect = None
                self.upperRRdirect = None

            if RD_flag:
                self.adjRDdirect = float(sumwtimesRD) / float(sumwRD)
                self.lowerRDdirect = self.adjRDdirect - (self.z / sumwRD**0.5)
                self.upperRDdirect = self.adjRDdirect + (self.z / sumwRD**0.5)
            else:
                self.adjRDdirect = None
                self.lowerRDdirect = None
                self.upperRDdirect = None

            # Mantel-Haenszel adjusted RR
            if MhRR_flag:
                try:
                    self.adjRRmh = sumMhRRnum / float(sumMhRRden)
                except MathError:
                    self.adjRRmh = None

                try:
                    adjRRmhSE = (float(sumRgbRRnum) / float(sumMhRRnum * sumMhRRden))**0.5
                    self.lowerRRmh = self.adjRRmh * math.exp(-self.z * adjRRmhSE)
                    self.upperRRmh = self.adjRRmh * math.exp( self.z * adjRRmhSE)
                except MathError:
                    self.adjRRmh = None
                    self.lowerRRmh = None
                    self.upperRRmh = None
            else:
                self.adjRRmh = None
                self.lowerRRmh = None
                self.upperRRmh = None

            # Breslow-Day chi square test for homogeneity of RR across strata
            try:
                if self.adjRRdirect is None:
                    raise NotAvailable
                self.BDchisqRR = 0.0
                for i in range(len(self.strata)):
                    self.BDchisqRR += float((math.log(RRarr[i]) - math.log(self.adjRRdirect))**2) / (1.0 / wRRarr[i])
                self.pBDchisqRR = 1.0 - r.pchisq(self.BDchisqRR, len(RRarr)-1)
            except MathError:
                self.BDchisqRR = None
                self.pBDchisqRR = None

            # Breslow-Day chi square test for homogeneity of RD across strata
            try:
                if self.adjRDdirect is None:
                    raise NotAvailable
                self.BDchisqRD = 0.0
                for i in range(len(self.strata)):
                    self.BDchisqRD += ((RDarr[i] - self.adjRDdirect)**2) / (1.0 / wRDarr[i])
                self.pBDchisqRD = 1.0 - r.pchisq(self.BDchisqRD, len(RDarr)-1)
            except MathError:
                self.BDchisqRD = None
                self.pBDchisqRD = None

            # Mantel-Haenszel adjusted odds ratios
            self.adjORmh = None
            self.lowerORmh = None
            self.upperORmh = None
            if MhOR_flag and RgbOR_flag:
                try:
                    self.adjORmh = float(sumMhORnum) / float(sumMhORden)
                    ORmhSE = ((float(sumRgbPR) / (2.0 * sumRgbSumR**2)) \
                            + (float(sumRgbPSplusQR) /  (2.0 * sumRgbSumR * sumRgbSumS )) \
                            + (float(sumRgbQS) / (2.0 * sumRgbSumS**2)))**0.5
                    self.lowerORmh = self.adjORmh * math.exp(-self.z * ORmhSE)
                    self.upperORmh = self.adjORmh * math.exp( self.z * ORmhSE)
                except MathError:
                    pass

            # make an array for passing to mantelhaen.test() in R
            mh_array = Numeric.array([0]*4*len(self.strata), typecode=Numeric.Int)
            mh_array.shape = (2, 2, len(self.strata))
            stratum_number = -1
            zero_stratum_flag = False
            for stratum in self.strata:
                stratum_number += 1
                mh_array[0, 0, stratum_number] = stratum.a
                mh_array[0, 1, stratum_number] = stratum.b
                mh_array[1, 0, stratum_number] = stratum.c
                mh_array[1, 1, stratum_number] = stratum.d
                if stratum.a + stratum.b + stratum.c + stratum.d < 1:
                    zero_stratum_flag = True

            self.MH_chisq_contcorr_statistic = None
            self.MH_chisq_contcorr_pvalue = None
            self.MH_commonOR = None
            self.MH_commonOR_ll = None
            self.MH_commonOR_ul = None
            self.MH_chisq_nocontcorr_statistic = None
            self.MH_chisq_nocontcorr_pvalue = None
            self.MH_exact_pvalue_twosided_asextreme = None
            self.MH_exact_pvalue_twosided_twiceonesided = None
            self.MH_exact_pvalue_onesided = None
            self.MH_mid_p_onesided = None
            self.MH_mid_p_twosided = None
            self.MH_exact_commonOR = None
            self.MH_exact_commonOR_ll = None
            self.MH_exact_commonOR_ul = None

            if exactOR_flag and zero_stratum_flag is False and \
                (max(crude_e1d1, crude_e0d1, crude_e1d0, crude_e0d0) < 10000 or \
                (max(crude_e1d1, crude_e0d1, crude_e1d0, crude_e0d0) < 20000 and \
                    min(crude_e1d1, crude_e0d1, crude_e1d0, crude_e0d0) < 50)):
                try:
                    r_mh = r.mantelhaen_test(mh_array, correct=True, conf_level=self.conflev)
                    self.MH_chisq_contcorr_statistic = r_mh['statistic']['Mantel-Haenszel X-squared']
                    self.MH_chisq_contcorr_pvalue = r_mh['p.value']
                    self.MH_commonOR = r_mh['estimate']['common odds ratio']
                    self.MH_commonOR_ll = r_mh['conf.int'][0]
                    self.MH_commonOR_ul = r_mh['conf.int'][1]
                    r_mh = r.mantelhaen_test(mh_array, correct=False, conf_level=self.conflev)
                    self.MH_chisq_nocontcorr_statistic = r_mh['statistic']['Mantel-Haenszel X-squared']
                    self.MH_chisq_nocontcorr_pvalue = r_mh['p.value']

                    r_mh = r.mantelhaen_test(mh_array, exact=True, alternative='two.sided', conf_level=self.conflev)
                    self.MH_exact_pvalue_twosided_asextreme = r_mh['p.value']
                    self.MH_exact_commonOR = r_mh['estimate']['common odds ratio']
                    self.MH_exact_commonOR_ll = r_mh['conf.int'][0]
                    self.MH_exact_commonOR_ul = r_mh['conf.int'][1]

                    r_mh = r.mantelhaen_test(mh_array, exact=True, alternative='less', conf_level=self.conflev)
                    p_less = r_mh['p.value']
                    r_mh = r.mantelhaen_test(mh_array, exact=True, alternative='greater', conf_level=self.conflev)
                    p_greater = r_mh['p.value']

                    if self.MH_exact_commonOR <= 1.0:
                        self.MH_exact_pvalue_onesided = p_less
                    else:
                        self.MH_exact_pvalue_onesided = p_greater

                    self.MH_exact_pvalue_twosided_twiceonesided = 2.0 * self.MH_exact_pvalue_onesided

                    pval1 = (0.5 * (p_less - (1.0 - p_greater)))  + (1.0 - p_greater)
                    self.MH_mid_p_onesided = min(pval1, 1.0 - pval1)
                    self.MH_mid_p_twosided = 2.0 * self.MH_mid_p_onesided
                except MathError:
                    pass

            try:
                # Woolf chi square test for homogeneity of OR across
                # strata
                r.library('vcd')
                r("woolf.test<-woolf_test")
                Wor = r.woolf_test(mh_array)
                self.WchisqOR = Wor['statistic']['X-squared']
                self.dfWchisqOR = Wor['parameter']['df']
                self.pWchisqOR = Wor['p.value']
            except MathError:
                self.WchisqOR = None
                self.pWchisqOR = None
                self.dfWchisqOR = None

            # directly adjusted odds ratio
            if ORda_flag:
                self.ORda = math.exp(float(sumwtimesOR) / float(sumwOR))
                # print "self.ORda:", self.ORda
                self.lowerORda = self.ORda * math.exp(-self.z / sumwOR**0.5)
                self.upperORda = self.ORda * math.exp( self.z / sumwOR**0.5)
            else:
                self.ORda = None
                self.lowerORda = None
                self.upperORda = None

            try:
                # Breslow-Day chi square test for homogeneity of OR across
                # strata
                if self.ORda is None:
                    raise NotAvailable
                self.BDchisqOR = 0.0
                for i in range(len(ORarr)):
                    # print ORarr[i], self.ORda, wORarr[i]
                    self.BDchisqOR += ((math.log(ORarr[i]) - math.log(self.ORda))**2) / (1.0 / wORarr[i])
                # print r.pchisq(self.BDchisqOR, len(ORarr)-1)
                self.pBDchisqOR = 1.0 - r.pchisq(self.BDchisqOR, len(ORarr)-1)
            except MathError:
                self.BDchisqOR = None
                self.pBDchisqOR = None

    def _repr_adjusted(self, res_section, section):
        assert len(self.strata) > 1
        if section == 'counts':
            return
        subsec = res_section.new_subsection('Adjusted')
        if section == 'measures_of_association':
            if True in self.expLT5:
                subsec.fmt('Warning: expected values in some strata are < 5: use of exact statistics recommended.')
            subsec.fmt('Mantel-Haenszel chi square with continuity correction: %s (p=%s)', self.MH_chisq_contcorr_statistic, self.MH_chisq_contcorr_pvalue)
            # subsec.fmt('Mantel-Haenszel chi square without continuity correction: %s (p=%s)', self.MhUncorrSummaryChiSq, self.pMhUncorrSummaryChiSq)
            subsec.fmt('Mantel-Haenszel chi square without continuity correction: %s (p=%s)', self.MH_chisq_nocontcorr_statistic, self.MH_chisq_nocontcorr_pvalue)
            subsec.fmt('Fisher exact test: one-sided: p=%s, two-sided (twice one-sided): p=%s, two-sided (as extreme): p=%s', self.MH_exact_pvalue_onesided, self.MH_exact_pvalue_twosided_twiceonesided, self.MH_exact_pvalue_twosided_asextreme, )
            subsec.fmt('Mid-p exact test: one-sided: p=%s, two-sided: p=%s', self.MH_mid_p_onesided, self.MH_mid_p_twosided)
        elif section == 'risk_based':
            subsec.fmt('Directly adjusted risk ratio: %s (%s, %s)', self.adjRRdirect, self.lowerRRdirect, self.upperRRdirect)
            subsec.fmt('Mantel-Haenszel adjusted risk ratio: %s (%s, %s)', self.adjRRmh, self.lowerRRmh, self.upperRRmh)
            subsec.fmt('Breslow-Day chi square test for homogeneity of RR across strata: %s (p=%s)', self.BDchisqRR, self.pBDchisqRR)
            subsec.fmt('Directly adjusted risk difference: %s (%s, %s)', self.adjRDdirect, self.lowerRDdirect, self.upperRDdirect)
            subsec.fmt('Breslow-Day chi square test for homogeneity of RD across strata: %s (p=%s)', self.BDchisqRD, self.pBDchisqRD)
        elif section == 'odds_based':
            subsec.fmt('Directly adjusted common odds ratio: %s (%s, %s)', self.ORda, self.lowerORda, self.upperORda)
            # subsec.fmt('Mantel-Haenszel common odds ratio: %s (%s, %s)', self.adjORmh, self.lowerORmh, self.upperORmh)
            subsec.fmt('Mantel-Haenszel common odds ratio: %s (%s, %s)', self.MH_commonOR, self.MH_commonOR_ll, self.MH_commonOR_ul)
            subsec.fmt('CMLE common odds ratio: %s (%s, %s)', self.MH_exact_commonOR, self.MH_exact_commonOR_ll, self.MH_exact_commonOR_ul)
            subsec.fmt('Breslow-Day chi square test for homogeneity of OR across strata: %s (p=%s)', self.BDchisqOR, self.pBDchisqOR)
            subsec.fmt('Woolf chi square test for homogeneity of OR across strata: %s, df=%s (p=%s)', self.WchisqOR, self.dfWchisqOR, self.pWchisqOR)

    _sections = [
        ('counts', 'Tabulated values'),
        ('measures_of_association', 'Measures of association'),
        ('risk_based', 'Risk-based measures'),
        ('odds_based', 'Odds-based measures'),
    ]
    sections = [s[0] for s in _sections]
    section_labels = dict(_sections)

    def report(self, sections=None):
        if sections is None:
            sections = self.sections
        r.sink("/dev/null")
        try:
            self.calc()
        finally:
            r.sink()
        for section in sections:
            label = self.section_labels[section]
            if section in ('risk_based', 'odds_based'):
                label += ' (%g%% conf. limits)' % (self.conflev * 100)
            res_section = _ReportSection(label)
            for stratum in self.strata:
                stratum.report(section, res_section)
            if len(self.strata) > 1:
                self.unstratified.report(section, res_section, crude=True)
                self._repr_adjusted(res_section, section=section)
            yield res_section

    def __str__(self):
        lines = []
        for res_section in self.report():
            lines.append(str(res_section))
        return '\n'.join(lines)


if __name__ == '__main__':
    import time

    starttime = time.time()
    x = twobytwotable()
    # OpenEpi example data
    x.add_stratum(66,36,28,32)
    x.add_stratum(139,93,61,54)
    print "OpenEpi example values"
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # example from Armitage and Berry
    x.add_stratum(1,21,4,16)
    print "Armitage and Berry example"
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # StatExact homogeneity of OR example 14.4.1 Alcohol and Oesophageal cancer
    x.add_stratum(1,0,9,106)
    x.add_stratum(4,5,26,164)
    x.add_stratum(25,21,29,138)
    x.add_stratum(42,34,27,139)
    x.add_stratum(19,36,18,88)
    x.add_stratum(5,8,0,31)
    print
    print "=============================================================="
    print "StatExact example 14.4.1 Alcohol and Oesophageal cancer values"
    print "Breslow-Day homogeneity of OR chi-sq should be 9.323,p=0.0968"
    print "CMLE common OR should be 5.251 with exact CI of (3.572, 7.757)"
    print "and mid-p exact CI of (3.630, 7.629)"
    print "Mantel-Haenszel common OR should be 5.158 with RGB CO of (3.562, 7.468)"
    print "All p-values should be < 0.0000"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # StatExact example
    x.add_stratum(1,0,9,106)
    # x.add_stratum(4,5,26,164)
    print
    print "StatExact example values"
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed


    starttime = time.time()
    x = twobytwotable()
    # StatExact extremely ill-conditioned data example
    x.add_stratum(4,0,16,7)
    x.add_stratum(4,0,13,7)
    x.add_stratum(2,0,13,8)
    x.add_stratum(1,0,17,8)
    x.add_stratum(1,0,17,8)
    x.add_stratum(1,0,29,10)
    x.add_stratum(2,0,29,10)
    x.add_stratum(1,0,30,10)
    x.add_stratum(1,0,30,10)
    x.add_stratum(1,0,33,13)
    print
    print "=============================================================="
    print "StatExact example 14.5.3 Extremely imbalanced minority hiring"
    print "CMLE common OR should be +Inf with exact CI of (1.819, +Inf)"
    print "and mid-p exact CI of (3.069, +Inf)"
    print "Mantel-Haenszel common OR cannot be estimated"
    print "One-sided exact p-value for common OR=1.0 should be 0.0022"
    print "Two-sided exact p-value for common OR=1.0 should be 0.0043 or 0.0044"
    print "MH two-sided p-value for common OR=1.0 should be 0.0063"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Other extremely ill-conditioned data example
    x.add_stratum(0,4,16,7)
    x.add_stratum(0,4,13,7)
    x.add_stratum(0,2,13,8)
    x.add_stratum(0,1,17,8)
    x.add_stratum(0,1,17,8)
    x.add_stratum(0,1,29,10)
    x.add_stratum(0,2,29,10)
    x.add_stratum(0,1,30,10)
    x.add_stratum(0,1,30,10)
    x.add_stratum(0,1,33,13)
    print
    print "=============================================================="
    print "Another extremely ill-conditioned data example - all zeros in cell A"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Other extremely ill-conditioned data example
    x.add_stratum(16,4,0,7)
    x.add_stratum(13,4,0,7)
    x.add_stratum(13,2,0,8)
    x.add_stratum(17,1,0,8)
    x.add_stratum(17,1,0,8)
    x.add_stratum(29,1,0,10)
    x.add_stratum(29,2,0,10)
    x.add_stratum(30,1,0,10)
    x.add_stratum(30,1,0,10)
    x.add_stratum(33,1,0,13)
    print
    print "=============================================================="
    print "Another extremely ill-conditioned data example - all zeros in cell C"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Other extremely ill-conditioned data example
    x.add_stratum(16,4,7,0)
    x.add_stratum(13,4,7,0)
    x.add_stratum(13,2,8,0)
    x.add_stratum(17,1,8,0)
    x.add_stratum(17,1,8,0)
    x.add_stratum(29,1,10,0)
    x.add_stratum(29,2,10,0)
    x.add_stratum(30,1,10,0)
    x.add_stratum(30,1,10,0)
    x.add_stratum(33,1,13,0)
    print
    print "=============================================================="
    print "Another extremely ill-conditioned data example - all zeros in cell D"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Other extremely ill-conditioned data example
    x.add_stratum(16,4,7,7)
    x.add_stratum(0,0,0,0)
    x.add_stratum(13,2,8,8)
    print
    print "=============================================================="
    print "Another extremely ill-conditioned data example - zeros in all cells in one stratum"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Other extremely ill-conditioned data example
    x.add_stratum(0,0,0,0)
    x.add_stratum(0,0,0,0)
    print
    print "=============================================================="
    print "Another extremely ill-conditioned data example - zeros in all cells in all strata"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Large single stratum
    x.add_stratum(950,999,234,789)
    print
    print "=============================================================="
    print "Large single stratum"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Large single stratum with one small cell
    x.add_stratum(950,999,23,789)
    print
    print "=============================================================="
    print "Large single stratum with one small cell"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Very large single stratum with a small cell
    x.add_stratum(9504,8997,43,7892)
    print
    print "=============================================================="
    print "Very large single stratum with a small cell"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Very large single stratum
    x.add_stratum(9504,8997,8943,7892)
    print
    print "=============================================================="
    print "Very large single stratum"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Two very large strata with small cells
    x.add_stratum(9504,8997,43,7892)
    x.add_stratum(9763,8345,27,8765)
    print
    print "=============================================================="
    print "Two very large single strata with small cells"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

    starttime = time.time()
    x = twobytwotable()
    # Two very large strata
    x.add_stratum(9504,8997,8943,7892)
    x.add_stratum(9763,8345,7827,8765)
    print
    print "=============================================================="
    print "Two very large single strata"
    print "=============================================================="
    print x
    elapsed = time.time() - starttime
    print '%.3f seconds' % elapsed

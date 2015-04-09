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
# $Id: martinstats.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/sandbox/martinstats.py,v $

# reverse-engineered version of OpenEpi MartinStats.js module - calculates
# Fisher's exact and conditional maximum likelihood estimates 

import sys
# Some constants
MAXDEGREE = 100000 # max degree of polynomial
MAXITER = 10000 # max number of iterations to bracket/converge to a root
TOLERANCE = 0.0000001 # relative tolerance level for results
INFINITY = -sys.maxint # used to represent infinity
NAN = None # used to represent Not a Number

function CheckData(datatype, tables):
    curTbl = list()
    sumA = 0
    minSumA = 0
    maxSumA = 0
    for i in range(len(tables)):
        curTbl = tables[i]
        
        
##########################################################################
###################################################################################
import sys

function CheckData(datatype, tables):
    curTbl = list()
    sumA = 0
    minSumA = 0
    maxSumA = 0
    for i in range(len(tables)):
        curTbl = tables[i]


class MartinAustin(object): # class for Martin-Austin exact stats

    def __init__(self,datatype=1,conflevel=0.95):
        "Datatypes: 1=stratified case-control, 2=matched case-control, 3=stratified person-time"
        self.conflevel = conflevel
        if datatype not in (1,):
            raise ValueError, 'datatype must be 1' # not supporting other types yet
        else:
            self.datatype = datatype
        # Some constants
        self.MAXDEGREE = 100000 # max degree of polynomial
        self.MAXITER = 10000 # max number of iterations to bracket/converge to a root
        self.TOLERANCE = 0.0000001 # relative tolerance level for results
        self.INFINITY = -sys.maxint # used to represent infinity
        self.NAN = None # used to represent Not a Number
        # other attributes
        self.NumColumns 
        self.NumRows 
        self.NumStrata  
        self.Tables = list() # List to be filled with Table objects

        self.sumA=0 # Sum of the observed "a" cells }
        self.minSumA=0 # Lowest value of "a" cell sum w/ given margins }
        self.maxSumA=0 # Highest value of "a" cell sum w/ given margins }

        self.polyD = list() # Vector of polynomial of conditional coefficients
        self.degD = 0  # The degree of polyD 

        self.value =0.0 # Used in defining Func???

        self.polyN = list() #  Vector - The "numerator" polynomial in Func 
        self.degN =0
        
    def add_Table(self,e1d1,e0d1,e1d0,e0d0):
        self.Tables.append(MAstratum(e1d1,e0d1,e1d0,e0d0,datatype=1,conflevel=self.conflevel))

    def _CalcExactLim(self,pbLower, pbFisher, pvApprox, pnConfLevel):
       var pnLimit
        if (self.minSumA < self.sumA) and (self.sumA < self.maxSumA): 
            pnLimit = self._getExactLim (pbLower, pbFisher, pvApprox, pnConfLevel)
        elif self.sumA == self.minSumA: 
            # Point estimate = 0 => pbLower pnLimit = 0 
            if pbLower: 
                pnLimit = 0
            else
                pnLimit = self._getExactLim( pbLower, pbFisher, pvApprox, pnConfLevel)
        elif self.sumA == self.maxSumA: 
            # Point estimate = inf => upper pnLimit = inf
            if not pbLower: 
                pnLimit = self.INFINITY
            else:
                pnLimit = self._getExactLim( pbLower, pbFisher, pvApprox, pnConfLevel)
       return pnLimit

    def _GetExactLim(self, pbLower, pbFisher, pvApprox, pnConfLevel)  
        # var i, error  //
        pvLimit = None
        if pbLower: 
            self.value = 0.5 * (1 + pnConfLevel)  #  = 1 - alpha / 2 
        else:
            self.value = 0.5 * (1 - pnConfLevel) # = alpha / 2 
        if pbLower and pbFisher: 
            # Degree of numerator poly 
            self.degN = self.sumA - self.minSumA - 1
        else:
            self.degN = self.sumA - self.minSumA 

        # re-dimension polyN(degN)
        for  i in range(self.degN + 1):
            self.polyN[i] = self.polyD[i] # self.degN!=self.degD => self.polyN!=self.polyD }

        if not pbFisher: 
            self.polyN[self.degN] = (0.5) * self.polyD[self.degN] #  Mid-P adjustment 
            pvLimit = self._converge(pvApprox) # Solves so that Func(pvLimit) = 0 
	    return pvLimit	

    def _CalcCmle(self,approx):
        # var cmle
        if (self.minSumA < self.sumA) and (self.sumA < self.maxSumA): 
            # Can calc point estimate
            cmle = self._GetCmle(approx)
        elif self.sumA == self.minSumA: 
            # Point estimate = 0 
            cmle = 0
        elif self.sumA == self.maxSumA: 
            # Point estimate = inf 
            cmle = self.INFINITY
	    return cmle

    def _GetCmle(self,approx)
        # var i, error,cmle
        self.value = self.sumA  #  The sum of the observed "a" cells
        self.degN = self.degD # Degree of the numerator polyNomial 
        for i in range(self.degN+1): # Defines the numerator polynomial 
            self.polyN[i] = (self.minSumA + i) * self.polyD[i]
        cmle = self._converge(approx)  # Solves so that Func(cmle) = 0 
        return cmle

    # This routine returns the exact P-values as defined in "Modern
    # Epidemiology" by K. J. Rothman (Little, Brown, and Co., 1986).

    def _CalcExactPVals(self):
        # var i, diff  #  Index; sumA - minSumA 
        # var upTail, denom  # Upper tail; the whole distribution
        pValues = dict()
        diff = self.sumA - self.minSumA
        upTail = self.polyD[self.degD]
        for i in range(self.degD - 1, diff - 1,-1):
            upTail = upTail + self.polyD[i]
        denom = upTail
        for i in range(diff - 1, -1, -1):
            denom = denom + self.polyD[i]
        pValues["upFishP"] = upTail / float(denom)
        pValues["loFishP"] = 1.0 - (upTail - self.polyD[diff]) / float(denom)
        pValues["upMidP"] = (upTail - 0.5 * self.polyD[diff]) / float(denom)
        pValues["loMidP"] = 1.0 - pValues["upMidP"]
        return pValues

    # The functions that follow (_BracketRoot, _Zero, and _Converge) locate a zero 
    # to the function Func .                                                

    def _Zero(self, x0, x1, f0, f1):
        # Takes in an array of x0,x1,f0, and f1 and returns a root or an error
        # var root
        found = False # Flags that a root has been found 
        # var x2, f2, swap # Newest point, Func(X2), storage variable
        # var iter  # Current number of iterations 
        var x0=nums.x0;
        var x1=nums.x1;
        var f0=nums.f0;
        var f1=nums.f1;
        error = 0 
        iter = 0
        if abs(f0) < abs(f1):
            # Make X1 best approx to root 
            x1, x0 = x0, x1
            f1, f0 = f0, f1
        if f1 == 0:
            found = True
        if not found and (f0 * f1) > 0: 
            error = 1 # Root not bracketed 
        while not found and iter < self.MAXITER and error == 0:
            iter += 1
            x2 = x1 - f1 * (x1 - x0) / float(f1 - f0)
            f2 = self._func(x2)
            if f1 * f2 < 0: 
                # x0 not retained}
                x0 = x1
                f0 = f1
            else
                # x0 retained => modify f0 }
                f0 = f0 * f1 / float(f1 + f2) # The Pegasus modification 
            x1 = x2
            f1 = f2
            if abs(x1 - x0) < abs(x1) * self.TOLERANCE) or f1 == 0:
                found = True
        root = x1 # Estimated root
        if not found and iter >= self.MAXITER and error == 0:
	        error=2 # Too many iterations 
        return root, error

    def _BracketRoot(self, approx)
        # Returns x0,x1,f1,f0
        iter = 0
        x1 = max(0.5, approx) # x1 is the upper bound
        x0 = 0  # x0 is the lower bound
        f0 = self._func(x0) # Func at x0
        f1 = self.func(x1) # Func at X1
        while f1 * f0 > 0.0 and iter < self.MAXITER: 
	        iter += 1
            x0 = x1 # What does this accomplish?  x0 does not seem to be used.
            f0 = f1
            x1 = x1 * 1.5 * iter
            f1 = self._func(x1)
	    return x0, x1, f0, f1


    # This routine returns the root of Func above on the interval [0, infinity].
    def _Converge(self,approx)
        # Returns the root or an error 
        # var rootc
        # var error
        x0, x1, f0, f1 = self._BracketRoot(approx)
        rootc, error = self._Zero(x0, x1, f0, f1)
        if error==0:
            return rootc
	    else:
 	        return self.NAN

    # Below is a routine for evaluating a polynomial. If the value at which the  
    # polynomial is being evaluated is > 1.0 then the polynomial is divided      
    # through by R^(degree of the poly). This helps to prevent floating point    
    # overflows but must be taken into account when evaluating Func below.       

    def _EvalPoly(self, c, degC, r) 
        # var i
        # var y 
        if r == 0: 
            y = c[0]
        elif r <= 1: 
            y = c[degC]
            if r < 1: 
                for i in range(degC - 1),-1,-1):
			        y = y * r + c[i]
            else:
                for i in range(degC - 1), -1, -1):
                    y = y + c[i]
        elif r > 1: 
            y = c[0]
            r = 1 / float(r)
            for i in range(1,degC +1):
                y = y * r + c[i]
        return y

    def _Func(self, r)
        # var numer , denom 
        numer = self._EvalPoly(self.polyN, self.degN, r)
        denom = self._EvalPoly(self.polyD, self.degD, r)  
        if r <= 1: 
            return numer / float(denom) - (self.value)
        else:
	        return (numer / float(r**(self.degD - self.degN))) / float(denom)) - self.value

    # Following is the key routine which outputs the "main" polynomial of 
    # conditional distribution coefficients to be used to compute exact  
    # estimates.                                                         

    def _CalcPoly(self, DataType)
        # This routine outputs the "main" polynomial of conditional distribution
        # coefficients which will subsequently be used to calculate the conditional
        # maximum likelihood estimate, exact confidence limits, and exact P-values.
        # The results are placed in the global variables, this.polyD and this.degD.
        # For a given data set, this routine MUST be called once before calling
        # CalcExactPVals(), CalcCmle(), and CalcExactLim(). Note that DATATYPE
        # indicates the type of data to be analyzed (1 = stratified case-control,
        # 2 = matched case-control, 3 = stratified person-time).
        poly1 = list()
        poly2 = list()  # Intermediate polynomials 
        # var i, j, deg1, deg2  # Index; degree of polynomials poly1 & poly2 
        CurTable = list() # ???
        CurTable = self.Tables[0]
        if DataType==1:
	        self.degD = self._PolyStratCC(CurTable, self.polyD)
        elif DataType==2:
            self.degD = self._PolyMatchCC(CurTable, self.polyD)
        elif DataType==3:
            self.degD = self._PolyStratPT(CurTable, self.polyD)
        else:
	        raise ValueError, "DataType must be 1, 2 or 3."

        for i in range(1,len(self.Tables):
            CurTable = self.Tables[i]
            Poly1 = list() # Reinitialise Poly1
            if CurTable.informative: 
	            deg1 = self.degD
      		    for j in range(deg1 + 1):    
			        # Copy self.polyD to poly1
        		    poly1[j] = self.polyD[j]
                if DataType==1:
			       deg2 = self._PolyStratCC(CurTable, poly2)
			    elif DataType==2:
			       deg2 = self._PolyMatchCC(CurTable, poly2)
			    elif DataType==3:
			       deg2 = self._PolyStratPT(CurTable, poly2)
			    else:
        	        raise ValueError, "DataType must be 1, 2 or 3."
                self.degD = self._MultPoly( poly1, poly2, deg1, deg2, self.polyD)

    # This routine multiplies together two polynomials p1 and p2 to obtain
    # the product polynomial P3. Reference: "Algorithms" 2nd ed., by R.
    # Sedgewick (Addison-Wesley, 1988), p. 522.
    def _MultPoly(self, p1 , p2 , deg1, deg2, p3 ):
        # p1, p2 are the two polynomials
        # deg1, deg2 are the degrees of the above polynomials
        # p3 is the product polynomial of p1 * p2
        # deg3 is the degree of the product polynomial
        # var i, j
        deg3 = deg1 + deg2
        for i in range(deg3 + 1):
	        p3[i] = 0.0
        for i in range(deg1 + 1):
            for j in range(deg2 + 1):  
                p3[i + j] = p1[i] * p2[j] + p3[i + j]
	    return deg3

    def _Comb(self, y, x)
        # Returns the combination y choose x.
        # var i
        # var f
        f = 1.0
        for i in range(1,round(min(x,y-x)) + 1):
            f = f * y / float(i)
            y = y - 1.0
        return f

    # Routines are given to calculate stratum-specific polynomials
    def _PolyStratCC(self, Table, polyDi)
        # var i
        # var minA, maxA, aa, bb, cc, dd
        degDi = 0
        polyDi[0] = 1.0
        if Table.informative: 
            minA = max(0, Table.m1 - Table.n0) # Min val of the "a" cell w/ these margins
            maxA = min(Table.m1, Table.n1) # Max val of the "a" cell w/ these margins 
            degDi = round(maxA - minA) # The degree of this table's polynomial }
            aa = minA                       # Corresponds to the "a" cell
            bb = Table.m1 - minA + 1        # Corresponds to the "b" cell 
            cc = Table.n1 - minA + 1        # Corresponds to the "c" cell
            dd = Table.n0 - Table.m1 + minA # Corresponds to the "d" cell 
            for i in range(1,degDi + 1):
                polyDi[i] = polyDi[i - 1] * ((bb - i) / float(aa + i)) * ((cc - i) / float(dd + i))
        return degDi

    def _BinomialExpansion(self, c0, c1, f, p, degp):
        # var i
        degp = f
        p[degp] = c1**degp
        for i in range(degp - 1, -1, -1):
            p[i] = p[i + 1] * c0 * (i + 1) / float(c1 *(degp - i))
        return c0, c1, f, p, degp

    def _PolyMatchCC(self, Table, polyEi)
        # var c0, c1
        degEi = 0
        polyEi[0] = 1.0
        if Table.informative: 
            c0 = (self._Comb(Table.n1, 0) * self._Comb(Table.n0, Table.m1)) # Corresponds to 0 in "a" cell 
            c1 = (self._Comb(Table.n1, 1) * self._Comb(Table.n0, Table.m1 - 1)) # Corresponds to 1 in "a" cell
            c0, c1, freq, polyEi, degEi = self._BinomialExpansion (c0, c1, freq, polyEi, degEi)
       return polyEi.length-1 # Need to subtract 1???


    def _PolyStratPT(self, Table, polyDi)
        degDi = 0
        polyDi[0] = 1.0
        if Table.informative: 
            self._BinomialExpansion((Table.n0 / float(Table.n1)), 1.0, round(Table.m1), polyDi, degDi)
        return len(polyDi) - 1


    def _CheckData(self, DataType)
        # numTables Number of "unique" 2x2 tables 
        # var tables  list of 2x2 table data 
        # var error Flags error in data 
        # This routine determines if the data allow exact estimates to be calculated.
        # It MUST be called once prior to calling CalcPoly() given below. DATATYPE
        # indicates the type of data to be analyzed (1 = stratified case-control,
        # 2 = matched case-control, 3 = stratified person-time). Exact estimates
        # can only be calculated if ERROR = 0.
        #
        # Errors : 0 = can calc exact estimates, i.e., no error,
        #          1 = too much data (MAXDEGREE too small),
        #          2 = no informative strata.
        #          3 = More than one case in a Matched Table (added July 21, 1998)
        # var i
        curTbl = list()
        error = 0
        # Compute the global vars SUMA, MINSUMA, MAXSUMA 
        self.sumA = 0
        self.minSumA = 0
        self.maxSumA = 0
        for i in range(len(self.Tables)):
            curTbl = self.Tables[i]
            if curTbl.informative: 
		        self.sumA += round(curTbl.a * curTbl.freq)
                if DataType in (1,2): 
                    # Case-control data 
            	    self.minSumA += round(max(0, curTbl.m1 - curTbl.n0) * curTbl.freq) 
            	    self.maxSumA += round(min(curTbl.m1, curTbl.n1) * curTbl.freq) 
                else:
                    # Person-time data 
            	    self.minSumA = 0
            	    self.maxSumA = round(curTbl.m1 * curTbl.freq) + self.maxSumA

            # Check for errors
            if self.maxSumA - self.minSumA > self.MAXDEGREE:
                # Poly too small 
                error = 1
            elif self.minSumA == self.maxSumA: 
                # No informative strata 
                error = 2
            elif DataType == 2 and curTbl.a > 1: 
                error = 3
        return error;

    def _Strat2x2(self, stratum, ORbased, RRbased, assoc, references):
        self._Process(stratum, 1, self.confLevel, ORbased, RRbased, assoc, references)  

    def _MatchedCC(self, stratum, ORbased, RRbased, assoc, references):     
        self._Process(stratum, 2, self.confLevel, ORbased, RRbased, assoc, references)   

    def _PersonTime(self, stratum, ORbased, RRbased, assoc, references):     
        self._Process(stratum, 3, self.confLevel, ORbased, RRbased, assoc, references)  

    def _addCCTbl(self, a,b,c,d,freq,tableArray):
        tbl = dict() # Should be an MAstratum instance!
        tbl.a = a
        tbl.b = b
        tbl.c = c
        tbl.d = d
        tbl.freq = freq
        tbl.m1 = tbl.a + tbl.b # number of cases 
        tbl.n1 = tbl.a + tbl.c # number of exposed
        tbl.n0 = tbl.b + tbl.d # number of unexposed 
        if tbl.a * tbl.d != 0 or tbl.b * tbl.c != 0:
            tbl.informative = True
        else:
            tbl.informative = False
        tableArray[tableArray.length]=tbl # check this!
    # UP TO HERE

def _Process(self, stratum, DataType, pnConfLevel, ORbased, RRbased, assoc, references):
    # var b, c, d  //    { b, c, d cells of 2x2 table }
    # var numTables  //   { Number of "unique" 2x2 tables }

    # var cmle        //    { Odds Ratio (cond. max. likelihood estimate) }
    # var loFishLim   //    { Lower exact Fisher confidence limit }
    # var upFishLim   //    { Upper exact Fisher confidence limit }
    # var loMidPLim   //    { Lower mid-P confidence limit }
    # var upMidPLim   //    { Upper mid-P confidence limit }
    # var approx  //    { An approximation to the exact estimate }
    # var error  //   { Error in procedure CheckData }
    # var s  // temporary string
    # var i   //temporary number
    # var errornum   //
    # this.resultString = ""  //
    # this.resultArray= new Array()
    # var  NumColumns = this.cmdObj.data[0].cols
    # var  NumRows = this.cmdObj.data[0].rows
    # var firststratum, laststratum,NumStrata;
    # // initialize variables
    self.pValues = list() # Holds all 4 p values
    self.polyD = list()   # The polynomial of conditional coefficients 
    self.degD =0  # The degree of polyD 
    self.value =0.0 # Used in defining Func
    self.polyN = list() # The "numerator" polynomial in Func 
    self.degN =0;
    self.cl = pnConfLevel*100    # Confidence limit for output formatting

    self.Tables = list()   # initialize Tables array
    # check this
    NumStrata = this.cmdObj.data[0].strata; //May be reset to 1 if only one table is currently
                                           //being processed
    var totalstrata=this.cmdObj.data[0].strata;  //Number of strata in dataset
   
   if (stratum==0) {stratum="Adjusted"}
   if (stratum=="Adjusted") 
    {   
	 
	 firststratum=1
	 laststratum=NumStrata
	// alert("stratum=all "+firststratum+" "+laststratum)
	}
	else if (parseInt(stratum)>0)
	{
	  NumStrata=1;
	  firststratum=stratum
	  laststratum=stratum
	}
	else if (stratum=="Crude")
    {
      dataTable=this.cmdObj.crudeTable()
	  firststratum=1
	  laststratum=1
    }
   var tbl = new Array()
   //alert("as defined tbl="+tbl)
    //ReDim Tables(NumStrata - 1)
   for (i = firststratum; i<= laststratum; i++)
	  {
	   tbl=new Array()
	   //tbl=null;
	   //tbl.length=0;
       if ( DataType == 1 )
       { 
 //                    { Stratified case-control }
         if (stratum=="Crude")
		 {
		 tbl.a = dataTable.E1D1  
         tbl.b = dataTable.E0D1   
         tbl.c = dataTable.E1D0  
         tbl.d = dataTable.E0D0  
		/*
		 alert("tbl.a crude="+tbl.a
		 +"\nb="+tbl.b
		 +"\nc="+tbl.c
		 +"\nd="+tbl.d)
		 */
		 }
		 else
		 {
		 tbl.a = this.cmdObj.data[i].E1D1  
         tbl.b = this.cmdObj.data[i].E0D1   
         tbl.c = this.cmdObj.data[i].E1D0  
         tbl.d = this.cmdObj.data[i].E0D0  
         }
         tbl.freq = 1 //
         tbl.m1 = tbl.a + tbl.b // { # cases }
         tbl.n1 = tbl.a + tbl.c // { # exposed }
         tbl.n0 = tbl.b + tbl.d // { # unexposed }
         tbl.informative = ((tbl.a * tbl.d) != 0) || ((tbl.b * tbl.c) != 0) 
   /*
	  alert( "stratum="+stratum+
	  "\ni="+i+
      "\na="+tbl.a+
	  "\nb="+tbl.b+
	  "\nc="+tbl.c+
	  "\nd="+tbl.d+
	  "\nfreq="+tbl.freq+
	  "\nm1="+tbl.m1+
	  "\nn1="+tbl.n1+
	  "\nn0="+tbl.n0+
	  "\ninformative="+tbl.informative+
	  "\nthis.cmdObj.data[1].E1D1="+this.cmdObj.data[1].E1D1) 
	 */  
	    }	
      else if(DataType == 2) 
        {  
		    
           //      Matched case-control 
		    if (this.cmdObj.data[0].numD==2 && 
		        this.cmdObj.data[0].numE==2)
		    {
			   //Two by two table.  Must be 1 to 1 matching.
			   //Other tables can be accomodated, but right now, we
			   //are setting up tables only for 1 to 1 matching.
			   //There are four possible tables, with frequencies 
			   //represented by the counts of pairs entered in OpenEpi.
			addCCTbl(1,0,0,1,this.cmdObj.data[i].E1D0,this.Tables);
			addCCTbl(1,0,1,0,this.cmdObj.data[i].E1D1,this.Tables);
			addCCTbl(0,1,0,1,this.cmdObj.data[i].E0D0,this.Tables);
			addCCTbl(0,1,1,0,this.cmdObj.data[i].E0D1,this.Tables);
			 
			   			
			}
           /*  tbl.a = this.cmdObj.data[i].E1D1  //
             tbl.c = this.cmdObj.data[i].E1D0   //
             tbl.d = this.cmdObj.data[i].E0D0   //
            // tbl.freq = pvaDataArray(2, 2, i)   //

            if ( tbl.a <= 1 ) 
            {
               b = 1 - tbl.a
            }
            else
            {
               b = -1
            }
            tbl.m1 = tbl.a + tbl.b // { # cases }
            tbl.n1 = tbl.a + tbl.c // { # exposed }
            tbl.n0 = tbl.b + tbl.d //           { # unexposed }
            tbl.informative = (tbl.a * tbl.d != 0) || (tbl.b * tbl.c != 0) 
			*/
         }
	  else if ( DataType == 3 ) 
        {
          //    Stratified person-time 
		 if (stratum=="Crude")
		 {
		 tbl.a = dataTable.E0D0  
         tbl.b = dataTable.E0D1   
         tbl.n1 = dataTable.E1D0  
         tbl.n0 = dataTable.E1D1  
		/*
		 alert("tbl.a crude="+tbl.a
		 +"\nb="+tbl.b
		 +"\nc="+tbl.c
		 +"\nd="+tbl.d)
		 */
		 }
		 else
		 { 
         tbl.a = this.cmdObj.data[i].E0D0    //
         tbl.b = this.cmdObj.data[i].E0D1     //
         tbl.n1 = this.cmdObj.data[i].E1D0    //
         tbl.n0 = this.cmdObj.data[i].E1D1    //
		 }
         tbl.freq = 1  //
         tbl.m1 = tbl.a + tbl.b  // { # cases }
         tbl.informative = (tbl.a * tbl.n0 != 0) 
		        || ((tbl.b * tbl.n1) != 0) 
		/*
		alert( "stratum="+stratum+
	  "\ni="+i+
      "\na="+tbl.a+
	  "\nb="+tbl.b+
	  "\nfreq="+tbl.freq+
	  "\nm1="+tbl.m1+
	  "\nn1="+tbl.n1+
	  "\nn0="+tbl.n0+
	  "\ninformative="+tbl.informative+
	  "\nthis.cmdObj.data[1].E1D1="+this.cmdObj.data[1].E1D1) 
	   */		
        }
     // End With
	 
	 if (DataType != 2) 
	  {
	  this.Tables[this.Tables.length]=tbl;
	  }
	// alert("450 this.Tables.length="+this.Tables.length);
   }//Next i
  /* alert("this.Tables has length="+this.Tables.length)
   for (i=0; i<this.Tables.length; i++)
    {
	  alert ("this.Tables["+i+"].a="+this.Tables[i].a)
	}
	*/
   errornum=this.checkData( DataType, this.Tables)  
   if ( errornum != 0 ) 
      {
	   if (errornum==1)
	       {
		     s="Exact calculations skipped, since numbers are large.  Use other results."
			 this.cmdObj.title(s)
             this.addToArray(this.resultArray,  "ERROR", 1 )
		   }
       else if (errornum==2)
	       {
             s="All tables have zero marginals. Cannot perform exact calculations."
             this.cmdObj.title(s)
             this.addToArray(this.resultArray,  "ERROR", 2) 
		   } //
       else if (errornum==3)
	       {
             s="PROBLEM: Must have only one case in each table for exact calculations."
             this.cmdObj.title(s)
             this.addToArray(this.resultArray,  "ERROR", 3 )
		   }
       }
 
  if (errornum==0)
   {
     //errornum was 0
	// try
	//  {
        this.calcPoly (DataType)
        pValues=this.calcExactPVals()
        cmle=this.calcCmle(1)
		//alert("cmle="+cmle);
		
        if (isNaN(cmle)||!isFinite(cmle)) 
       	{
            approx = this.maxSumA
        }
        else
		{
            approx = cmle
        }
        upFishLim=this.calcExactLim (false, true, approx, pnConfLevel)
        upMidPLim=this.calcExactLim (false, false, approx, pnConfLevel)
		
        loFishLim=this.calcExactLim (true, true, approx, pnConfLevel)
        loMidPLim=this.calcExactLim (true, false, approx, pnConfLevel)
       // this.cmdObj.newtable(6,100)
        //this.cmdObj.line(6)
	    var totalstrata=this.cmdObj.data[0].strata;
		if (stratum=="Adjusted" || stratum=="Crude" || totalstrata==1)
	    {
	      editorschoice1=editorschoice;
	    }
	    else
	    {
	      editorschoice1="";
	    }
		if (DataType==1 || DataType==2)
		  {
			//s="Exact Odds Ratio Estimates"
			//this.cmdObj.title(s)
			s="CMLE OR*" 
			references[0]='newrow("span6:*Conditional maximum likelihood estimate of Odds Ratio");' 
            ORbased[0]='newrow("c:bold:Stratum","c:bold:CMLE OR*","c:bold:span2:'+editorschoice1+'Mid-P Limits","c:bold:span2:Fisher Limits");'
			
			//newrow("span4:"+s,"",fmtSigFig(cmle,4))
		  }
		  else
		  {
			//s="Exact Rate Ratio Estimates"
			//this.cmdObj.title(s)
			//s= "Conditional maximum likelihood estimate of Rate Ratio:"
			//this.cmdObj.newrow("span5:"+s,"",fmtSigFig(cmle,4)) 
			s="CMLE RR*" 
			references[0]='newrow("span6:*Conditional maximum likelihood estimate of Rate Ratio");' 
            //ORbased[0]='newrow("c:bold:Stratum","c:bold:CMLE RR*","c:bold:span2:Mid-P Limits","c:bold:span2:Fisher Limits");'
			//ORbased[0]+='\nline(6)' 
			RRbased[0]='newrow("c:bold:Stratum","c:bold:CMLE RR*","c:bold:span2:Mid-P Limits","c:bold:span2:Fisher Limits");'
			RRbased[0]+='\nline(6)'
		  }
	  // this.addToArray(this.resultArray,  "CMLE", fmtSigFig(cmle,4)) 
	   //this.cmdObj.line(6)
	  // s="Lower & Upper " + pnConfLevel+"%" + " Exact Fisher Limits:"  
	  // this.cmdObj.newrow("span4:"+s,fmtSigFig(loFishLim,4), fmtSigFig(upFishLim,4))
	 var index=stratum;
	 
	 if(index=="Adjusted") {index=totalstrata+2}
	 if (index=="Crude") {index=totalstrata+1}
	 	
	  var pstratum ="";
	  if (totalstrata>1) {pstratum=stratum}
	  //alert("pstratum="+pstratum +"NumStrata="+NumStrata);
	  ORbased[index]='\nnewrow("'+pstratum +'","span2:CMLE Odds Ratio*",'+fmtSigFig(cmle,4)+','
	  ORbased[index]+='"c:span2:'+limits(loMidPLim,upMidPLim,1)+'","'+editorschoice1+'Mid-P Exact");'
	  ORbased[index]+='\nnewrow("","span2:","","c:span2:'+limits(loFishLim,upFishLim,1)+'","Fisher Exact");'
      if (DataType==3)
	    {
		  //Person Time data
		RRbased[index]='\nnewrow("'+pstratum +'","span2:'+editorschoice1+'CMLE Rate Ratio*",'+fmtSigFig(cmle,4)+','
	    RRbased[index]+='"c:span2:'+limits(loMidPLim,upMidPLim,1)+'","'+editorschoice1+'Mid-P Exact");'
//alert("cmle="+cmle);
 
	    RRbased[index]+='\nnewrow("","span2:","","c:span2:'+limits(loFishLim,upFishLim,1)+'","Fisher Exact");'

		}

	   assoc[0]='newrow("c:bold:Stratum","c:span2:bold:Value","c:bold:p-value(1-tail)","c:bold:p-value(2-tail)");'
	   assoc[0]+='\nline(5)'
	  //2-tail p is minimum value for Fisher and mid-P from the two values offered
	  //(per Rothman)
	  var FishP1Tail;
	  var FishP1TailType;
	  
	  var midP1Tail;
	  var midP1TailType;
	  
	  
      
	  if (pValues.upFishP<pValues.loFishP)
	     {
		  FishP1TailType=""
		  FishP1Tail=pValues.upFishP;
		 } 
		else
		 {
		  //One tail type tests negative (protective) association
		  FishP1TailType="(P)"
		  FishP1Tail=pValues.loFishP;
		 } 
		 
	  if (pValues.upMidP<pValues.loMidP)
	     {
		  midP1TailType=""
		  midP1Tail=pValues.upMidP;
		 } 
		else
		 {
		  //One tail type tests negative (protective) association
		  midP1TailType="(P)"
		  midP1Tail=pValues.loMidP;
		 }  
		 
	  var FishP2Tail=2*FishP1Tail;
	  var midP2Tail=2*midP1Tail;	  
	  
	  
	  var Fish1Tailstr="c:span2:"+fmtPValue(FishP1Tail,ConfLevel)+FishP1TailType;
	  //var midP1Tailstr="c:span2:"+"lower="+fmtPValue(pValues.loMidP,ConfLevel)+"<br>upper="+fmtPValue(pValues.upMidP,ConfLevel);
	  var midP1Tailstr="c:span2:"+fmtPValue(midP1Tail,ConfLevel)+midP1TailType;
	 
	  //assoc[index]='newrow("","c:span2:'+stratum+'","'+fmtPValue(FishP,ConfLevel)+'","'+fmtPValue(midP,ConfLevel)+'");'
	  assoc[index]='\nnewrow("","span2:Fisher exact","","'+Fish1Tailstr+'","c:span2:'+fmtPValue(FishP2Tail,ConfLevel)+ '");'
	  assoc[index]+='\nnewrow("","span2:'+editorschoice1+'Mid-P exact","","'+midP1Tailstr+'","c:span2:'+fmtPValue(midP2Tail,ConfLevel)+ '");' 
      
	   s="(P)indicates a one-tail P-value for Protective or negative association; otherwise one-tailed exact P-values are for a positive association.";
	   s+="<br>Martin,D; Austin,H (1991): An efficient program for computing "
	   s+="conditional maximum likelihood estimates and exact confidence "      
       s+="limits for a common odds ratio. Epidemiology 2, 359-362."
	   //this.cmdObj.newrow();
	   references[0]+='\nnewrow("span6:'+s+'")'            
       s="Martin,DO; Austin,H (1996): Exact estimates for a rate ratio."       
       s+="Epidemiology 7, 29-33."   
	   if (DataType==3)
	     {
		 references[0]+='\nnewrow("span6:'+s+'")' 
		 }
	   //endtable();
} //if errornum==0

}  //end of Process function











class MAstratum(object):

    def __init__(self,e1d1,e0d1,e1d0,e0d0,datatype=1,conflevel=0.95):
        self.conflevel = conflevel
        if datatype == 1: # Stratified case-control
		    self.a = e1d1  
            self.b = e0d1   
            self.c = e1d0  
            self.d = e0d0  
            self.freq = 1.0 
            self.m1 = self.a + self.b # cases
            self.n1 = self.a + self.c # exposed
            self.n0 = self.b + self.d # unexposed
            self.informative = ((self.a * self.d) != 0) or ((self.b * self.c) != 0) 
        else:
            raise ValueError, 'datatype must be 1' # not supporting other types yet
                


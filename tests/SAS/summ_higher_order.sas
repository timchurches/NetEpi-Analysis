/*
 *  The contents of this file are subject to the HACOS License Version 1.2
 *  (the "License"); you may not use this file except in compliance with
 *  the License.  Software distributed under the License is distributed
 *  on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
 *  implied. See the LICENSE file for the specific language governing
 *  rights and limitations under the License.  The Original Software
 *  is "NetEpi Analysis". The Initial Developer of the Original
 *  Software is the Health Administration Corporation, incorporated in
 *  the State of New South Wales, Australia.
 *
 *  Copyright (C) 2004,2005 Health Administration Corporation.
 *  All Rights Reserved.
 */

options nodate pageno=1 linesize=100 pagesize=60;

data testdata;
file 'c:\temp\testdata.txt' ;
keep z a b c d e f  ;
letters = 'abc' ;
attrib cola length=$2000
       colb length=$2000
       colc length=$2000
       cold length=$2000
       cole length=$32000
       colf length=$32000
       z length=$1
       a length=$1
       b length=$1
       c length=$1
       d length=$1
       e length=8
       f length=8
       sume length=8
       sumf length=8 ;
sume = 0 ;
sumf = 0 ;
z = 'z' ;
do t = 1 to 200 ;
   a = substr(letters,int(ranuni(123)*3 + 1),1) ;
   b = substr(letters,int(ranuni(456)*3 + 1),1) ;
   c = substr(letters,int(ranuni(789)*3 + 1),1) ;
   d = substr(letters,int(ranuni(246)*3 + 1),1) ;
   e = ranuni(999) ;
   f = ranuni(888) ;
   cola = trim(left(cola)) || "'" || a || "', " ;
   colb = trim(left(colb)) || "'" || b || "', " ;
   colc = trim(left(colc)) || "'" || c || "', " ;
   cold = trim(left(cold)) || "'" || d || "', " ;
   cole = trim(left(cole)) ||  put(e,18.16) || ", " ;
   colf = trim(left(colf)) ||  put(f,18.16) || ", " ;
   output ;
   sume = sume + e ;
   sumf = sumf + f ;
end ;
put cola= ;
put colb= ;
put colc= ;
put cold= ;
put cole= ;
put colf= ;
file log ;
put sume 18.16 ;
put sumf 18.16 ;
run ;


proc summary data=testdata ;
   class a b c ;
   var e ;
   freq f ;
   output out=test_out n=n mean=wgt_meane;
   run;

data test_out ;
 set test_out ;
 if _type_ = '000'b then level = 0 ;
 if _type_ = '100'b or _type_ = '010'b or _type_ = '001'b  then level = 1 ;
 if _type_ = '110'b or _type_ = '101'b or _type_ = '011'b then level = 2 ;
 if _type_ = '111'b then level = 3 ;
 if a = ' ' then a = 'z' ;
 if b = ' ' then b = 'z' ;
 if c = ' ' then c = 'z' ;
run ;


data level_111 ;
 set test_out ;
 * if _type_ = '111'b ;
 n_111 = n ;
 drop n ;
 run ;
data level_011 ;
 set test_out ;
 if _type_ = '011'b ;
 n_011 = n ;
 drop n ;
 run ;
proc sort data=level_011 ;
 by b c ;
  run ;
data level_101 ;
 set test_out ;
 if _type_ = '101'b ;
 n_101 = n ;
 drop n ;
run ;
proc sort data=level_101 ;
 by a c ;
  run ;
data level_110 ;
 set test_out ;
 if _type_ = '110'b ;
 n_110 = n ;
 drop n  ;
run ;
proc sort data=level_110 ;
 by a b ;
  run ;
data level_001 ;
 set test_out ;
 if _type_ = '001'b ;
 n_001 = n ;
 drop n  ;
 run ;
proc sort data=level_001 ;
 by c ;
  run ;
data level_010 ;
 set test_out ;
 if _type_ = '010'b ;
 n_010 = n ;
 drop n  ;
 run ;
proc sort data=level_010 ;
 by b ;
  run ;
data level_100 ;
 set test_out ;
 if _type_ = '100'b ;
 n_100 = n ;
 drop n  ;
 run ;
proc sort data=level_100 ;
 by a  ;
  run ;
data level_000 ;
 set test_out ;
 if _type_ = '000'b ;
 n_000 = n ;
 drop n  ;
 run ;

*******;

proc sort data=level_111 ;
 by b c ;
 run ;
data testprops ;
 merge level_011  level_111(in=b111) ;
 by b c;
 if b111 ;
 run ;
proc sort data=testprops ;
 by b ;
 run ;
data testprops ;
 merge level_011  testprops(in=b111) ;
 by b ;
 if b111 ;
 run ;
proc sort data=testprops ;
 by c ;
 run ;
data testprops ;
 merge level_011  testprops(in=b111) ;
 by c ;
 if b111 ;
 run ;


 proc sort data=testprops ;
 by a c ;
 run ;
data testprops ;
 merge level_101 testprops(in=b111) ;
 by a c;
 if b111 ;
 run ;
 proc sort data=testprops ;
 by a ;
 run ;
data testprops ;
 merge level_101 testprops(in=b111) ;
 by a ;
 if b111 ;
 run ;
 proc sort data=testprops ;
 by c ;
 run ;
data testprops ;
 merge level_101 testprops(in=b111) ;
 by c;
 if b111 ;
 run ;




proc sort data=testprops ;
 by a b ;
 run ;
data testprops ;
 merge level_110 testprops(in=b111) ;
 by a b;
 if b111 ;
 run ;
proc sort data=testprops ;
 by a ;
 run ;
data testprops ;
 merge level_110 testprops(in=b111) ;
 by a ;
 if b111 ;
 run ;
proc sort data=testprops ;
 by b ;
 run ;
data testprops ;
 merge level_110 testprops(in=b111) ;
 by b;
 if b111 ;
 run ;




proc sort data=testprops ;
 by a ;
 run ;
data testprops ;
 merge level_100 testprops(in=b111) ;
 by a ;
 if b111 ;
 run ;
proc sort data=testprops ;
 by b ;
 run ;
data testprops ;
 merge level_010 testprops(in=b111) ;
 by b ;
 if b111 ;
 run ;
proc sort data=testprops ;
 by c ;
 run ;
data testprops ;
 merge level_001 testprops(in=b111) ;
 by c ;
 if b111 ;
 run ;
data testprops ;
 set testprops ;
 n_000 = 200 ;
 drop _freq_ _type_  ;

select ;
  when (_type_ = '111'b) n = n_111 ;
  when (_type_ = '011'b) n = n_011 ;
  when (_type_ = '101'b) n = n_101 ;
  when (_type_ = '110'b) n = n_110 ;
  when (_type_ = '100'b) n = n_100 ;
  when (_type_ = '010'b) n = n_010 ;
  when (_type_ = '001'b) n = n_001 ;
  when (_type_ = '000'b) n = n_000 ;
  otherwise n = . ;
 end ;
 of_all_abc = n / n_000 ;
 of_all_ab = n / n_001 ;
 of_all_ac = n / n_010 ;
 of_all_bc = n / n_100 ;
 of_all_a = n / n_011 ;
 of_all_b = n / n_101 ;
 of_all_c = n / n_110 ;
 of_all = n / n_000 ;
  run ;
proc sort data=testprops ;
 by level a b c ;
 run ;
proc print data=testprops ;
 where level = 3 ;
 run ;
proc print data=testprops ;
 run ;

******************************** ;
 proc summary data=testdata ;
   * where c ne 'c' and f > 0.1 ;
   class a b d ;
   var e ;
   weight f ;
   output out=test_out n=n p25=p25_cole mean=mean_cole stderr=stderr_cole;
   run;
data test_out ;
 set test_out ;
 if _type_ = '000'b then level = 0 ;
 if _type_ = '100'b or _type_ = '010'b or _type_ = '001'b  then level = 1 ;
 if _type_ = '110'b or _type_ = '101'b or _type_ = '011'b then level = 2 ;
 if _type_ = '111'b then level = 3 ;
 if a = ' ' then a = 'z' ;
 if b = ' ' then b = 'z' ;
 if c = ' ' then c = 'z' ;
 if d = ' ' then d = 'z' ;
run ;
proc sort data=test_out ;
 by level a b d ;
 run ;
title 'Unfiltered, weighted' ;
proc print data=test_out ;
 run ;

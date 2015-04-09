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

options pageno=1 ;
%macro misc(exclnpwgts,vdef,wvdef) ;

data a ;
 x = . ;
 wgt = . ;
 output ;
 run ;

proc summary data=a nway vardef=&vdef;
 var x ;
 output out=a_quantiles n=n nmiss=nmiss
                           sum=sum mean=mean min=min max=max sumwgt=sumwgt
                           stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                   skew=skew kurt=kurt t=t probt=probt ;
 run ;

proc summary data=a nway alpha=0.05 vardef=&wvdef
%if &exclnpwgts = 1 %then exclnpwgts ; ;
 var x ;
 weight wgt ;
 output out=a_quantiles_wgted n=n nmiss=nmiss sum=sum mean=mean min=min max=max sumwgt=sumwgt
                            stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                        skew=skew kurt=kurt t=t probt=probt ;
 run ;

data quantiles_a ;
 set a_quantiles
     a_quantiles_wgted(in=w) ;
 if w then wgted = 1 ;
  else wgted = 0 ;
 exclnpwgts = &exclnpwgts ;
 vardef = "&vdef" ;
 wvardef = "&wvdef" ;
 run ;

title "[]" ;
proc print data=quantiles_a ;
 format var 20.10 stderr 20.10 cv 20.10 lclm 20.10 uclm 20.10 t 20.10 skew 20.10 kurt 20.10 probt 20.10 ;
 run ;

data b ;
 x = 1 ;
 wgt = x ;
 output ;
 x = 2 ;
 wgt = x ;
 output ;
 x = 3 ;
 wgt = x ;
 output ;
 x = 3 ;
 wgt = x ;
 output ;
 x = 5 ;
 wgt = x ;
 output ;
 run ;

proc summary data=b nway vardef=&vdef;
 var x ;
 output out=b_quantiles n=n nmiss=nmiss
                           sum=sum mean=mean min=min max=max sumwgt=sumwgt
                           stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                   skew=skew kurt=kurt t=t probt=probt ;
 run ;

proc summary data=b nway alpha=0.05 vardef=&wvdef
%if &exclnpwgts = 1 %then exclnpwgts ; ;
 var x ;
 weight wgt ;
 output out=b_quantiles_wgted n=n nmiss=nmiss sum=sum mean=mean min=min max=max sumwgt=sumwgt
                            stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                        skew=skew kurt=kurt t=t probt=probt ;
 run ;

data quantiles_b ;
 set b_quantiles
     b_quantiles_wgted(in=w) ;
 if w then wgted = 1 ;
  else wgted = 0 ;
 exclnpwgts = &exclnpwgts ;
 vardef = "&vdef" ;
 wvardef = "&wvdef" ;
 run ;

title "[1,2,3,3,5]" ;
proc print data=quantiles_b ;
 format var 20.10 stderr 20.10 cv 20.10 lclm 20.10 uclm 20.10 t 20.10 skew 20.10 kurt 20.10 probt 20.10 ;
 run ;

data c ;
 x = . ;
 wgt = x ;
 output ;
 x = 2 ;
 wgt = x ;
 output ;
 x = . ;
 wgt = x ;
 output ;
 x = 5 ;
 wgt = x ;
 output ;
 x = . ;
 wgt = x ;
 output ;
 run ;

proc summary data=c nway vardef=&vdef;
 var x ;
 output out=c_quantiles n=n nmiss=nmiss
                           sum=sum mean=mean min=min max=max sumwgt=sumwgt
                           stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                   skew=skew kurt=kurt t=t probt=probt ;
 run ;

proc summary data=c nway alpha=0.05 vardef=&wvdef
%if &exclnpwgts = 1 %then exclnpwgts ; ;
 var x ;
 weight wgt ;
 output out=c_quantiles_wgted n=n nmiss=nmiss sum=sum mean=mean min=min max=max sumwgt=sumwgt
                            stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                        skew=skew kurt=kurt t=t probt=probt ;
 run ;

data quantiles_c ;
 set c_quantiles
     c_quantiles_wgted(in=w) ;
 if w then wgted = 1 ;
  else wgted = 0 ;
 exclnpwgts = &exclnpwgts ;
 vardef = "&vdef" ;
 wvardef = "&wvdef" ;
 run ;

title "[.,2,.,5,.]" ;
proc print data=quantiles_c ;
 format var 20.10 stderr 20.10 cv 20.10 lclm 20.10 uclm 20.10 t 20.10 skew 20.10 kurt 20.10 probt 20.10 ;
 run ;

data d ;
 x = 2 ;
 wgt = x ;
 output ;
 x = 5 ;
 wgt = x ;
 output ;
 run ;

proc summary data=d nway vardef=&vdef;
 var x ;
 output out=d_quantiles n=n nmiss=nmiss
                           sum=sum mean=mean min=min max=max sumwgt=sumwgt
                           stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                   skew=skew kurt=kurt t=t probt=probt ;
 run ;

proc summary data=d nway alpha=0.05 vardef=&wvdef
%if &exclnpwgts = 1 %then exclnpwgts ; ;
 var x ;
 weight wgt ;
 output out=d_quantiles_wgted n=n nmiss=nmiss sum=sum mean=mean min=min max=max sumwgt=sumwgt
                            stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                        skew=skew kurt=kurt t=t probt=probt ;
 run ;

data quantiles_d ;
 set d_quantiles
     d_quantiles_wgted(in=w) ;
 if w then wgted = 1 ;
  else wgted = 0 ;
 exclnpwgts = &exclnpwgts ;
 vardef = "&vdef" ;
 wvardef = "&wvdef" ;
 run ;

title "[2,5]" ;
proc print data=quantiles_d ;
 format var 20.10 stderr 20.10 cv 20.10 lclm 20.10 uclm 20.10 t 20.10 skew 20.10 kurt 20.10 probt 20.10 ;
 run ;

data e ;
 x = 2 ;
 wgt = x ;
 output ;
 run ;

proc summary data=e nway vardef=&vdef;
 var x ;
 output out=e_quantiles n=n nmiss=nmiss
                           sum=sum mean=mean min=min max=max sumwgt=sumwgt
                           stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                   skew=skew kurt=kurt t=t probt=probt ;
 run ;

proc summary data=e nway alpha=0.05 vardef=&wvdef
%if &exclnpwgts = 1 %then exclnpwgts ; ;
 var x ;
 weight wgt ;
 output out=e_quantiles_wgted n=n nmiss=nmiss sum=sum mean=mean min=min max=max sumwgt=sumwgt
                            stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                        skew=skew kurt=kurt t=t probt=probt ;
 run ;

data quantiles_e ;
 set e_quantiles
     e_quantiles_wgted(in=w) ;
 if w then wgted = 1 ;
  else wgted = 0 ;
 exclnpwgts = &exclnpwgts ;
 vardef = "&vdef" ;
 wvardef = "&wvdef" ;
 run ;

title "[2]" ;
proc print data=quantiles_e ;
 format var 20.10 stderr 20.10 cv 20.10 lclm 20.10 uclm 20.10 t 20.10 skew 20.10 kurt 20.10 probt 20.10 ;
 run ;

data f ;
 x = -2 ;
 wgt = x ;
 output ;
 run ;

proc summary data=f nway vardef=&vdef;
 var x ;
 output out=f_quantiles n=n nmiss=nmiss
                           sum=sum mean=mean min=min max=max sumwgt=sumwgt
                           stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                   skew=skew kurt=kurt t=t probt=probt ;
 run ;

proc summary data=f nway alpha=0.05 vardef=&wvdef
%if &exclnpwgts = 1 %then exclnpwgts ; ;
 var x ;
 weight wgt ;
 output out=f_quantiles_wgted n=n nmiss=nmiss sum=sum mean=mean min=min max=max sumwgt=sumwgt
                            stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                        skew=skew kurt=kurt t=t probt=probt ;
 run ;

data quantiles_f ;
 set f_quantiles
     f_quantiles_wgted(in=w) ;
 if w then wgted = 1 ;
  else wgted = 0 ;
 exclnpwgts = &exclnpwgts ;
 vardef = "&vdef" ;
 wvardef = "&wvdef" ;
 run ;

title "[-2]" ;
proc print data=quantiles_f ;
 format var 20.10 stderr 20.10 cv 20.10 lclm 20.10 uclm 20.10 t 20.10 skew 20.10 kurt 20.10 probt 20.10 ;
 run ;


data g ;
 x = -3 ;
 wgt = x ;
 output ;
 x = -4 ;
 wgt = x ;
 output ;
 x = -5 ;
 wgt = x ;
 output ;
 x = -2 ;
 wgt = x ;
 output ;
 x = -76 ;
 wgt = x ;
 output ;
 run ;

proc summary data=g nway vardef=&vdef;
 var x ;
 output out=g_quantiles n=n nmiss=nmiss
                           sum=sum mean=mean min=min max=max sumwgt=sumwgt
                           stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                   skew=skew kurt=kurt t=t probt=probt ;
 run ;

proc summary data=g nway alpha=0.05 vardef=&wvdef
%if &exclnpwgts = 1 %then exclnpwgts ; ;
 var x ;
 weight wgt ;
 output out=g_quantiles_wgted n=n nmiss=nmiss sum=sum mean=mean min=min max=max sumwgt=sumwgt
                            stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                        skew=skew kurt=kurt t=t probt=probt ;
 run ;

data quantiles_g ;
 set g_quantiles
     g_quantiles_wgted(in=w) ;
 if w then wgted = 1 ;
  else wgted = 0 ;
 exclnpwgts = &exclnpwgts ;
 vardef = "&vdef" ;
 wvardef = "&wvdef" ;
 run ;

title "[-3,-4,-5,-2,-76]" ;
proc print data=quantiles_g ;
 format var 20.10 stderr 20.10 cv 20.10 lclm 20.10 uclm 20.10 t 20.10 skew 20.10 kurt 20.10 probt 20.10 ;
 run ;

%mend ;

%misc(0,DF,WDF)
%misc(1,DF,WDF)
%misc(0,N,WEIGHT)
%misc(1,N,WEIGHT)

********************************************************************************************* ;
options pageno=1 ;
%macro pc(n,miss_x,miss_wgt,exclnpwgts,vdef,wvdef) ;

data a(drop=y) ;
 do y = &n to -10 by -1 ;
  x = y ;
  wgt = x / 3 ;
%if &miss_x = 1 %then %do ;
  if mod(x,7) = 0 and x < 500 then x = . ;
%end ;
%if &miss_wgt = 1 %then %do ;
  if mod(x,13) = 0 and x > 500 then wgt = . ;
%end ;
  output ;
end ;
run ;

%do def = 1 %to 5 ;

proc summary data=a nway pctldef=&def vardef=&vdef;
 var x ;
 output out=quantiles_&def n=n nmiss=nmiss
                           sum=sum mean=mean min=min max=max sumwgt=sumwgt
                           stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                   skew=skew kurt=kurt t=t probt=probt
                           median=median p1=p1 p10=p10 p25=p25 p75=p75 p90=p90 p99=p99 ;
 run ;
%end ;

proc summary data=a nway alpha=0.05 vardef=&wvdef
%if &exclnpwgts = 1 %then exclnpwgts ; ;
 var x ;
 weight wgt ;
 output out=quantiles_wgted n=n nmiss=nmiss sum=sum mean=mean min=min max=max sumwgt=sumwgt
                            stderr=stderr stddev=stddev cv=cv lclm=lclm uclm=uclm var=var
                                                        skew=skew kurt=kurt t=t probt=probt
                            median=median p1=p1 p10=p10 p25=p25 p75=p75 p90=p90 p99=p99 ;
 run ;

data quantiles ;
 set quantiles_1(in=a)
     quantiles_2(in=b)
     quantiles_3(in=c)
     quantiles_4(in=d)
     quantiles_5(in=e)
     quantiles_wgted(in=w) ;
 select ;
  when (a) def = 1 ;
  when (b) def = 2 ;
  when (c) def = 3 ;
  when (d) def = 4 ;
  when (e) def = 5 ;
  otherwise ;
 end ;
 if w then wgted = 1 ;
  else wgted = 0 ;
 negten_to_ = &n ;
 missing_x = &miss_x ;
 missing_wgt = &miss_wgt ;
 exclnpwgts = &exclnpwgts ;
 vardef = "&vdef" ;
 wvardef = "&wvdef" ;
 run ;

proc print data=quantiles ;
 format var 20.10 stderr 20.10 cv 20.10 lclm 20.10 uclm 20.10 t 20.10 skew 20.10 kurt 20.10 probt 20.10 ;
 run ;
%mend ;

%pc(990,0,0,0,DF,WDF)
%pc(995,0,0,0,DF,WDF)
%pc(990,1,0,0,DF,WDF)
%pc(995,1,0,0,DF,WDF)
%pc(990,0,1,0,DF,WDF)
%pc(995,0,1,0,DF,WDF)
%pc(990,1,1,0,DF,WDF)
%pc(995,1,1,0,DF,WDF)

%pc(990,0,0,1,DF,WDF)
%pc(995,0,0,1,DF,WDF)
%pc(990,1,0,1,DF,WDF)
%pc(995,1,0,1,DF,WDF)
%pc(990,0,1,1,DF,WDF)
%pc(995,0,1,1,DF,WDF)
%pc(990,1,1,1,DF,WDF)
%pc(995,1,1,1,DF,WDF)

%pc(990,0,0,0,N,WEIGHT)
%pc(995,0,0,0,N,WEIGHT)
%pc(990,1,0,0,N,WEIGHT)
%pc(995,1,0,0,N,WEIGHT)
%pc(990,0,1,0,N,WEIGHT)
%pc(995,0,1,0,N,WEIGHT)
%pc(990,1,1,0,N,WEIGHT)
%pc(995,1,1,0,N,WEIGHT)

%pc(990,0,0,1,N,WEIGHT)
%pc(995,0,0,1,N,WEIGHT)
%pc(990,1,0,1,N,WEIGHT)
%pc(995,1,0,1,N,WEIGHT)
%pc(990,0,1,1,N,WEIGHT)
%pc(995,0,1,1,N,WEIGHT)
%pc(990,1,1,1,N,WEIGHT)
%pc(995,1,1,1,N,WEIGHT)

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

/* indirect_std_check.sas
   Written by Tim Churches, November 2005. Checks NetEpi Analysis indirect standardisation
   results.
*/

/* Adjust the paths below to point to the CSV files of synthetic death and population data
   left behind in the /demo/scratch subdirectory of the unpacked NetEpi-Analysis distribution
   after running the SOOM_demo_data_load.py program with either no options or with the
   --datasets="syndeath" option. Note that you need to decompress (gunzip) the files
   left by the NetEpi program in the /demo/scratch directory first, because SAS does not
   know how to read gzipped files (without using a pipe through an external program). */

%let path = C:\USERDATA\;

filename syndths "&path.synthetic_deaths.csv" ;
filename synpopns "&path.synthetic_pops.csv" ;

 /**********************************************************************
 *   PRODUCT:   SAS
 *   VERSION:   8.2
 *   CREATOR:   External File Interface
 *   DATE:      17NOV05
 *   DESC:      Generated SAS Datastep Code
 *   TEMPLATE SOURCE:  (None Specified.)
 ***********************************************************************/
    data WORK.syndeaths                              ;
   %let _EFIERR_ = 0; /* set the ERROR detection macro variable */
    infile  syndths delimiter = ',' MISSOVER DSD lrecl=32767 firstobs=2 ;
       informat agegrp best32. ;
       informat sex best32. ;
       informat region best32. ;
       informat year best32. ;
       informat causeofdeath best32. ;
       format agegrp best12. ;
       format sex best12. ;
       format region best12. ;
       format year best12. ;
       format causeofdeath best12. ;
    input
                agegrp
                sex
                region
                year
                causeofdeath
    ;
    if _ERROR_ then call symput('_EFIERR_',1);  /* set ERROR detection macro variable */
    run;

/**********************************************************************
 *   PRODUCT:   SAS
 *   VERSION:   8.2
 *   CREATOR:   External File Interface
 *   DATE:      17NOV05
 *   DESC:      Generated SAS Datastep Code
 *   TEMPLATE SOURCE:  (None Specified.)
 ***********************************************************************/
    data WORK.synpops                                ;
   %let _EFIERR_ = 0; /* set the ERROR detection macro variable */
    infile synpopns delimiter = ',' MISSOVER DSD lrecl=32767 firstobs=2 ;
       informat agegrp best32. ;
       informat sex best32. ;
       informat region best32. ;
       informat year best32. ;
       informat pop best32. ;
       format agegrp best12. ;
       format sex best12. ;
       format region best12. ;
       format year best12. ;
       format pop best12. ;
    input
                agegrp
                sex
                region
                year
                pop
    ;
    if _ERROR_ then call symput('_EFIERR_',1);  /* set ERROR detection macro variable */
    run;

%macro smrcalc(stdcod,targcod,conflev) ;

** Step 1a: Get the number of events in the Standard numerator dataset by age & sex ** ;
data events1 ;
set syndeaths ;
where causeofdeath = &stdcod ;
run ;

proc summary data=events1 nway ;
var year ;
class agegrp sex ;
output out=st_evnts n=st_evnti ;
run ;

** Step 1b: Get the number of events in the Target numerator dataset ** ;
data events2 ;
set syndeaths ;
where causeofdeath = &targcod ;
run ;

** Step 2: Get the Standard Population by age and sex ** ;
data st_pops ;
set synpops ;
run ;

proc summary data=st_pops nway ;
class agegrp sex ;
var pop ;
output out=st_pops sum=pop ;
run ;

** Step 3: Calculate the Standard age&sex-specific rates ** ;
proc sql ;
create table st_rate as
select * from st_pops as a left outer join st_evnts as b
on a.agegrp=b.agegrp and a.sex=b.sex ;

data st_rate ;
set st_rate ;
if st_ratei=. then st_ratei=0 ;
if st_evnti > 0 then st_ratei = (st_evnti/pop) ;
else st_ratei = 0 ;
run ;

** Step 4: Get the Target Population Totals** ;
data sp_pops ;
set synpops ;
run ;

proc summary data=sp_pops nway ;
class agegrp sex region ;
var pop ;
output out=sp_pops sum=sp_popi ;
run ;

** Step 5: Calculate the Target Population Expected Number of Events (Deaths) by Age&Sex ** ;
proc sql ;
create table sp_expi as
select * from st_rate as a right join sp_pops as b
on a.agegrp=b.agegrp and a.sex=b.sex ;

data sp_expi ;
set sp_expi ;
sp_expi=st_ratei*sp_popi ;
run ;

proc summary data=sp_expi nway ;
var sp_expi ;
class region sex ;
output out=sp_exp sum=sp_exp ;
run ;

** Step 6: Get the Target Population Observed events ** ;
proc summary data=events2 nway ;
var year ;
class region sex ;
output out=sp_evnts n=sp_evnt ;
run ;

** Step 7: Calculate the Indirectly Standardised Mortality Ratio (SMR) and Confidence Intervals** ;
proc sql ;
create table smr as
select * from sp_exp as a left outer join sp_evnts as b
on a.region=b.region and a.sex=b.sex ;

data smr ;
set smr ;
attrib smr label="Std Mortality Ratio"
l99 label="SMR lower CL"
u99 label="SMR upper CL"
p label="SMR p value"
sp_exp label="Expected" ;
if sp_evnt = . then sp_evnt = 0 ;
smr=(sp_evnt/sp_exp)*100 ;

* Calculate a p-value. ;
select ;
when (sp_evnt=0) do ;
p_u = poisson(sp_exp,sp_evnt) ;
p_l = poisson(sp_exp,sp_evnt) ;
p = p_u + p_l ;
end ;
when (sp_evnt ge sp_exp) do ;
p_u = 1 - poisson(sp_exp,(sp_evnt-1)) ;
p_l = poisson(sp_exp,round(sp_exp*(sp_exp/sp_evnt))) ;
p = p_u + p_l ;
end ;
when (sp_evnt lt sp_exp) do ;
if (sp_exp + (sp_exp-sp_evnt)) = int(sp_exp+(sp_exp-sp_evnt)) then
p_u = 1 - poisson(sp_exp,(int(sp_exp+(sp_exp-sp_evnt))-1)) ;
else
p_u = 1 - poisson(sp_exp,(int(sp_exp*(sp_exp/sp_evnt)))) ;
p_l = poisson(sp_exp,sp_evnt) ;
p = p_u + p_l ;
end ;
otherwise ;
end ;
if p > 1 then p = 1 ;
* Calculate Confidence Intervals ;
if sp_evnt = 0 then do ;
l99 = 0 ;
u_lam99 = -log(1 - &conflev) ;
if u_lam99 ne . then u99 = u_lam99/sp_exp ;
else l99 = . ;
end ;
else do ;
l_lam99 = gaminv((1 - &conflev)/2,sp_evnt) ;
if sp_exp > 0 then l99 = l_lam99/sp_exp ;
else l99 = . ;
u_lam99 = gaminv((1 + &conflev)/2,sp_evnt+1) ;
if u_lam99 ne . then u99 = u_lam99/sp_exp ;
else l99 = . ;
end ;
if l99 ne . then l99 = 100*l99 ;
if u99 ne . then u99 = 100*u99 ;
run ;

filename smr_out "&path.smr_results_&stdcod._&targcod._CL&conflev..csv" ;

title "Std causeofdeath=&stdcod., target causeofdeath=&targcod., conf. level=&conflev." ;
proc print data=smr label noobs ;
 var region sex sp_evnt sp_exp smr l99 u99 p ;
 run ;

/**********************************************************************
*   PRODUCT:   SAS
*   VERSION:   8.2
*   CREATOR:   External File Interface
*   DATE:      17NOV05
*   DESC:      Generated SAS Datastep Code
*   TEMPLATE SOURCE:  (None Specified.)
***********************************************************************/
   data _null_;
   set  WORK.SMR                                     end=EFIEOD;
   %let _EFIERR_ = 0; /* set the ERROR detection macro variable */
   %let _EFIREC_ = 0;     /* clear export record count macro variable */
   file smr_out delimiter=',' DSD DROPOVER lrecl=32767;
      format region best12. ;
      format sex best12. ;
      format _TYPE_ best12. ;
      format _FREQ_ best12. ;
      format sp_evnt best12. ;
      format sp_exp best12. ;
      format smr best12. ;
      format l99 best12. ;
      format u99 best12. ;
      format p best12. ;
      format p_u best12. ;
      format p_l best12. ;
      format u_lam99 best12. ;
      format l_lam99 best12. ;
   if _n_ = 1 then        /* write column names */
    do;
      put
      'region'
      ','
      'sex'
      ','
      '_TYPE_'
      ','
      '_FREQ_'
      ','
      'sp_evnt'
      ','
      'sp_exp'
      ','
      'smr'
      ','
      'l99'
      ','
      'u99'
      ','
      'p'
      ','
      'p_u'
      ','
      'p_l'
      ','
      'u_lam99'
      ','
      'l_lam99'
      ;
    end;
    do;
      EFIOUT + 1;
      put region @;
      put sex @;
      put _TYPE_ @;
      put _FREQ_ @;
      put sp_evnt @;
      put sp_exp @;
      put smr @;
      put l99 @;
      put u99 @;
      put p @;
      put p_u @;
      put p_l @;
      put u_lam99 @;
      put l_lam99 ;
      ;
    end;
   if _ERROR_ then call symput('_EFIERR_',1);  /* set ERROR detection macro variable */
   If EFIEOD then
      call symput('_EFIREC_',EFIOUT);
   run;

filename smr_out ;

%mend ;

%smrcalc(37,37,0.99) ;
%smrcalc(37,37,0.90) ;

%smrcalc(95,95,0.99) ;
%smrcalc(95,95,0.90) ;

%smrcalc(37,95,0.99) ;
%smrcalc(37,95,0.90) ;

%smrcalc(95,37,0.99) ;
%smrcalc(95,37,0.90) ;

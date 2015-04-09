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

data counts ;
input count sex $ agegrp ;
cards ;
685 1 1
657 2 1
66 1 2
34 2 2
58 1 3
42 2 3
98 1 4
193 2 4
108 1 5
384 2 5
109 1 6
454 2 6
154 1 7
436 2 7
213 1 8
396 2 8
223 1 9
262 2 9
283 1 10
274 2 10
280 1 11
273 2 11
270 1 12
232 2 12
314 1 13
282 2 13
378 1 14
352 2 14
420 1 15
395 2 15
325 1 16
386 2 16
195 1 17
297 2 17
147 1 18
325 2 18
;
run ;

data popn ;
input pop sex $ agegrp ;
cards ;
10145000 1 1
9680000 2 1
10413000 1 2
9932000 2 2
10031000 1 3
9548000 2 3
10011000 1 4
9472000 2 4
9000000 1 5
8772000 2 5
9596000 1 6
9661000 2 6
10416000 1 7
10495000 2 7
11316000 1 8
11410000 2 8
10657000 1 9
10837000 2 9
9138000 1 10
9443000 2 10
7346000 1 11
7716000 2 11
5614000 1 12
6050000 2 12
4712000 1 13
5246000 2 13
4432000 1 14
5235000 2 14
3786000 1 15
4871000 2 15
2903000 1 16
4101000 2 16
1708000 1 17
2896000 2 17
1097000 1 18
2686000 2 18
;
run ;

data stdpop ;
input pop sex $ agegrp ;
cards ;
88600 1 1
88600 2 1
86900 1 2
86900 2 2
86000 1 3
86000 2 3
84700 1 4
84700 2 4
82200 1 5
82200 2 5
79300 1 6
79300 2 6
76100 1 7
76100 2 7
71500 1 8
71500 2 8
65900 1 9
65900 2 9
60400 1 10
60400 2 10
53700 1 11
53700 2 11
45500 1 12
45500 2 12
37200 1 13
37200 2 13
29600 1 14
29600 2 14
22100 1 15
22100 2 15
15200 1 16
15200 2 16
 9100 1 17
 9100 2 17
 6000 1 18
 6000 2 18
 ;
 run ;

proc print data=counts ;
 run ;

proc print data=popn ;
  run ;

proc print data=stdpop ;
  run ;

%dstand(stdpop = %str(stdpop),
        spevents = %str(counts),
		sppop = %str(popn),
		countvar = %str(count),
		agegrps = 1 to 18,
		basepop = 100000,
		outds = sumevnt1
		) ;
proc print data=sumevnt1 ;
 run ;


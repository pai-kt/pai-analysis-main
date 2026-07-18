libname tmt_w20 "G:\????Ʈ??????\?ڳ󰡽???Ʈ???ڷ?\24?? ???? ??????Ʈ ?۾?\?丶??\????\SASDB";


%macro aa(a,b,c,d); 
PROC IMPORT OUT= W_&a._&b.
            DATAFILE= "G:\????Ʈ??????\?ڳ󰡽???Ʈ???ڷ?\24?? ???? ??????Ʈ ?۾?\?丶??\????\??����????\22??_?ϼ??丶??_&c._&d..xlsx" 
            DBMS=EXCEL REPLACE;
     GETNAMES=YES;
     MIXED=NO;
     SCANTEXT=YES;
     USEDATE=YES;
     SCANTIME=YES;
RUN;
%mend; 
%aa(gn,221019, ?泲, ??????); %aa(gn,221020, ?泲, ?輺??); %aa(gn,221021, ?泲, ?迬??); %aa(gn,221022, ?泲, ?迬??); %aa(gn,221023, ?泲, ?迵??);
%aa(gn,221025, ?泲, ??????); %aa(gn,221026, ?泲, ��????); %aa(gn,221027, ?泲, ��??ȣ); %aa(gn,221028, ?泲, ��????); %aa(gn,221029, ?泲, ��ĥ??);  %aa(gn,221030, ?泲, ??????);
%aa(jn,221008, ????, ?輱ȯ); %aa(jn,221009, ????, ?輺??);%aa(jn,221010, ????, ?ڹ?ȭ);  %aa(jn,221011, ????, ��??ȯ); %aa(jn,221012, ????, ?̸???); 
%aa(jn,221013, ????, ?̺???); %aa(jn,221014, ????, ??????);  %aa(jn,221017, ????, ?־???);    



/*999??��
%macro bb(a,b); 
data w_&a._&b.; 
set w_&a._&b.; 
if d_g_ec=-999 then d_g_ec=.; 
if d_g_ph=-999 then  d_g_ph=.; 
if d_num=-999 then d_num=.; 
if p_water=-999 then p_water=.;
if p_water_day=-999 then p_water_day=.;
if date=. then delete; 
run;  
%mend;
%bb(gn,191041); %bb(gn,191042); %bb(gn,191043); %bb(gn,191044); %bb(gn,191045);
%bb(gn,191046); %bb(gn,191047); %bb(gn,191049); %bb(gn,191050); %bb(gn,191051);

%bb(jn,191027); %bb(jn,191028); %bb(jn,191029); %bb(jn,191032); %bb(jn,191033); 
%bb(jn,191034); %bb(jn,191035); %bb(jn,191036); %bb(jn,191037); %bb(jn,191038); %bb(jn,191039);  

%bb(jb,191013); %bb(jb,191014); %bb(jb,191015); %bb(jb,191016); %bb(jb,191017); 
%bb(jb,191018); %bb(jb,191019); %bb(jb,191021); %bb(jb,191024); %bb(jb,191025); 


%bb(gn,201039); %bb(gn,201040); %bb(gn,201041); %bb(gn,201042); %bb(gn,201043); 
%bb(gn,201044); %bb(gn,201045); %bb(gn,201046); %bb(gn,201047); %bb(gn,201048); %bb(gn,201049); 

%bb(jn,201027); %bb(jn,201028); %bb(jn,201029); %bb(jn,201031);  %bb(jn,201032); %bb(jn,201033); %bb(jn,201034); %bb(jn,201037);       

%bb(jb,201014); %bb(jb,201015); %bb(jb,201016); %bb(jb,201017); %bb(jb,201018); %bb(jb,201019); 
%bb(jb,201020); %bb(jb,201022); %bb(jb,201023); %bb(jb,201024); %bb(jb,201025); %bb(jb,201026); 


%bb(gn,211014); %bb(gn,211015); %bb(gn,211016); %bb(gn,211017); %bb(gn,211018); %bb(gn,211019); %bb(gn,211020); %bb(gn,211021); 

%bb(jn,211023); %bb(jn,211024); %bb(jn,211025); %bb(jn,211029); %bb(jn,211030); %bb(jn,211031);         





/*EC 1?̸?, 4?̻? ????ó??, ph?? 5????, 8?̻? ????*/
/*????Ƚ?? 50?ʰ? ????, p_water_day 200?̸? 3200?ʰ? ????*/
%macro dd(a,b); 
data w_&a._&b.; 
set w_&a._&b.; 
if d_g_ec>=4 or d_g_ec<1 then d_g_ec=.; 
if d_g_ph<=5 or d_g_ph>=8 then  d_g_ph=.; 
if d_num>50 then p_water=.;
if d_num>50 then p_water_day=.;
if d_num>50 then d_num=.;
if p_water_day <200 then d_num=.;
if p_water_day <200 then p_water=.;
if p_water_day <200 then p_water_day=.;
if p_water_day >3200 then d_num=.;
if p_water_day >3200 then p_water=.;
if p_water_day >3200 then p_water_day=.;
run;  
%mend;
%dd(gn,221019); %dd(gn,221020); %dd(gn,221021); %dd(gn,221022); %dd(gn,221023);
%dd(gn,221025); %dd(gn,221026); %dd(gn,221027); %dd(gn,221028); %dd(gn,221029);  %dd(gn,221030);
%dd(jn,221008); %dd(jn,221009); %dd(jn,221010); %dd(jn,221011); %dd(jn,221012); %dd(jn,221013); %dd(jn,221014); %dd(jn,221017);    


/*id?ο?*/
%macro ee(a,b); 
data w_&a._&b.; 
set w_&a._&b.; 
id=&b.;
run;  
%mend;
%ee(gn,221019); %ee(gn,221020); %ee(gn,221021); %ee(gn,221022); %ee(gn,221023);
%ee(gn,221025); %ee(gn,221026); %ee(gn,221027); %ee(gn,221028); %ee(gn,221029);  %ee(gn,221030);
%ee(jn,221008); %ee(jn,221009); %ee(jn,221010); %ee(jn,221011); %ee(jn,221012); %ee(jn,221013); %ee(jn,221014); %ee(jn,221017);    


%macro ff(a,b); 
data w_&a._&b.; 
set w_&a._&b.; 
keep date d_g_ec d_g_ph d_num p_water_day p_water id;
run;  
%mend;
%ff(gn,221019); %ff(gn,221020); %ff(gn,221021); %ff(gn,221022); %ff(gn,221023);
%ff(gn,221025); %ff(gn,221026); %ff(gn,221027); %ff(gn,221028); %ff(gn,221029); %ff(gn,221030);
%ff(jn,221008);%ff(jn,221009);%ff(jn,221010); %ff(jn,221011); %ff(jn,221012); %ff(jn,221013); %ff(jn,221014); %ff(jn,221017);    


/*?????? ?? ???̱?*/
data tmt_w; set w_gn_221019 w_gn_221020 w_gn_221021 w_gn_221022 w_gn_221023 w_gn_221025 w_gn_221026 w_gn_221027 w_gn_221028 w_gn_221029 w_gn_221030
                         w_jn_221008 w_jn_221009 w_jn_221010 w_jn_221011 w_jn_221012 w_jn_221013 w_jn_221014 w_jn_221017 ;
run;



/*��???Ͽ? ???? ?ڸ???*/
PROC IMPORT OUT=start
            DATAFILE= "G:\????Ʈ??????\?ڳ󰡽???Ʈ???ڷ?\24?? ???? ??????Ʈ ?۾?\?丶??\��????(start).xlsx" 
            DBMS=xlsx REPLACE;
     GETNAMES=YES; 
RUN;

/*��???? */
proc sort data=tmt_w; by id ;run;
proc sort data=start ; by id ;run;
data tmt_w; merge tmt_w start; by id; run;

data tmt_w; set tmt_w;
if date=. then delete; run;

data tmt_w; set tmt_w;
INFORMAT start yymmdd10.;
FORMAT  start yymmdd10.;
 run;

  /*��???? ??¥ ???缭 ???µ????ͼ?*/ 
data tmt_w; set tmt_w;
if date<start then delete; 
if date>end then delete; run; 


/*?׷??��? ?̻?ġ Ȯ??*/ 

ods pdf file='G:\????Ʈ??????\?ڳ󰡽???Ʈ???ڷ?\24?? ???? ??????Ʈ ?۾?\?丶??\????\?丶??_????_??????_ec_ph_3??Ȯ??.pdf'; 

symbol1 interpol=join; 

proc gplot data=tmt_w; 
by id;
plot d_g_ec*date; 
plot d_g_ph*date; 
run; 

ods pdf close; 



ods pdf file='G:\????Ʈ??????\?ڳ󰡽???Ʈ???ڷ?\24?? ???? ??????Ʈ ?۾?\?丶??\????\?丶??_????_??????_????_3??Ȯ??.pdf'; 
symbol1 interpol=join; 

proc gplot data=tmt_w; 
by id;
plot p_water_day*date; 
plot p_water*date; 
plot d_num*date; 
run; 

ods pdf close; 



/***?????? ????***/
 data water_gw; set tmt_w;
year=year(date); month=month(date); day=day(date); run;


/***????????***/
data water_gw; set  water_gw; week=week(date,'u'); run;
data  water_gw; set water_gw; week2=week+1;  run;
data water_gw; set water_gw; if week2=53 then week3=1; else week3=week2;  run;   

data water_gw_2; set water_gw; /*???????߰?*/
if week2=53 and week3=1 then year=year+1; 
else year=year; 
run; 

data water_gw_2; set water_gw_2; drop week week2;  rename week3=week; run;



/*******************?????? ??????****************************/
proc sort data=water_gw_2; by  id year week ; run;  
proc means data=water_gw_2  noprint; by id year week;
output out=water_gw_week mean(d_g_ec)=d_g_ec  mean(d_g_ph)=d_g_ph mean(d_num)=d_num mean(p_water_day)=p_water_day; 
run;



***********************???????? ?۾??Ϸ?**************;


/*???? month ???ϱ?*/
data water_gw_week1; set water_gw_week;
if year=2019 and 1<=week<=5 then month=1;
else if year=2019 and 6<=week<=9 then month=2;
else if year=2019 and 10<=week<=13 then month=3;
else if year=2019 and 14<=week<=17 then month=4;
else if year=2019 and 18<=week<=22 then month=5;
else if year=2019 and 23<=week<=26 then month=6;
else if year=2019 and 27<=week<=30 then month=7;
else if year=2019 and 31<=week<=35 then month=8;
else if year=2019 and 36<=week<=39 then month=9;
else if year=2019 and 40<=week<=44 then month=10;
else if year=2019 and 45<=week<=48 then month=11;
else if year=2019 and 49<=week<=53 then month=12;

if year=2020 and 1<=week<=5 then month=1;
else if year=2020 and 6<=week<=9 then month=2;
else if year=2020 and 10<=week<=13 then month=3;
else if year=2020 and 14<=week<=18 then month=4;
else if year=2020 and 19<=week<=22 then month=5;
else if year=2020 and 23<=week<=26 then month=6;
else if year=2020 and 27<=week<=31 then month=7;
else if year=2020 and 32<=week<=35 then month=8;
else if year=2020 and 36<=week<=39 then month=9;
else if year=2020 and 40<=week<=44 then month=10;
else if year=2020 and 45<=week<=48 then month=11;
else if year=2020 and 49<=week<=53 then month=12;

else if year=2021 and 1<=week<=4 then month=1;
else if year=2021 and 5<=week<=8 then month=2;
else if year=2021 and 9<=week<=12 then month=3;
else if year=2021 and 13<=week<=17 then month=4;
else if year=2021 and 18<=week<=21 then month=5;
else if year=2021 and 22<=week<=25 then month=6;
else if year=2021 and 26<=week<=30 then month=7;
else if year=2021 and 31<=week<=34 then month=8;
else if year=2021 and 35<=week<=39 then month=9;
else if year=2021 and 40<=week<=43 then month=10;
else if year=2021 and 44<=week<=47 then month=11;
else if year=2021 and 48<=week<=53 then month=12;

else if year=2022 and 1<=week<=4 then month=1;
else if year=2022 and 5<=week<=8 then month=2;
else if year=2022 and 9<=week<=13 then month=3;
else if year=2022 and 14<=week<=17 then month=4;
else if year=2022 and 18<=week<=21 then month=5;
else if year=2022 and 22<=week<=26 then month=6;
else if year=2022 and 27<=week<=30 then month=7;
else if year=2022 and 31<=week<=34 then month=8;
else if year=2022 and 35<=week<=39 then month=9;
else if year=2022 and 40<=week<=43 then month=10;
else if year=2022 and 44<=week<=47 then month=11;
else if year=2022 and 48<=week<=53 then month=12;
run;

data water_gw_week1_v; set water_gw_week1;
if id=201042 or id=201017 or id=211017 or id=191024 or id=201024 or id=191014 or id=201022 or id=201015 or id=191045 or id=191019 or id=191018 or id=201020 or id=191015/*???? ????*/
or id=191013 or id=191016 or id=191021 or id=191025 or  id=191028  or id=191029 or id=191032 or id=191033  or id=191036  
or id=191037 or id=191038 or id=191040 or id=191041 or  id=191042 or id=191043 or id=191044 or id=191046 or id=191047  or id=191049 or id=191050 or id=191051
or id=201014 or id=201016 or id=201018 or id=201019 or id=201023 or id=201025 or id=201026 or id=201029 or id=201030
or id=201031 or id=201032 or id=201035 or id=201036 or id=201038 or id=201039 or id=201040 or id=201041 or id=201043 or id=201044 or id=201045 or id=201046
or id=201047 or id=201048 or id=201049
or id=211012 or id=211013 or id=211014 or id=211015 or id=211016 or id=211018 or id=211019 or  id=211020 or id=211021 or id=211024 or  id=211025 or id=211029 or id=211030 /*???? ?Ϲ?*/
;
run;

data water_gw_week1_g; set water_gw_week1;
if id=191027 or id=201033   /*��?? ????*/
or id=191034 or id=191035 or id=191039 
or id=201027 or id=201028 or id=201034 or id=201037 
or id=211023 or id=211031   /*��?? ?Ϲ?*/
;
run;

data water_gw_week1_v; set water_gw_week1_v;
if id=201042 or id=201017 or id=211017 or id=191024 or id=201024 or id=191014 or id=201022 or id=201015 or id=191045 or id=191019 or id=191018 or id=201020 or id=191015  then group="????";
else if  id=191013 or id=191016 or id=191021 or id=191025 or  id=191028  or id=191029 or id=191032 or id=191033  or id=191036  
or id=191037 or id=191038 or id=191040 or id=191041 or  id=191042 or id=191043 or id=191044 or id=191046 or id=191047  or id=191049 or id=191050 or id=191051

or id=201014 or id=201016 or id=201018 or id=201019 or id=201023 or id=201025 or id=201026 or id=201029 or id=201030
or id=201031 or id=201032 or id=201035 or id=201036 or id=201038 or id=201039 or id=201040 or id=201041 or id=201043 or id=201044 or id=201045 or id=201046
or id=201047 or id=201048 or id=201049

or id=211012 or id=211013 or id=211014 or id=211015 or id=211016 or id=211018 or id=211019 or  id=211020 or id=211021 or id=211024 or  id=211025 or id=211029 or id=211030 then group="?Ϲ?"
;
run;

data water_gw_week1_g; set water_gw_week1_g;
if id=191027 or id=201033  then group="????";
else if id=191034 or id=191035 or id=191039 
or id=201027 or id=201028 or id=201034 or id=201037 
or id=211023 or id=211031  then group = "?Ϲ?"
;
run;


/*??��???? ????????*/
PROC export data= water_gw_week1_v
OUTFILE= "I:\?????г?????????\?ڳ󰡽???Ʈ???ڷ?\23?? ???? ??????Ʈ ?۾?\?丶??\SAS out\Water_gw_week1_v.xlsx"
            DBMS=xlsx REPLACE;
     sheet="sheet1"; 
RUN;

PROC export data= water_gw_week1_g
OUTFILE= "I:\?????г?????????\?ڳ󰡽???Ʈ???ڷ?\23?? ???? ??????Ʈ ?۾?\?丶??\SAS out\Water_gw_week1_g.xlsx"
            DBMS=xlsx REPLACE;
     sheet="sheet1"; 
RUN;

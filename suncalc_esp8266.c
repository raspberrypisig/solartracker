//#include <stdio.h>
//#include <math.h>
//#include <TimeLib.h>

#define SECS_PER_MIN ((time_t)(60UL))
#define SECS_PER_HOUR ((time_t)(3600UL))
#define SECS_PER_DAY  ((time_t)(SECS_PER_HOUR * 24UL))
#define SECS_YR_2000 ((time_t)(946684800UL)) // the time at the start of y2k
#define LEAP_YEAR(Y) ( ((1970+(Y))>0) && !((1970+(Y))%4) && ( ((1970+(Y))%100) || !((1970+(Y))%400) ) )
#define MELBOURNE_TIMEZONE 10
#define MELBOURNE_TIMEZONE_DST 11
#define DAYS_MS 86400000
//#define DAYS_MS_SMALL 86400.000f
#define J1970 2440588
#define J2000 2451545
#define PI 3.14159265359
#define RAD (PI/180.0)
#define DEG (180.0/PI)
#define E (RAD * 23.4397)

#if defined(__AVR__)
typedef long long int time_t;
#endif

int monthDays[]={31,28,31,30,31,30,31,31,30,31,30,31};


typedef struct  { 
  int Second; 
  int Minute; 
  int Hour; 
  int Wday;   // day of week, sunday is day 1
  int Day;
  int Month; 
  int Year;   // offset from 1970; 
} tmElements_t;

typedef struct {
  double azimuth;
  double altitude;
} sun_pos;

typedef struct {
  double ra;
  double dec;  
} ra_dec;


long long makeTime(tmElements_t tm)
{   
// assemble time elements into time_t 
// note year argument is offset from 1970 (see macros in time.h to convert to other formats)
// previous version used full four digit year (or digits since 2000),i.e. 2009 was 2009 or 9
  
  int i;
  int seconds;

  // seconds from 1970 till 1 jan 00:00:00 of the given year
  seconds= tm.Year*(SECS_PER_DAY * 365);
  for (i = 0; i < tm.Year; i++) {
    if (LEAP_YEAR(i)) {
      seconds +=  SECS_PER_DAY;   // add extra days for leap years
    }
  }
  
  // add days for this year, months start from 1
  for (i = 1; i < tm.Month; i++) {
    if ( (i == 2) && LEAP_YEAR(tm.Year)) { 
      seconds += SECS_PER_DAY * 29;
    } else {
      seconds += SECS_PER_DAY * monthDays[i-1];  //monthDay array starts from 0
    }
  }
  seconds+= (tm.Day-1) * SECS_PER_DAY;
  seconds+= tm.Hour * SECS_PER_HOUR;
  seconds+= tm.Minute * SECS_PER_MIN;
  seconds+= tm.Second;
  return seconds; 
}


bool isDst(tmElements_t t) {
  int month = t.Month;
  int year = t.Year - 30; // 2018 becomes 18
  int day = t.Day; 

  if (month > 4 && month < 10) {
    return false;
  }

  else if (month < 4 || month > 10) {
    return true;
  }

  int x = (year + year/4 + 5) % 7;
  int y = (year + year/4 + 6) % 7;

  if ( month == 4) {
    if ( day > (7 - x) ) {
      return false;
    }

    else if ( day == (7 - x) ) {
      return false;
    }

    else {
      return true;
    }
  }

  else if ( month == 10 ) {
    if ( day > (7 - y) ) {
      return true;
    }

    else if ( day == (7 - y) ) {
      return true;
    }

    else {
      return false;
    }
  }

 return false;
}


double toJulian(time_t t) {
  return (t/86400.0)  - 0.500 + 2440588.0;
}

double toDays(time_t t) {
    return toJulian(t) - J2000;
}

tmElements_t specify_time(int day, int month, int year, int hour, int minute, int second) {
    tmElements_t t;

    t.Day = day;
    t.Month = month;
    t.Year = year - 1970;    
    t.Wday = 1;
    t.Minute = minute;
    t.Second = second;

    int timezone_adjustment = isDst(t) ? MELBOURNE_TIMEZONE_DST : MELBOURNE_TIMEZONE;
    t.Hour = hour - timezone_adjustment;
    return t;
}

double siderealTime(double d, double lw) {
    return RAD * (280.16 + 360.9856235 * d) - lw;
}

double rightAscension(double l, double b) {
    return atan2(sin(l) * cos(E) - tan(b) * sin(E), cos(l));
}

double declination(double l, double b) {
    return asin(sin(b) * cos(E) + cos(b) * sin(E) * sin(l));
}

double solarMeanAnomaly(double d) {
    return RAD * (357.5291 + 0.98560028 * d);
}

double eclipticLongitude(double M) {
    double C = RAD * (1.9148 * sin(M) + 0.02 * sin(2 * M) + 0.0003 * sin(3 * M));  
    double P = RAD * 102.9372;
    return M + C + P + PI;
}

ra_dec sunCoords(float d){
    double M = solarMeanAnomaly(d);
    double L = eclipticLongitude(M);
    ra_dec r;
    r.ra = rightAscension(L, 0);
    r.dec = declination(L, 0);
    return r;
}

double azimuth(double H, double phi, double dec){
    return atan2(sin(H), cos(H) * sin(phi) - tan(dec) * cos(phi));
}

double altitude(double H, double phi, double dec){
    return asin(sin(phi) * sin(dec) + cos(phi) * cos(dec) * cos(H));
}

sun_pos solarPosition(time_t date, double latitude, double longitude) {
    double lw = RAD * -longitude;
    double phi = RAD * latitude;
    double d = toDays(date);
    ra_dec c = sunCoords(d);
    double H = siderealTime(d, lw) - c.ra;

    //printf("%lu\n", date);
    //printf("%lf\n", lw);
    //printf("%lf\n", phi);
    //printf("%lf\n", d);
    //printf("%lf\n", c.dec);
    //printf("%lf\n", c.ra);
    //printf("%lf\n", H);

    sun_pos pos;
    pos.azimuth = azimuth(H, phi, c.dec);
    pos.altitude = altitude(H, phi, c.dec);
    return pos;
}



void setup()
{
    Serial.begin(9600);
    delay(5000);
    double latitude = -37.94510;
    double longitude = 145.07790;
    const tmElements_t t = specify_time(14,10,2019,10,48,0);
    //time_t setTime = makeTime(&t);
    //setTime(10,48,0,14,10,2019);
    time_t tt = makeTime(t);

    //Serial.println(tt);
    //printf("%lu\n", setTime);
    //printf("%f\n", toJulian(setTime));
    //printf("%f\n", toDays(setTime));
    sun_pos p = solarPosition(tt, latitude, longitude);
    Serial.print("Azimuth:");
    Serial.print(180+ p.azimuth * DEG);
    Serial.print(" Elevation:");
    Serial.println(p.altitude * DEG);
    //printf("%lf\n", 180 + p.azimuth * DEG);
    //printf("%lf\n", p.altitude * DEG);
}

void loop() {
}

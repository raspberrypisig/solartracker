#include <stdio.h>
#define SECS_PER_MIN ((time_t)(60UL))
#define SECS_PER_HOUR ((time_t)(3600UL))
#define SECS_PER_DAY  ((time_t)(SECS_PER_HOUR * 24UL))
#define SECS_YR_2000 ((time_t)(946684800UL)) // the time at the start of y2k
#define LEAP_YEAR(Y) ( ((1970+(Y))>0) && !((1970+(Y))%4) && ( ((1970+(Y))%100) || !((1970+(Y))%400) ) )
#define MELBOURNE_TIMEZONE 10
#define MELBOURNE_TIMEZONE_DST 11

typedef long time_t;

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

time_t makeTime(tmElements_t tm)
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
  return (time_t)seconds; 
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
  printf("%d\n", x);
  printf("%d\n", y);

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

}

/*
def toMillis(date):
    return (date - epochStart).total_seconds() * 1000
*/

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

int main()
{
    tmElements_t t = specify_time(16,5,2018,13,04,00);
    time_t setTime = makeTime(t);
    printf("%ld\n", setTime);
    return 0;
}

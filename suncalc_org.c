#include <stdio.h>
#include <math.h>

#define MELBOURNE_TIMEZONE 10
#define MELBOURNE_TIMEZONE_DST 11

#define PI 3.14159265359
#define It PI
#define _t 315576e4
#define kt 86400
#define Bt 86400
#define jt It / 180
#define Zt 149597870700
#define Kt 6378137
#define $t .0002908882086657216
#define te 484813681109536e-20
#define ae 180 / It


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
  double deltapsi;
  double deltaepsilon;
  double ra;
  double decl;
  double azimuth;
  double altitude;
  double corrAltitude;
}spa;

double a(double t, double e) {
    return t - (int)(t / e) * e;
}

double e(double t) {
    return t = a(t, 2 * It);
}

double n(double t) {
    return ((int)(10 * t + 0.5) / 10.0);
}

double P(tmElements_t t) {
   
    int e = t.Year;
    int a = t.Month;
    double M = e + (a - .5) / 12.0;
    double i = i = M - 2e3;
    //printf("%lf\n", M);
    //printf("%lf\n", i);
    double s = 62.92 + .32217 * i + .005589 * pow(i, 2);
    //printf("%lf\n", s);
    double q = n(s);
    //printf("%lf\n", q);
    return q;
}



double w(tmElements_t t) {
    double seconds = P(t);
    double minutes = (double) t.Minute;
    double hour = (double) t.Hour;
    //dateX = new Date(t.getFullYear(),t.getMonth(),t.getDate(),t.getHours(),t.getMinutes(),t.getSeconds() + Me);
    //var e, a, n, M = dateX.getFullYear(), i = dateX.getMonth() + 1, s = dateX.getDate(), o = dateX.getHours(), r = dateX.getMinutes(), h = dateX.getSeconds();
    /*
    if (0 == M)
        return "invalid";
    if (1582 == M && 10 == i && s > 4 && 15 > s)
        return "invalid";
    */
    int month = t.Month;
    int e,n;
    int year = t.Year;
    int s = t.Day;

    if (month > 2) {
      e = year;
      n = month + 1;
    }

    else {
      e = year - 1;
      n = month + 13;
    }

    int u = (int)((int)(365.25 * e) + (int)(30.6001 * n) + s + 1720995);
    double c = 588829;

    //printf("%d\n", s);
    //printf("%d\n",u);

    if (  s + 31 * (month + 12 * year) >= c) {
     int a = (int)(0.01 * e);
     u += 2 - a + (int)(0.25 * a);
    }
    //printf("%d\n",u);

    double l = hour / 24 - .5;
    
    //printf("%lf\n", hour);
    //printf("%lf\n", l);

    if (0 > l) {
      l = l + 1;
      --u;
    }
 

    //printf("%lf\n", l);
    //printf("%d\n", u);

    double d = l + ((minutes+1) + ((int)(seconds))%60 / 60.0) / 60.0 / 24.0; // +1 is a hack, accounts for Me
    double g = 1e5 * (u + d);
    double m = floor(g);

    //printf("%lf\n", seconds);
    //printf("%d\n", );
    //printf("%lf\n", d);
    //printf("%lf\n", g);
    //printf("%.llf\n", m);
        

    if (g - m > 0.5 && ++m) {
     m /= 1e5;
     return 24 * m * 60 * 60;  
    }
    return 0;
    /*
    i > 2 ? (e = M,
    n = i + 1) : (e = M - 1,
    n = i + 13);
    var u = Math.floor(Math.floor(365.25 * e) + Math.floor(30.6001 * n) + s + 1720995)
        , c = 588829;
    s + 31 * (i + 12 * M) >= c && (a = Math.floor(.01 * e),
    u += 2 - a + Math.floor(.25 * a));
    var l = o / 24 - .5;
    0 > l && (l += 1,
    --u);
    var d = l + (r + h / 60) / 60 / 24
        , g = 1e5 * (u + d)
        , m = Math.floor(g);
    return g - m > .5 && ++m,
    m /= 1e5,
    24 * m * 60 * 60
    */
}



double m(tmElements_t t) {
    return (w(t) - 2451545.0 * kt) / _t;
}



double v(tmElements_t t) {
    double a;
    int e, n;
    int M = t.Year;
    int i = t.Month;
    int s = t.Day;
    int o = t.Minute;
    int r = t.Minute;
    int h = t.Second;
    if (i>2) {
      e = M;
      n = i + 1;
    }
    else {
      e = M - 1;
      n = i + 13;
    }
    
    double u = floor(floor(365.25 * e) + floor(30.6001 * n) + s + 1720995);
    int c = 588829;
    if (s + 31 * (i + 12 * M) >= c) {
       a = floor(.01 * e);
    }
    u += 2 - a + floor(.25 * a);
    double l = o / 24 - .5;
    if (0 > l) {
      l += 1;
      --u;
    }
    double d = l + (r + h / 60) / 60 / 24;
    double g = 1e5 * (u + d);
    int m = floor(g);
    if (g - m > .5) {
      ++m;
    }
    m /= 1e5;
    return floor(24 * m * 60 * 60);
}

spa X(tmElements_t t) {
  double T = m(t);
  double D = (297.85036 + 445267.11148 * T - .0019142 * pow(T, 2) + pow(T, 3) / 189474) * jt;
  double M = (357.52772 + 35999.05034 * T - 1603e-7 * pow(T, 2) - pow(T, 3) / 3e5) * jt;
  double MP = (134.96298 + 477198.867398 * T + .0086972 * pow(T, 2) + pow(T, 3) / 56250) * jt;
  double F = (93.27191 + 483202.017538 * T - .0036825 * pow(T, 2) + pow(T, 3) / 327270) * jt;
  double Omega = (125.04452 - 1934.136261 * T + .0020708 * pow(T, 2) + pow(T, 3) / 45e4) * jt;
  double deltapsi = 1e-4 * te * (+(-171996 + -174.2 * T) * sin(+Omega) + (-13187 + -1.6 * T) * sin(-2 * D + 2 * F + 2 * Omega) + (-2274 + -.2 * T) * sin(2 * F + 2 * Omega) + (2062 + .2 * T) * sin(2 * Omega) + (1426 + -3.4 * T) * sin(+M) + (712 + .1 * T) * sin(+MP) + (-517 + 1.2 * T) * sin(-2 * D + M + 2 * F + 2 * Omega) + (-386 + -.4 * T) * sin(2 * F + Omega) + -301 * sin(+MP + 2 * F + 2 * Omega) + (217 + -.5 * T) * sin(-2 * D - 1 * M + 2 * F + 2 * Omega) + -158 * sin(-2 * D + MP) + (129 + .1 * T) * sin(-2 * D + 2 * F + Omega) + 123 * sin(-1 * MP + 2 * F + 2 * Omega) + 63 * sin(2 * D) + (63 + .1 * T) * sin(+MP + Omega) + -59 * sin(2 * D * -1 * MP + 2 * F + 2 * Omega) + (-58 + -.1 * T) * sin(-1 * MP + Omega) + -51 * sin(+MP + 2 * F + Omega) + 48 * sin(-2 * D + 2 * MP) + 46 * sin(-2 * MP + 2 * F + Omega) + -38 * sin(2 * D + 2 * F + 2 * Omega) + -31 * sin(2 * MP + 2 * F + 2 * Omega) + 29 * sin(2 * MP) + 29 * sin(-2 * D + MP + 2 * F + 2 * Omega) + 26 * sin(2 * F) + -22 * sin(-2 * D + 2 * F) + 21 * sin(-1 * MP + 2 * F + Omega) + (17 + -.1 * T) * sin(2 * M) + 16 * sin(2 * D - 1 * MP + Omega) + (-16 + .1 * T) * sin(-2 * D + 2 * M + 2 * F + 2 * Omega) + -15 * sin(+M + Omega) + -13 * sin(-2 * D + MP + Omega) + -12 * sin(-1 * M + Omega) + 11 * sin(2 * MP - 2 * F) + -10 * sin(2 * D - 1 * MP + 2 * F + Omega) + -8 * sin(2 * D + MP + 2 * F + 2 * Omega) + 7 * sin(+M + 2 * F + 2 * Omega) + -7 * sin(-2 * D + M + MP) + -7 * sin(-1 * M + 2 * F + 2 * Omega) + -8 * sin(2 * D + 2 * F + Omega) + 6 * sin(2 * D + MP) + 6 * sin(-2 * D + 2 * MP + 2 * F + 2 * Omega) + 6 * sin(-2 * D + MP + 2 * F + Omega) + -6 * sin(2 * D - 2 * MP + Omega) + -6 * sin(2 * D + Omega) + 5 * sin(-1 * M + MP) + -5 * sin(-2 * D - 1 * M + 2 * F + Omega) + -5 * sin(-2 * D + Omega) + -5 * sin(2 * MP + 2 * F + Omega) + 4 * sin(-2 * D + 2 * MP + Omega) + 4 * sin(-2 * D + M + 2 * F + Omega) + 4 * sin(+MP - 2 * F) + -4 * sin(-1 * D + MP) + -4 * sin(-2 * D + M) + -4 * sin(+D) + 3 * sin(+MP + 2 * F) + -3 * sin(-2 * MP + 2 * F + 2 * Omega) + -3 * sin(-1 * D - 1 * M + MP) + -3 * sin(+M + MP) + -3 * sin(-1 * M + MP + 2 * F + 2 * Omega) + -3 * sin(2 * D - 1 * M - 1 * MP + 2 * F + 2 * Omega) + -3 * sin(3 * MP + 2 * F + 2 * Omega) + -3 * sin(2 * D - 1 * M + 2 * F + 2 * Omega));
  double deltaepsilon = 1e-4 * te * (+(92025 + 8.9 * T) * cos(+Omega) + (5736 + -3.1 * T) * cos(-2 * D + 2 * F + 2 * Omega) + (977 + -.5 * T) * cos(2 * F + 2 * Omega) + (-895 + .5 * T) * cos(2 * Omega) + (54 + -.1 * T) * cos(+M) + -7 * cos(+MP) + (224 + -.6 * T) * cos(-2 * D + M + 2 * F + 2 * Omega) + 200 * cos(2 * F + Omega) + (129 + -.1 * T) * cos(+MP + 2 * F + 2 * Omega) + (-95 + .3 * T) * cos(-2 * D - 1 * M + 2 * F + 2 * Omega) + -70 * cos(-2 * D + 2 * F + Omega) + -53 * cos(-1 * MP + 2 * F + 2 * Omega) + -33 * cos(+MP + Omega) + 26 * cos(2 * D - 1 * MP + 2 * F + 2 * Omega) + 32 * cos(-1 * MP + Omega) + 27 * cos(+MP + 2 * F + Omega) + -24 * cos(-2 * MP + 2 * F + Omega) + 16 * cos(2 * D + 2 * F + 2 * Omega) + 13 * cos(2 * MP + 2 * F + 2 * Omega) + -12 * cos(-2 * D + MP + 2 * F + 2 * Omega) + -10 * cos(-1 * MP + 2 * F + Omega) + -8 * cos(2 * D - 1 * MP + Omega) + 7 * cos(-2 * D + 2 * M + 2 * F + 2 * Omega) + 9 * cos(+M + Omega) + 7 * cos(-2 * D + MP + Omega) + 6 * cos(-1 * M + Omega) + 5 * cos(2 * D - 1 * MP + 2 * F + Omega) + 3 * cos(2 * D + MP + 2 * F + 2 * Omega) + -3 * cos(+M + 2 * F + 2 * Omega) + 3 * cos(-1 * M + 2 * F + 2 * Omega) + 3 * cos(2 * D + 2 * F + Omega) + -3 * cos(-2 * D + 2 * MP + 2 * F + 2 * Omega) + -3 * cos(-2 * D + MP + 2 * F + Omega) + 3 * cos(2 * D - 2 * MP + Omega) + 3 * cos(2 * D + Omega) + 3 * cos(-2 * D - 1 * M + 2 * F + Omega) + 3 * cos(-2 * D + Omega) + 3 * cos(2 * MP + 2 * F + Omega));
  spa sp;   
  sp.deltapsi = deltapsi;
  sp.deltaepsilon = deltaepsilon;  
  return sp;
}

double  z(tmElements_t t) {
        double T = m(t);
        double U = T/100;
        double y =  23 * jt + 26 * $t + 21.448 * te + (-4680.93 * U - 1.55 * pow(U, 2) + 1999.25 * pow(U, 3) - 51.38 * pow(U, 4) - 249.67 * pow(U, 5) + -39.05 * pow(U, 6) + 7.12 * pow(U, 7) + 27.87 * pow(U, 8) + 5.79 * pow(U, 9) + 2.45 * pow(U, 10)) * te;
        return y;
}

double S(tmElements_t t) {
    double epsilon0 = z(t);
    spa e = X(t);
    double deltapsi = e.deltapsi;
    double deltaepsilon = e.deltaepsilon;
    double yy = epsilon0 + deltaepsilon;
    return yy;
}

double i(tmElements_t t) {
    double T = m(t);
    return (125.04 - 1934.136 * T) * jt;
}


double h(tmElements_t t) {
    double T = m(t);
    return fmod((357.52911 + 35999.05029 * T - 1537e-7 * pow(T, 2)) * jt,  (360 * jt));
}

double l(tmElements_t t) {
    double T = m(t);
    double M = h(t);
    return (1.914602 - .004817 * T - 14e-6 * pow(T, 2)) * jt * sin(M) + (.019993 - 101e-6 * T) * jt * sin(2 * M) + 289e-6 * jt * sin(3 * M);
}

double o(tmElements_t t) {
    double T = m(t);
    return (280.46646 + 36000.76983 * T + 3032e-7 * pow(T, 2)) * jt;
}

double r(tmElements_t t) {
    return o(t) + l(t);

}

double s(tmElements_t t) {
    double T = m(t);
    double omega = i(t);
    return r(t) - .00569 * jt - .00478 * jt * sin(omega);
}

spa O(tmElements_t t) {
    double epsilon = S(t);
    double epsilonprime = epsilon + .00256 * jt * cos(i(t));
    double sunLong = s(t);
    double ssl = sin(sunLong);
    double ra = atan2(cos(epsilonprime) * ssl, cos(sunLong));
    double decl = asin(sin(epsilonprime) * ssl);
    spa sp;
    sp.ra  = ra;
    sp.decl = decl;
    return sp;
}


double c(tmElements_t t) {
    double T = m(t);
    return  h(t) + l(t);
}

double d(tmElements_t t) {
    double T = m(t);
    return .016708634 - 42037e-9 * T - 1.267e-7 * pow(T, 2);
}

double g(tmElements_t t) {
    double eccentricity = d(t);
    double trueAnomaly = c(t);
    return 1.000001018 * Zt * (1 - pow(eccentricity, 2)) / (1 + eccentricity * cos(trueAnomaly));
}

double A(tmElements_t t) {
    double T = m(t);
    double a = (280.46061837 + 360.98564736629 * (v(t) / Bt - 2451545) + 387933e-9 * pow(T, 2) - pow(T, 3) / 3871e4) * jt;
    return e(a);
}

double x(tmElements_t t) {
  spa hA = X(t);
  double deltapsi = hA.deltapsi;
  double trueObliquity = S(t);
  double correction = deltapsi * cos(trueObliquity);
  return e(A(t) + correction);
}

double V(tmElements_t t, double e) {
    double angle = x(t);
    return angle - e;
}

double b(tmElements_t t, double e, double a) {
    return V(t, e) - a;
}

spa y(tmElements_t t, double e, double a, double n, double M) {
    double H = b(t, M, e);
    double azimuth = atan2(sin(H), cos(H) * sin(n) - tan(a) * cos(n));
    double altitude = asin(sin(n) * sin(a) + cos(n) * cos(a) * cos(H));
    spa sp;
    sp.azimuth  = azimuth;
    sp.altitude = altitude;
    return sp;    
}


double bt(double t, double e) {
    double azParallax = asin(Kt / t);
    double altParallax = asin(sin(azParallax) * cos(e));
    return altParallax;
}

//double Y(double t, double e, double a) {
double Y(double t, double e, double a) {  
        //int e = 283;
        //int a = 1010;
        double h5 = t / jt;
        double v5 = (h5 + 10.3 / (h5 + 5.11)) * jt;
        double pressCorr = a / 1010 * 283 / e;
        double R = 1.02 * pressCorr * $t / tan(v5);
        return R;
    }


spa L(tmElements_t t, double e, double a, double n, double M, double i, double s, double o) {
    s = 283,
    o = 1010;
    spa r = y(t, e, a, n, M);
    double azimuth = r.azimuth;
    double altitude = r.altitude;
    if (i) {
     altitude -= bt(i, altitude);
    } 
    double corrAltitude = altitude + Y(altitude, s, o);
    spa sp;
    sp.azimuth = azimuth;
    sp.corrAltitude = corrAltitude;
    return sp;
}


spa _(tmElements_t t, double e, double a) {
  int n = 283;
  int M = 1010;
  spa sp = O(t);
  double sunRA = sp.ra;
  double sunDecl = sp.decl;
  //return g(t);
  return L(t, sunRA, sunDecl, e, a, g(t), n, M);
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


tmElements_t specify_time(int day, int month, int year, int hour, int minute, int second) {
    tmElements_t t;

    t.Day = day;
    t.Month = month;
    //t.Year = year - 1970;
    t.Year = year;    
    t.Wday = 1;
    t.Minute = minute;
    t.Second = second;

    int timezone_adjustment = isDst(t) ? MELBOURNE_TIMEZONE_DST : MELBOURNE_TIMEZONE;
    t.Hour = hour - timezone_adjustment;
    return t;
}

spa getSunSecInfo(tmElements_t t, double e, double a) {
  a = -1 * a;
  double Me = P(t);
  tmElements_t M = t;
  double i = e * jt;
  double s = a * jt;
  spa o = _(M, i, s);
  double r = o.corrAltitude * ae;
  double h = o.azimuth * ae + 180;
  double u = o.corrAltitude;
  double c = o.azimuth ;
  return o;
}

int main(int argc, char const *argv[])
{
    double latitude = -37.94510;
    double longitude = 145.07790;
    //const tmElements_t t = specify_time(14,10,2019,10,48,0);
    const tmElements_t t = {
      .Second = 0,
      .Minute = 48,
      .Hour = 23,
      .Wday = 1,
      .Day = 13,
      .Month = 10,
      .Year = 2019
    }; //UTC time
    //double d  = S(t);
    //printf("%lf\n", d);
    //spa sp = _(t);
    //printf("%lf\n", sp.ra);
    //printf("%lf\n", sp.decl);
    
    //P(t);
    //printf("%lf\n", P(t));
    //printf("%d\n", P(t));
    int a = 4+50;
    return 0;
}


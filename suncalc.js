//var f = SoMo.getSunSecInfo(mt, ht[1], ht[0], pt / 6e4, "de")
//mt: Tue Oct 2015 2019 21:20:00 GMT+1100 (AEDST) Date
//ht: [-3.51559, 40.1789]  lat,long
//pt: 7200000 ?  72000000/6e4 -> this is UTC+11 in milliseconds so (11*60*60*1000=39600000)
//jt: 0.017453292519943295
//ae: 57.29577951308232
//a: -lat

var It = Math.PI
//var Ut = "undef"
var _t = 315576e4
var kt = 86400
var Bt = 86400
//var Ct = 3600
//var Jt = 3600
//var qt = 60
//var Wt = 31556925.9746784
var jt = It / 180
//var Gt = .017453292519943295
//var Qt = 6.283185307179586
var Zt = 149597870700
var Kt = 6378137
var $t = .0002908882086657216
var te = 484813681109536e-20
//var ee = 2551439.9952
var ae = 180 / It
//var ne = It / 180
//var Me = 0
//var ie = new Object

function a(t, e) {
    return t - Math.floor(t / e) * e
}

function A(t) {
    T = m(t);
    var a = (280.46061837 + 360.98564736629 * (v(t) / Bt - 2451545) + 387933e-9 * Math.pow(T, 2) - Math.pow(T, 3) / 3871e4) * jt;
    return e(a)
}

function b(t, e, a) {
    return V(t, e) - a
}

function bt(t, e) {
    return azParallax = Math.asin(Kt / t),
    altParallax = Math.asin(Math.sin(azParallax) * Math.cos(e)),
    altParallax
}

function c(t) {
    return T = m(t),
    h(t) + l(t)
}

function d(t) {
    return T = m(t),
    .016708634 - 42037e-9 * T - 1.267e-7 * Math.pow(T, 2)
}

function e(t) {
    return t = a(t, 2 * It)
}

function g(t) {
    return eccentricity = d(t),
    trueAnomaly = c(t),
    1.000001018 * Zt * (1 - Math.pow(eccentricity, 2)) / (1 + eccentricity * Math.cos(trueAnomaly))
}

function h(t) {
    return T = m(t),
    (357.52911 + 35999.05029 * T - 1537e-7 * Math.pow(T, 2)) * jt % (360 * jt)
}

function i(t) {
    return T = m(t),
    (125.04 - 1934.136 * T) * jt
}

function l(t) {
    return T = m(t),
    M = h(t),
    (1.914602 - .004817 * T - 14e-6 * Math.pow(T, 2)) * jt * Math.sin(M) + (.019993 - 101e-6 * T) * jt * Math.sin(2 * M) + 289e-6 * jt * Math.sin(3 * M)
}

function L(t, e, a, n, M, i, s, o) {
    s = 283,
    o = 1010;
    var r = y(t, e, a, n, M);
    return azimuth = r.azimuth,
    altitude = r.altitude,
    null != i && (altitude -= bt(i, altitude)),
    corrAltitude = altitude + Y(altitude, s, o),
    {
        azimuth: azimuth,
        corrAltitude: corrAltitude
    }
}

function m(t) {
    return (w(t) - 2451545 * kt) / _t
}

function n(t) {
    return Math.round(10 * t) / 10
}

function o(t) {
    return T = m(t),
    (280.46646 + 36000.76983 * T + 3032e-7 * Math.pow(T, 2)) * jt
}

function O(t) {
    return epsilon = S(t),
    epsilonprime = epsilon + .00256 * jt * Math.cos(i(t)),
    sunLong = s(t),
    ssl = Math.sin(sunLong),
    ra = Math.atan2(Math.cos(epsilonprime) * ssl, Math.cos(sunLong)),
    decl = Math.asin(Math.sin(epsilonprime) * ssl),
    {
        ra: ra,
        decl: decl
    }
}

function P(t) {
    var e = t.getFullYear()
      , a = t.getMonth() + 1
      , M = e + (a - .5) / 12
      , i = 0
      , s = 0;
    return e >= 1600 && 1700 > e && (i = M - 1600,
    s = 120 - .9808 * i - .01532 * Math.pow(i, 2) + Math.pow(i, 3) / 7129),
    e >= 1700 && 1800 > e && (i = M - 1700,
    s = 8.83 + .1603 * i - .0059285 * Math.pow(i, 2) + 13336e-8 * Math.pow(i, 3) - Math.pow(i, 4) / 1174e3),
    e >= 1800 && 1860 > e && (i = M - 1800,
    s = 13.72 - .332447 * i + .0068612 * Math.pow(i, 2) + .0041116 * Math.pow(i, 3) - 37436e-8 * Math.pow(i, 4) + 121272e-10 * Math.pow(i, 5) - 1.699e-7 * Math.pow(i, 6) + 8.75e-10 * Math.pow(i, 7)),
    e >= 1860 && 1900 > e && (i = M - 1860,
    s = 7.62 + .5737 * i - .251754 * Math.pow(i, 2) + .01680668 * Math.pow(i, 3) - .0004473624 * Math.pow(i, 4) + Math.pow(i, 5) / 233174),
    e >= 1900 && 1920 > e && (i = M - 1900,
    s = -2.79 + 1.494119 * i - .0598939 * Math.pow(i, 2) + .0061966 * Math.pow(i, 3) - 197e-6 * Math.pow(i, 4)),
    e >= 1920 && 1941 > e && (i = M - 1920,
    s = 21.2 + .84493 * i - .0761 * Math.pow(i, 2) + .0020936 * Math.pow(i, 3)),
    e >= 1941 && 1961 > e && (i = M - 1950,
    s = 29.07 + .407 * i - Math.pow(i, 2) / 233 + Math.pow(i, 3) / 2547),
    e >= 1961 && 1986 > e && (i = M - 1975,
    s = 45.45 + 1.067 * i - Math.pow(i, 2) / 260 - Math.pow(i, 3) / 718),
    e >= 1986 && 2005 > e && (i = M - 2e3,
    s = 63.86 + .3345 * i - .060374 * Math.pow(i, 2) + .0017275 * Math.pow(i, 3) + 651814e-9 * Math.pow(i, 4) + 2373599e-11 * Math.pow(i, 5)),
    e >= 2005 && 2050 > e && (i = M - 2e3,
    s = 62.92 + .32217 * i + .005589 * Math.pow(i, 2)),
    e >= 2050 && 2150 > e && (s = -20 + 32 * Math.pow((M - 1820) / 100, 2) - .5628 * (2150 - M)),
    e >= 2150 && (u = (M - 1820) / 100,
    s = -20 + 32 * Math.pow(u, 2)),
    n(s)
}

function r(t) {
    return o(t) + l(t)

}

function s(t) {
    return T = m(t),
    omega = i(t),
    r(t) - .00569 * jt - .00478 * jt * Math.sin(omega)
}

function S(t) {
    epsilon0 = z(t);
    var e = X(t);
    return deltapsi = e.deltapsi,
    deltaepsilon = e.deltaepsilon,
    epsilon0 + deltaepsilon
}

function v(t) {
    var e, a, n, M = t.getFullYear(), i = t.getMonth() + 1, s = t.getDate(), o = t.getHours(), r = t.getMinutes(), h = t.getSeconds();
    if (0 == M)
        return "invalid";
    if (1582 == M && 10 == i && s > 4 && 15 > s)
        return "invalid";
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
    Math.round(24 * m * 60 * 60)
}

function V(t, e) {
    return angle = x(t),
    angle - e
}

    function w(t) {
        dateX = new Date(t.getFullYear(),t.getMonth(),t.getDate(),t.getHours(),t.getMinutes(),t.getSeconds() + Me);
        var e, a, n, M = dateX.getFullYear(), i = dateX.getMonth() + 1, s = dateX.getDate(), o = dateX.getHours(), r = dateX.getMinutes(), h = dateX.getSeconds();
        if (0 == M)
            return "invalid";
        if (1582 == M && 10 == i && s > 4 && 15 > s)
            return "invalid";
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
    }

    function x(t) {
        return hA = X(t),
        deltapsi = hA.deltapsi,
        trueObliquity = S(t),
        correction = deltapsi * Math.cos(trueObliquity),
        e(A(t) + correction)
    }

    function X(t) {
        return T = m(t),
        D = (297.85036 + 445267.11148 * T - .0019142 * Math.pow(T, 2) + Math.pow(T, 3) / 189474) * jt,
        M = (357.52772 + 35999.05034 * T - 1603e-7 * Math.pow(T, 2) - Math.pow(T, 3) / 3e5) * jt,
        MP = (134.96298 + 477198.867398 * T + .0086972 * Math.pow(T, 2) + Math.pow(T, 3) / 56250) * jt,
        F = (93.27191 + 483202.017538 * T - .0036825 * Math.pow(T, 2) + Math.pow(T, 3) / 327270) * jt,
        Omega = (125.04452 - 1934.136261 * T + .0020708 * Math.pow(T, 2) + Math.pow(T, 3) / 45e4) * jt,
        deltapsi = 1e-4 * te * (+(-171996 + -174.2 * T) * Math.sin(+Omega) + (-13187 + -1.6 * T) * Math.sin(-2 * D + 2 * F + 2 * Omega) + (-2274 + -.2 * T) * Math.sin(2 * F + 2 * Omega) + (2062 + .2 * T) * Math.sin(2 * Omega) + (1426 + -3.4 * T) * Math.sin(+M) + (712 + .1 * T) * Math.sin(+MP) + (-517 + 1.2 * T) * Math.sin(-2 * D + M + 2 * F + 2 * Omega) + (-386 + -.4 * T) * Math.sin(2 * F + Omega) + -301 * Math.sin(+MP + 2 * F + 2 * Omega) + (217 + -.5 * T) * Math.sin(-2 * D - 1 * M + 2 * F + 2 * Omega) + -158 * Math.sin(-2 * D + MP) + (129 + .1 * T) * Math.sin(-2 * D + 2 * F + Omega) + 123 * Math.sin(-1 * MP + 2 * F + 2 * Omega) + 63 * Math.sin(2 * D) + (63 + .1 * T) * Math.sin(+MP + Omega) + -59 * Math.sin(2 * D * -1 * MP + 2 * F + 2 * Omega) + (-58 + -.1 * T) * Math.sin(-1 * MP + Omega) + -51 * Math.sin(+MP + 2 * F + Omega) + 48 * Math.sin(-2 * D + 2 * MP) + 46 * Math.sin(-2 * MP + 2 * F + Omega) + -38 * Math.sin(2 * D + 2 * F + 2 * Omega) + -31 * Math.sin(2 * MP + 2 * F + 2 * Omega) + 29 * Math.sin(2 * MP) + 29 * Math.sin(-2 * D + MP + 2 * F + 2 * Omega) + 26 * Math.sin(2 * F) + -22 * Math.sin(-2 * D + 2 * F) + 21 * Math.sin(-1 * MP + 2 * F + Omega) + (17 + -.1 * T) * Math.sin(2 * M) + 16 * Math.sin(2 * D - 1 * MP + Omega) + (-16 + .1 * T) * Math.sin(-2 * D + 2 * M + 2 * F + 2 * Omega) + -15 * Math.sin(+M + Omega) + -13 * Math.sin(-2 * D + MP + Omega) + -12 * Math.sin(-1 * M + Omega) + 11 * Math.sin(2 * MP - 2 * F) + -10 * Math.sin(2 * D - 1 * MP + 2 * F + Omega) + -8 * Math.sin(2 * D + MP + 2 * F + 2 * Omega) + 7 * Math.sin(+M + 2 * F + 2 * Omega) + -7 * Math.sin(-2 * D + M + MP) + -7 * Math.sin(-1 * M + 2 * F + 2 * Omega) + -8 * Math.sin(2 * D + 2 * F + Omega) + 6 * Math.sin(2 * D + MP) + 6 * Math.sin(-2 * D + 2 * MP + 2 * F + 2 * Omega) + 6 * Math.sin(-2 * D + MP + 2 * F + Omega) + -6 * Math.sin(2 * D - 2 * MP + Omega) + -6 * Math.sin(2 * D + Omega) + 5 * Math.sin(-1 * M + MP) + -5 * Math.sin(-2 * D - 1 * M + 2 * F + Omega) + -5 * Math.sin(-2 * D + Omega) + -5 * Math.sin(2 * MP + 2 * F + Omega) + 4 * Math.sin(-2 * D + 2 * MP + Omega) + 4 * Math.sin(-2 * D + M + 2 * F + Omega) + 4 * Math.sin(+MP - 2 * F) + -4 * Math.sin(-1 * D + MP) + -4 * Math.sin(-2 * D + M) + -4 * Math.sin(+D) + 3 * Math.sin(+MP + 2 * F) + -3 * Math.sin(-2 * MP + 2 * F + 2 * Omega) + -3 * Math.sin(-1 * D - 1 * M + MP) + -3 * Math.sin(+M + MP) + -3 * Math.sin(-1 * M + MP + 2 * F + 2 * Omega) + -3 * Math.sin(2 * D - 1 * M - 1 * MP + 2 * F + 2 * Omega) + -3 * Math.sin(3 * MP + 2 * F + 2 * Omega) + -3 * Math.sin(2 * D - 1 * M + 2 * F + 2 * Omega)),
        deltaepsilon = 1e-4 * te * (+(92025 + 8.9 * T) * Math.cos(+Omega) + (5736 + -3.1 * T) * Math.cos(-2 * D + 2 * F + 2 * Omega) + (977 + -.5 * T) * Math.cos(2 * F + 2 * Omega) + (-895 + .5 * T) * Math.cos(2 * Omega) + (54 + -.1 * T) * Math.cos(+M) + -7 * Math.cos(+MP) + (224 + -.6 * T) * Math.cos(-2 * D + M + 2 * F + 2 * Omega) + 200 * Math.cos(2 * F + Omega) + (129 + -.1 * T) * Math.cos(+MP + 2 * F + 2 * Omega) + (-95 + .3 * T) * Math.cos(-2 * D - 1 * M + 2 * F + 2 * Omega) + -70 * Math.cos(-2 * D + 2 * F + Omega) + -53 * Math.cos(-1 * MP + 2 * F + 2 * Omega) + -33 * Math.cos(+MP + Omega) + 26 * Math.cos(2 * D - 1 * MP + 2 * F + 2 * Omega) + 32 * Math.cos(-1 * MP + Omega) + 27 * Math.cos(+MP + 2 * F + Omega) + -24 * Math.cos(-2 * MP + 2 * F + Omega) + 16 * Math.cos(2 * D + 2 * F + 2 * Omega) + 13 * Math.cos(2 * MP + 2 * F + 2 * Omega) + -12 * Math.cos(-2 * D + MP + 2 * F + 2 * Omega) + -10 * Math.cos(-1 * MP + 2 * F + Omega) + -8 * Math.cos(2 * D - 1 * MP + Omega) + 7 * Math.cos(-2 * D + 2 * M + 2 * F + 2 * Omega) + 9 * Math.cos(+M + Omega) + 7 * Math.cos(-2 * D + MP + Omega) + 6 * Math.cos(-1 * M + Omega) + 5 * Math.cos(2 * D - 1 * MP + 2 * F + Omega) + 3 * Math.cos(2 * D + MP + 2 * F + 2 * Omega) + -3 * Math.cos(+M + 2 * F + 2 * Omega) + 3 * Math.cos(-1 * M + 2 * F + 2 * Omega) + 3 * Math.cos(2 * D + 2 * F + Omega) + -3 * Math.cos(-2 * D + 2 * MP + 2 * F + 2 * Omega) + -3 * Math.cos(-2 * D + MP + 2 * F + Omega) + 3 * Math.cos(2 * D - 2 * MP + Omega) + 3 * Math.cos(2 * D + Omega) + 3 * Math.cos(-2 * D - 1 * M + 2 * F + Omega) + 3 * Math.cos(-2 * D + Omega) + 3 * Math.cos(2 * MP + 2 * F + Omega)),
        {
            deltapsi: deltapsi,
            deltaepsilon: deltaepsilon
        }
    }

    function y(t, e, a, n, M) {
        return H = b(t, M, e),
        azimuth = Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(n) - Math.tan(a) * Math.cos(n)),
        altitude = Math.asin(Math.sin(n) * Math.sin(a) + Math.cos(n) * Math.cos(a) * Math.cos(H)),
        {
            azimuth: azimuth,
            altitude: altitude
        }
    }

    function Y(t, e, a) {
        return e = 283,
        a = 1010,
        h5 = t / jt,
        v5 = (h5 + 10.3 / (h5 + 5.11)) * jt,
        pressCorr = a / 1010 * 283 / e,
        R = 1.02 * pressCorr * $t / Math.tan(v5),
        R
    }

    function z(t) {
        return T = m(t),
        U = T / 100,
        23 * jt + 26 * $t + 21.448 * te + (-4680.93 * U - 1.55 * Math.pow(U, 2) + 1999.25 * Math.pow(U, 3) - 51.38 * Math.pow(U, 4) - 249.67 * Math.pow(U, 5) + -39.05 * Math.pow(U, 6) + 7.12 * Math.pow(U, 7) + 27.87 * Math.pow(U, 8) + 5.79 * Math.pow(U, 9) + 2.45 * Math.pow(U, 10)) * te
    }


    function _(t, e, a, n, M) {
        n = 283,
        M = 1010;
        var i = O(t);
        return sunRA = i.ra,
        sunDecl = i.decl,
        L(t, sunRA, sunDecl, e, a, g(t), n, M)
    }

   var getSunSecInfo = function(t, e, a, n) {
        var t = new Date(t.getTime());
        a = -1 * a,
        t.setMinutes(t.getMinutes() - n);
        Me = P(t);
        var M = t
          , i = e * jt
          , s = a * jt
          , o = _(M, i, s)
          , r = o.corrAltitude * ae
          , h = o.azimuth * ae + 180
          , u = o.corrAltitude
          , c = o.azimuth
        return {
            Azimuth_Rad: c,
           Altitude_Rad: u,
            Azimuth_Deg: h,
            Altitude_Deg: r,
           
        }
    }
    
    const boo = getSunSecInfo(new Date('14 october 2019 10:48:00'), -37.9451, 145.0779, 660)
    console.log(boo)

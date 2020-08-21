from decimal import Decimal, getcontext

def pi():
    """Compute Pi to the current precision.

    >>> print(pi())
    3.141592653589793238462643383

    """
    getcontext().prec += 2  # extra digits for intermediate steps
    three = Decimal(3)      # substitute "three=3.0" for regular floats
    lasts, t, s, n, na, d, da = 0, three, 3, 1, 0, 0, 24
    while s != lasts:
        lasts = s
        n, na = n+na, na+8
        d, da = d+da, da+32
        t = (t * n) / d
        s += t
    getcontext().prec -= 2
    return +s               # unary plus applies the new precision

_pi = pi()

def radians(degrees):
    getcontext().prec += 2
    rad = _pi * degrees / 180
    getcontext().prec -= 2
    return +rad

def degrees(radians):
    getcontext().prec += 2
    deg = radians * 180 / _pi
    getcontext().prec -= 2
    return +deg

def exp(x):
    """Return e raised to the power of x.  Result type matches input type.

    >>> print(exp(Decimal(1)))
    2.718281828459045235360287471
    >>> print(exp(Decimal(2)))
    7.389056098930650227230427461
    >>> print(exp(2.0))
    7.38905609893
    >>> print(exp(2+0j))
    (7.38905609893+0j)

    """
    getcontext().prec += 2
    i, lasts, s, fact, num = 0, 0, 1, 1, 1
    while s != lasts:
        lasts = s
        i += 1
        fact *= i
        num *= x
        s += num / fact
    getcontext().prec -= 2
    return +s

def cos(x):
    """Return the cosine of x as measured in radians.

    The Taylor series approximation works best for a small value of x.
    For larger values, first compute x = x % (2 * pi).

    >>> print(cos(Decimal('0.5')))
    0.8775825618903727161162815826
    >>> print(cos(0.5))
    0.87758256189
    >>> print(cos(0.5+0j))
    (0.87758256189+0j)

    """
    getcontext().prec += 2
    i, lasts, s, fact, num, sign = 0, 0, 1, 1, 1, 1
    c = 0
    while s != lasts:
        lasts = s
        i += 2
        fact *= i * (i-1)
        num *= x * x
        sign *= -1
        s += num / fact * sign
        c += 1
    getcontext().prec -= 2
    return +s

def sin(x):
    """Return the sine of x as measured in radians.

    The Taylor series approximation works best for a small value of x.
    For larger values, first compute x = x % (2 * pi).

    >>> print(sin(Decimal('0.5')))
    0.4794255386042030002732879352
    >>> print(sin(0.5))
    0.479425538604
    >>> print(sin(0.5+0j))
    (0.479425538604+0j)

    """
    getcontext().prec += 2
    i, lasts, s, fact, num, sign = 1, 0, x, 1, x, 1
    c = 0
    while s != lasts:
        lasts = s
        i += 2
        fact *= i * (i-1)
        num *= x * x
        sign *= -1
        s += num / fact * sign
        c += 1
    getcontext().prec -= 2
    return +s

def tan(x):
    """\
    Return the sine of x as measured in radians.

    This is a cheap and dirty implememtation. The "real" way to do this
    is with a Taylor series expansion that uses Bernoulli numbers, and I don't
    want to go there right now.
    """

    return sin(x) / cos(x)

def atan(x):
    """\
    Return the arctangent of x in radians

    This uses a Taylor series expansion, which converges very slowly...
    atan(x) = x - x**3/3 + x**5/5 - x**7/7 + ...
    Compare with the series for sine, which is similar but has factorials in the denominator.
    """
    getcontext().prec += 2
    i, lasts, s, num, sign = 1, 0, x, x, 1

    for _ in range(2000000):
        lasts = s
        i += 2
        num *= x * x
        sign *= -1
        s += (num / i) * sign
    getcontext().prec -= 2
    return +s

def atan2(y, x):
    getcontext().prec += 2
    slope = x / y
    angle = atan(slope)
    getcontext().prec -= 2
    return +angle

def test():
    import math

    # cosine = cos(radians(Decimal(60)))
    rad = radians(Decimal(45))
    tangent = tan(rad)
    # tangent = Decimal(math.tan(math.radians(45)))
    print(degrees(atan(tangent)))
    print(4*atan(Decimal(1)))
    print(_pi)

if __name__ == "__main__":
    test()



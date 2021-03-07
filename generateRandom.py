import time
import numpy as np


def congruenciaLineal(n):
    xn = np.random.random()
    k = 4
    a = 1 + (2 * k)
    c = 3
    g = 1
    m = 1024
    while m < n:
        g = g + 1
        m = 2 ** g

    randoms = []
    for i in range(n):
        xn1 = ((a * xn) + c) % m
        randoms.append(xn1 / m)
        xn = xn1

    return randoms


def congruenciaMult(n):
    xn = int(time.time())
    t = 3
    a = 3 + (8 * t)
    g = 1
    m = 1024
    while m < n:
        g = g + 1
        m = 2 * g

    randoms = []
    for i in range(n):
        xn1 = (a * xn) % m
        randoms.append(xn1 / m)
        xn = xn1

    return randoms

import numpy as np
from scipy.stats.distributions import chi2
from scipy.stats import kstwo
import requests


# Retorna si los números ingresados pasan una prueba de medias
def testMedia(randoms):
    med = media(randoms)

    n = len(randoms)
    z = 1.96

    li = (1 / 2) - (z * (1 / np.sqrt(12 * n)));
    ls = (1 / 2) + (z * (1 / np.sqrt(12 * n)));

    return (med <= ls) & (med >= li);


# Retorna si los números ingresados pasan una prueba de varianza
def testVarianza(randoms):
    n = len(randoms)
    grade_liberty = n - 1
    aceptation = 0.95
    a = 1 - aceptation

    variance = np.var(randoms, ddof=1)

    a_2 = a / 2
    a_3 = 1 - a_2

    xa_1 = chi2.ppf(a_3, df=grade_liberty)
    xa_2 = chi2.ppf(a_2, df=grade_liberty)

    li = xa_1 / (12 * grade_liberty)
    ls = xa_2 / (12 * grade_liberty)

    if ls > li:
        return (variance <= ls) & (variance >= li)
    else:
        return (variance >= ls) & (variance <= li)


# Retorna si los números ingresados pasan una prueba de Chi2
def testChi2(randoms):
    n = len(randoms)

    hist = np.histogram(randoms)[0]

    chiSum = 0

    for i in range(len(hist)):
        frecObt = hist[i]
        frecEsp = round(n / len(hist), 2)
        chiSum += round(((frecObt - frecEsp) ** 2) / frecEsp, 2)

    return chi2.ppf(0.95, df=len(hist) - 1) > chiSum


# Retorna si los números ingresados pasan una prueba de KS
def testKS(randoms):
    aceptation = 0.95
    n = len(randoms)

    hist = np.histogram(randoms)[0]
    difs = []
    pEsp = n / len(hist)
    pEspAux = pEsp
    fAcum = hist[0]
    for i in range(len(hist)):
        if i != 0:
            pEsp += pEspAux
            fAcum += hist[i]
        difs.append(abs((fAcum / n) - (pEsp / n)))
    dmax = max(difs)
    if n <= 50:
        dmaxp = kstwo.ppf(aceptation, n)
    else:
        dmaxp = 1.3581 / np.sqrt(n)
    return dmax < dmaxp


# Retorna si los números ingresados pasan una prueba de poker
def testPoker(randoms):
    return requests.post('https://dcb-node-deploy-poker.herokuapp.com/pokertest', json={"listRi": randoms}).json()[
        "isOk"]


# Retorna si los números ingresados pasan todas las pruebas
def testAll(randoms):
    return testMedia(randoms) & testVarianza(randoms) & testChi2(randoms) & testKS(randoms) & testPoker(randoms)


# Calcula la media de una lista de números ingresados
def media(ri):
    return sum(ri) / len(ri)

import numpy as np
import base64
from io import BytesIO
from matplotlib.figure import Figure
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import requests
from sympy import *
from generateRandom import congruenciaLineal
from test import testAll

# Se inicializa el modulo Flask
app = Flask(__name__)
# Se inicializan los CORS para evitar problemas al momento de hacer peticiones al backend

CORS(app, support_credentials=True)


# Petición para comprobar la conexión del servidor
@app.route('/ping', methods=['GET'])
@cross_origin(supports_credentials=True)
def ping():
    return jsonify({'response': 'pong!'})


@app.route('/area', methods=['POST'])
@cross_origin(supports_credentials=True)
def getArea():
    integral = {
        "func": request.json["func"],
        "max": request.json["max"],
        "min": request.json["min"],
        "iterations": request.json["n"],
        "varint": request.json["varint"]
    }
    res = area(integral["func"], integral["min"], integral["max"], integral["iterations"], integral["varint"])
    return jsonify(res)


def area(f, a, b, N, varint):
    integr = str(integral(f, varint,
                          a, b))
    data = {
        "func": integr
    }
    if integr != "nan":
        try:
            resIntegr = \
                requests.post('https://gentle-island-67610.herokuapp.com/montecarlo/resolve',
                              json={"data": data}).json()[
                    "res"]
        except:
            resIntegr = integr
    else:
        resIntegr = \
            requests.post('https://gentle-island-67610.herokuapp.com/montecarlo/resolve', json={"data": data}).json()[
                "res"]

    if a == b:
        x = np.arange(a - 1, b + 1, 0.1)
        data = {
            "x": x.tolist(),
            "func": f,
            "varinc": varint
        }
        y = requests.post('https://gentle-island-67610.herokuapp.com/montecarlo/func', json={"data": data}).json()["y"]
        res = 0
        x_rand = None
        y_rand = None
        ind_debajo_positive = None
        ind_debajo_negative = None
        ind_encima = None
        debajo_neg = 0
        debajo_pos = 0
        area_rect = 0

    else:
        if a < b:
            x = np.arange(a, b, 0.01)
        else:
            x = np.arange(b, a, 0.01)

        data = {
            "x": x.tolist(),
            "func": f,
            "varinc": varint
        }
        y = requests.post('https://gentle-island-67610.herokuapp.com/montecarlo/func', json={"data": data}).json()["y"]
        f_max = max(y)
        f_min = min(y)
        randoms = generateRandoms(N)
        x_rand = a + randoms * (b - a)
        data = {
            "x": x_rand.tolist(),
            "func": f,
            "varinc": varint
        }
        f_x_rand = \
            requests.post('https://gentle-island-67610.herokuapp.com/montecarlo/func', json={"data": data}).json()["y"]

        if (f_max >= 0) & (f_min >= 0):
            y_rand = generateRandoms(N) * f_max
            ind_debajo_positive = np.where(y_rand < f_x_rand)
            ind_debajo_negative = None
            ind_encima = np.where(y_rand >= f_x_rand)
            area_rect = f_max * (b - a)
            debajo_neg = 0
            debajo_pos = len(ind_debajo_positive[0])
            res = area_rect * debajo_pos / N

        elif (f_max <= 0) & (f_min <= 0):

            y_rand = generateRandoms(N) * f_min
            ind_debajo_positive = None
            ind_debajo_negative = np.where(y_rand > f_x_rand)
            ind_encima = np.where(y_rand <= f_x_rand)
            area_rect = f_min * (b - a)
            debajo_neg = len(ind_debajo_negative[0])
            debajo_pos = 0
            res = area_rect * debajo_neg / N

        else:

            y_rand = f_min + generateRandoms(N) * (f_max - f_min)
            ind_debajo_positive = np.where((y_rand < f_x_rand) & (y_rand > 0))
            ind_debajo_negative = np.where((y_rand > f_x_rand) & (y_rand < 0))
            ind_encima = np.where(((y_rand <= f_x_rand) & (y_rand < 0)) | ((y_rand >= f_x_rand) & (y_rand > 0)))
            area_rect = (f_max - f_min) * (b - a)
            debajo_neg = len(ind_debajo_negative[0])
            debajo_pos = len(ind_debajo_positive[0])
            debajo_rest = debajo_pos - debajo_neg
            res = area_rect * debajo_rest / N

    return response_integral(res, img(x=x, y=y, x_rand=x_rand, y_rand=y_rand, ind_debajo_positive=ind_debajo_positive,
                                      ind_debajo_negative=ind_debajo_negative,
                                      ind_encima=ind_encima), debajo_neg=debajo_neg, debajo_pos=debajo_pos,
                             area_rect=area_rect, integrate_real=resIntegr)


def generateRandoms(n):
    randoms = congruenciaLineal(n)
    while testAll(randoms) == false:
        randoms = congruenciaLineal(n)
    return np.array(randoms)


def img(x, y, x_rand, y_rand, ind_debajo_positive, ind_debajo_negative, ind_encima):
    fig = Figure()
    ax = fig.subplots()
    ax.plot(x, y, color="blue")
    if ind_debajo_positive is not None:
        ax.scatter(x_rand[ind_debajo_positive], y_rand[ind_debajo_positive], color="green")
    if ind_debajo_negative is not None:
        ax.scatter(x_rand[ind_debajo_negative], y_rand[ind_debajo_negative], color="red")
    if ind_encima is not None:
        ax.scatter(x_rand[ind_encima], y_rand[ind_encima], color="violet")

    buf = BytesIO()
    fig.savefig(buf, format="png")

    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data


def integral(f, varint, a, b):
    x = Symbol(varint)
    return integrate(f, (x, a, b))


def media(ri):
    return sum(ri) / len(ri)


def response_integral(res, img, debajo_neg, debajo_pos, area_rect, integrate_real):
    response = {"res": res,
                "img": img,
                "debajo_negative": debajo_neg, "debajo_positive": debajo_pos,
                "area_rect": area_rect, "integrate_real": integrate_real}

    return response


# Inica el servicio
if __name__ == '__main__':
    app.run(debug=True, port=5000)

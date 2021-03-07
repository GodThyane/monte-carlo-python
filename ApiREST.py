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


# Petición que dado los datos de la funcion a integrar,
# retorna el resultado mediante montecarlo, la imagen de la función,
# la cantidad de números que están bajo la curva, el área del rectángulo formado y el resultado exacto
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


# Retorna el resultado mediante montecarlo, la imagen de la función,
# la cantidad de números que están bajo la curva, el área del rectángulo formado y el resultado exacto
def area(f, a, b, N, varint):
    # Guarda el valor exacto de la integral
    integr = str(integral(f, varint,
                          a, b))
    data = {
        "func": integr
    }
    # Si la integral es errónea, habrá un error en la petición 'post', si no,
    # se intentará dado el resultado, resolver el resultado con la petición post
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
    # Si los límites son iguales, se formarán los 'x' entre a y b restados y sumados con 1
    # a = 10, b = 10: 9.1, 9.2 .... 10.8, 10.9
    if a == b:
        # Crea una lista de números entre a y b con decimales de 0.1
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
        # Si 'a' es menor que 'b', se guarda en 'x' números desde 'a' hasta 'b' con decimales de 0.01
        if a < b:
            x = np.arange(a, b, 0.01)
        # Si 'b' es menor que 'a', se guarda en 'x' números desde 'b' hasta 'a' con decimales de 0.01
        else:
            x = np.arange(b, a, 0.01)

        data = {
            "x": x.tolist(),
            "func": f,
            "varinc": varint
        }
        # En 'y' se guardan los resultados de la función, dado una lista de 'x' generados
        y = requests.post('https://gentle-island-67610.herokuapp.com/montecarlo/func', json={"data": data}).json()["y"]
        # Se guarda el valor máximo que se halle en y
        f_max = max(y)
        # Se guarda el valor mínimo que se halle en y
        f_min = min(y)
        # Guarda 'n' números pseudoaleatorios
        randoms = generateRandoms(N)
        # Normaliza la lista de números pseudoaleatorios dado 'a' y 'b'
        x_rand = a + randoms * (b - a)
        data = {
            "x": x_rand.tolist(),
            "func": f,
            "varinc": varint
        }
        # En 'f_x_rand' se guardan los resultados de la función, dado una lista de 'x'
        f_x_rand = \
            requests.post('https://gentle-island-67610.herokuapp.com/montecarlo/func', json={"data": data}).json()["y"]

        # Si el valor máximo y el valor mínimo de 'y' es mayor a 0,
        # solo se tiene en cuenta el valor máximo, y se toma f_min como 0
        if (f_max >= 0) & (f_min >= 0):
            # Genera 'n' números pseudoaleatorios entre 0 y el valor máximo
            y_rand = generateRandoms(N) * f_max
            # Guarda la cantidad de números de 'y_rand' que estén por debajo de 'f_x_rand'
            ind_debajo_positive = np.where(y_rand < f_x_rand)
            ind_debajo_negative = None
            # Guarda la cantidad de números de 'y_rand' que estén por encima de 'f_x_rand'
            ind_encima = np.where(y_rand >= f_x_rand)
            # Guarda el área del rectángulo formado, dado los límites y el valor máximo.
            area_rect = f_max * (b - a)
            debajo_neg = 0
            debajo_pos = len(ind_debajo_positive[0])
            # Guarda el resultado de la integral, dado el área del rectángulo,
            # la cantidad de números que están bajo la función y la cantidad de números pseudoaleatorios generados
            res = area_rect * debajo_pos / N

        # Si el valor máximo y el valor mínimo de 'y' es menor a 0,
        # solo se tiene en cuenta el valor mínimo, y se toma f_max como 0
        elif (f_max <= 0) & (f_min <= 0):
            # Genera 'n' números pseudoaleatorios entre el valor mínimo y 0
            y_rand = generateRandoms(N) * f_min
            ind_debajo_positive = None
            # Guarda la cantidad de números de 'y_rand' que estén por debajo de 'f_x_rand' negativo
            ind_debajo_negative = np.where(y_rand > f_x_rand)
            # Guarda la cantidad de números de 'y_rand' que estén por encima de 'f_x_rand' negativo
            ind_encima = np.where(y_rand <= f_x_rand)
            # Guarda el área del rectángulo formado, dado los límites y el valor mínimo.
            area_rect = f_min * (b - a)
            debajo_neg = len(ind_debajo_negative[0])
            debajo_pos = 0
            # Guarda el resultado de la integral, dado el área del rectángulo,
            # la cantidad de números que están bajo la función negativa y la cantidad
            # de números pseudoaleatorios generados
            res = area_rect * debajo_neg / N

        # Si el valor máximo es mayor a 0 y el valor mínimo de 'y' es menor a 0,
        # Se tienen en cuenta ambos.
        else:
            # Genera 'n' números pseudoaleatorios entre el valor mínimo y el valor máximo
            y_rand = f_min + generateRandoms(N) * (f_max - f_min)
            # Guarda la cantidad de números de 'y_rand' que estén por debajo de 'f_x_rand' positivo
            ind_debajo_positive = np.where((y_rand < f_x_rand) & (y_rand > 0))
            # Guarda la cantidad de números de 'y_rand' que estén por debajo de 'f_x_rand' negativo
            ind_debajo_negative = np.where((y_rand > f_x_rand) & (y_rand < 0))
            # Guarda la cantidad de números de 'y_rand' que estén por encima de 'f_x_rand' negativo o positivo
            ind_encima = np.where(((y_rand <= f_x_rand) & (y_rand < 0)) | ((y_rand >= f_x_rand) & (y_rand > 0)))
            # Guarda el área del rectángulo formado, dado los límites, el valor mínimo y el valor máximo.
            area_rect = (f_max - f_min) * (b - a)
            debajo_neg = len(ind_debajo_negative[0])
            debajo_pos = len(ind_debajo_positive[0])
            debajo_rest = debajo_pos - debajo_neg
            # Guarda el resultado de la integral, dado el área del rectángulo,
            # la cantidad de números que están bajo la función negativa-positiva y la cantidad
            # de números pseudoaleatorios generados
            res = area_rect * debajo_rest / N

    return response_integral(res, img(x=x, y=y, x_rand=x_rand, y_rand=y_rand, ind_debajo_positive=ind_debajo_positive,
                                      ind_debajo_negative=ind_debajo_negative,
                                      ind_encima=ind_encima), debajo_neg=debajo_neg, debajo_pos=debajo_pos,
                             area_rect=area_rect, integrate_real=resIntegr)


# Retorna 'n' cantidad de números pseudoaleatorios (siempre y cuando pasen todas las pruebas)
# utilizando el método de congruencia lineal
def generateRandoms(n):
    randoms = congruenciaLineal(n)
    while testAll(randoms) == false:
        randoms = congruenciaLineal(n)
    return np.array(randoms)


# Retorna la imagen de la función y los puntos debajo, encima de dicha función
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


# Retorna el valor exacto de la integral dada, recibe la función, variable de integración y los límites.
def integral(f, varint, a, b):
    x = Symbol(varint)
    return integrate(f, (x, a, b))


# Retorna un objeto con la respuesta de la integral, imágen,
# cantidad de números bajo y encima de la función, el área del rectángulo y el valor exacto de la integral
def response_integral(res, img, debajo_neg, debajo_pos, area_rect, integrate_real):
    response = {"res": res,
                "img": img,
                "debajo_negative": debajo_neg, "debajo_positive": debajo_pos,
                "area_rect": area_rect, "integrate_real": integrate_real}

    return response


# Inica el servicio
if __name__ == '__main__':
    app.run(debug=True, port=5000)

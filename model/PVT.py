#Funciones para calcular el PVT
#%% Funcion para Solubilidad del gas
# Correlación de Standing (1947) para la solubilidad del gas Rs

def rs_standing(api, sg, p, t_f):
        """
        Calcula la solubilidad del gas (Rs) usando la correlación de Standing (1947).

        Parámetros:
        api : float,  gravedad API del petróleo
        sg  : float, gravedad específica del gas en solucion
        p   : float,  presión del sistema (psi)
        t_f : float,  temperatura del sistema (F)

        Retorna:
        rs : float, solubilidad del gas (scf/bbl)
        """

        try:
            # Cálculo del exponente x
            x = 0.0125 * api - 0.00091 * t_f

            # Ecuación de Standing
            rs = sg * (((p / 18.2) + 1.4) * (10 ** x)) ** 1.2048

            return rs

        except Exception as e:
            print("Error calculando Rs (Standing, 1947):", e)
            return None
#%% Funcion para Factor volumetrico del petroleo
#Correlacion de Standing (1981) para el factor volumetrico del petroleo
def bo_standing(rs, sg, sgo, t_f):
    """"
    Calcular el factor volumetrico del petroleo (Bo) usando la correlacion de Standing (1981)

    Parametros:
    rs: float, solubilidad del gas (scf/bbl)
    sg: float, gravedad específica del gas en solucion
    sgo: float, gravedad específica del gas a condiciones de tanque
    t_f: float, temperatura del sistema (F)

    Retorna:
    bo: float, volumetrico del petroleo (bbl/STB)
    """
    try:
        # Ecuación de Standing
        bo = 0.9759 + 0.000120 * ((rs * ((sg/sgo) ** 0.5) + 1.25 * t_f) ** 1.2)
        return bo

    except Exception as e:
        print("Error calculando Bo (Standing, 1981):", e)
        return None

#Correlacion de Vasquez-Beggs (1980) para el factor volumetrico del petroleo
#ya que tiene logaritmos, importamos la libreria math
import math
def bo_vasbeg (rs, api, sgg, t_f, psep, tsep):
    """"
    Calcular el factor volumetrico del petroleo (Bo) usando la correlacion de Vasquez/Beggs

    Parametros:
    rs: float, solubilidad del gas (scf/bbl)
    api: float, gravedad API del petroleo
    sgg: float, gravedad especifica del gas
    t_f: float, temperatura del sistema (F)
    psep: float, presion del separador (psi)
    tsep: float, temperatura del separador (F)

    Retorna:
    bo: float, volumetrico del petroleo (bbl/STB)
    """
    try:
        # Gas en solución corregido por condiciones de separador
        if psep <= 0:
            # evitamos log de valores no validos
            return None
        ygs = sgg * (1.0 + 5.912e-5 * api * tsep * math.log(psep / 114.7))
        if api >= 30>:
            C1, C2, C3= 4.677e-4, 1.751e-5, -1.811e-8
        else:
            C1, C2, C3 = 4.670e-4, 1.100e-5, 1.337E-9

        bo = 1.0 + (C1 * rs) + (t_f - 60) * (api/ygs) * (C2 + (C3 * rs))
        return bo
    except Exception as e:
        print("Error calculando Bo (Vasquez/Beggs):", e)
        return None



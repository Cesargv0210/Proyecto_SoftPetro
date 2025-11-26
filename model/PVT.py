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
    bo: float, factor volumetrico del petroleo (bbl/STB)
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
    bo: float, factor volumetrico del petroleo (bbl/STB)
    """
    try:
        # Gas en solución corregido por condiciones de separador
        if psep <= 0:
            # evitamos log de valores no validos
            return None
        ygs = sgg * (1.0 + 5.912e-5 * api * tsep * math.log(psep / 114.7))
        if api >= 30:
            C1, C2, C3= 4.677e-4, 1.751e-5, -1.811e-8
        else:
            C1, C2, C3 = 4.670e-4, 1.100e-5, 1.337E-9

        bo = 1.0 + (C1 * rs) + (t_f - 60) * (api/ygs) * (C2 + (C3 * rs))
        return bo
    except Exception as e:
        print("Error calculando Bo (Vasquez/Beggs):", e)
        return None
#%% Funcion para la comprensibilidad isotermica del petroleo
#Correlacion de Petrosky (1993) para la compresibilidad isotermica del petroleo
def co_petrosk (rsb, sgg, P, t_f, api):
    """
    Calcular la comprensibilidad isotermica del petroleo (co) usando la correlacion Petrosky (1993)

    Parametros:
    rsb: float, solubilidad del gas en el puntoi de burbuja, (scf/bbl)
    sgg: float, gravedad especifica del gas
    api: float, gravedad API del petroleo
    t_f: float, temperatura del sistema (F)
    P: float, presion arriba de la presion del punto de burbuja, (psia)

    Retorna:
    co: float, Coeficiente de compresibilidad del petróleo (psia⁻¹)
    """
    try:
        # Ecuación de Petrosky–Farshad (1993)
        co = (
                1.705e-7 *
                (rsb ** 0.69357) *
                (sgg ** 0.1885) *
                (api ** 0.3272) *
                (t_f ** 0.6729) *
                (P ** -0.5906)
        )

        return co

    except Exception as e:
        print("Error calculando Co (Petrosky–Farshad, 1993):", e)
        return None


#Correlacion de Vasquez-Beggs (1980) para la comprensibilidad isotermica del petroleo
import math
def co_vasquez_beggs(Rsb, y_g, api, t_f, p, psep, tsep):
    """
    Calcular el coeficiente de compresibilidad del petróleo (Co)
    usando la correlación de Vasquez–Beggs (1980).

    Parámetros:

    Rsb: float, Solubilidad del gas en el punto de burbuja (scf/STB)
    y_g : float
        Gravedad específica del gas
    api : float
        Gravedad API del petróleo
    t_f : float
        Temperatura del sistema (°F)
    p : float
        Presión arriba de la presión del punto de burbuja (psia)
    psep : float
        Presión del separador (psia)
    tsep : float
        Temperatura del separador (°F)

    Retorna:
    --------
    co : float
        Coeficiente de compresibilidad del petróleo (psia⁻¹)
    """

    try:
        # Evitar logaritmos inválidos
        if psep <= 0:
            return None

        # Cálculo del gas específico corregido por condiciones del separador
        y_gc = y_g * (1 + (5.912e-5) * api * tsep * math.log(psep / 114.7))

        # Ecuación de Vasquez–Beggs (1980)
        numerador = -1433 + (5 * Rsb) + (17.2 * t_f) - (1180 * y_gc) + (12.61 * api)
        denominador = (1e5 * p)

        co = numerador / denominador

        return co

    except Exception as e:
        print("Error calculando Co (Vasquez–Beggs, 1980):", e)
        return None

#%% Funcion para la densiada del petroleo
#Correlacion de Standing (1947) para la densidad del petroleo po
def ro_standing(Rs, y_g, y_o, t_f):
    """
    Calcular la densidad del petróleo (ρo) para petróleo saturado
    usando la correlación de Standing (1947).

    Parámetros:
    ----------
    Rs : float
        Solubilidad del gas (scf/STB)
    y_g : float
        Gravedad específica del gas
    y_o : float
        Gravedad específica del petróleo a condiciones de tanque
    t_f : float
        Temperatura del sistema (°F)

    Retorna:
    --------
    ro : float
        Densidad del petróleo ρo (lb/ft³)
    """

    try:
        # Factor volumétrico del petróleo (Bo) según Standing
        term = Rs * (y_g / y_o) ** 0.25 + 1.25 * t_f
        Bo = 0.972 + 0.000147 * (term ** 1.175)

        # Densidad del petróleo saturado
        ro = (62.4 * y_o + 0.0136 * Rs * y_g) / Bo

        return ro

    except Exception as e:
        print("Error calculando ρo (Standing, 1947):", e)
        return None

#%% Funcion para la viscosidad del petroleo uo
#Correlacion de Beggs/Robinson (1975) para la viscosidad del petroleo saturado
import math

def mu_beggs_robinson(api, t_f, Rs=None):
    """
    Calcula la viscosidad del petróleo muerto (μ_od) o saturado (μ_ob)
    usando las correlaciones de Beggs–Robinson (1975).

    Si Rs es None:
        → Retorna μ_od (petróleo muerto).
    Si Rs tiene un valor:
        → Calcula internamente μ_od y retorna μ_ob (petróleo saturado).

    Parámetros:
    ----------
    api : float
        Gravedad API del petróleo.
    t_f : float
        Temperatura del sistema (°F).
    Rs : float, opcional
        Solubilidad del gas en solución (scf/STB).
        - Si no se proporciona, solo se calcula μ_od.
        - Si se proporciona, se calcula μ_ob.

    Retorna:
    --------
    mu : float
        Viscosidad según el caso:
        - μ_od si Rs=None
        - μ_ob si Rs se proporciona
    """

    try:
        # ================================
        # 1) VISCOSIDAD DEL PETRÓLEO MUERTO (μ_od)
        # ================================
        x = 10 ** ((3.0324 - 0.02023 * api) * (t_f ** -1.163))
        mu_od = (10 ** x) - 1.0

        # Si no hay Rs, devolvemos μ_od directamente
        if Rs is None:
            return mu_od

        # ================================
        # 2) VISCOSIDAD DEL PETRÓLEO SATURADO (μ_ob)
        # ================================
        a = 10.715 * (Rs + 100) ** (-0.515)
        b = 5.44 * (Rs + 150) ** (-0.338)

        mu_ob = a * (mu_od ** b)

        return mu_ob

    except Exception as e:
        print("Error calculando viscosidad (Beggs–Robinson, 1975):", e)
        return None

#Correlacion usando Vasquez/Beggs (1975) para la viscocidad del petroleo subsaturado
import math

def muo_vasquez_beggs(mu_ob, p, pb):
    """
    Calcular la viscosidad del petróleo subsaturado (μo)
    usando la correlación de Vasquez–Beggs (1975).

    Parámetros:
    ----------
    mu_ob : float
        Viscosidad del petróleo saturado (cp).
    p : float
        Presión del sistema (psia).
    pb : float
        Presión de punto de burbuja (psia).

    Retorna:
    --------
    mu_o : float
        Viscosidad del petróleo subsaturado (cp).
    """

    try:
        # Por definición, la correlación aplica para petróleo subsaturado: P > Pb.
        # Si P <= Pb, devolvemos la viscosidad saturada (μob) como aproximación.
        if p <= 0 or pb <= 0:
            return None
        if p <= pb:
            return mu_ob

        # Cálculo del exponente m según Vasquez–Beggs (1975)
        m = 2.6 * (pb ** 1.187) * math.exp(-11.513 - 8.98e-5 * pb)

        # Viscosidad del petróleo subsaturado
        mu_o = mu_ob * (p / pb) ** m

        return mu_o

    except Exception as e:
        print("Error calculando μo (Vasquez–Beggs, 1975):", e)
        return None

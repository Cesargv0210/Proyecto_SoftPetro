#%% Importar librerías
import xlwings as xw
import numpy as np

# Importar tus funciones del modelo PVT
from model.PVT import (
    rs_standing,
    bo_vasbeg,
    co_vasquez_beggs,
)

#%% Parámetros base (establecidos)
pb = 3970.0      # psia
rsb = 1124.0     # scf/stb
api = 38.982
sg_gas = 0.65
pr = 4409.0      # psia
tr = 140.0       # °F
psep = 100.0     # psia
tsep = 120.0     # °F

#%% Abrir el archivo Excel existente
wb = xw.Book("PVT_App.xlsm")

# Nombre de la hoja de prueba
sheet = wb.sheets["Summary"]

#%% 1) Prueba mínima: escribir y leer una celda
sheet["C3"].value = "Prueba xlwings OK"
valor_c3 = sheet["C3"].value
print("Valor en C3 (de Excel):", valor_c3)

#%% 2) Escribir los datos base en algunas celdas
sheet["A5"].value = "pb (psia)"
sheet["B5"].value = pb

sheet["A6"].value = "rsb (scf/stb)"
sheet["B6"].value = rsb

sheet["A7"].value = "API"
sheet["B7"].value = api

sheet["A8"].value = "sg_gas"
sheet["B8"].value = sg_gas

sheet["A9"].value = "Pr (psia)"
sheet["B9"].value = pr

sheet["A10"].value = "T (F)"
sheet["B10"].value = tr

#%% 3) Calcular Rs, Bo y Co para la presión de yacimiento (Pr)

Rs_pr = rs_standing(api, sg_gas, pr, tr)
Bo_pr = bo_vasbeg(Rs_pr, api, sg_gas, tr, psep, tsep)
Co_pr = co_vasquez_beggs(rsb, sg_gas, api, tr, pr, psep, tsep)

print("Rs(Pr)  =", Rs_pr)
print("Bo(Pr)  =", Bo_pr)
print("Co(Pr)  =", Co_pr)

# Escribir estos resultados en el Excel
sheet["D5"].value = "Resultados en Pr"
sheet["C6"].value = "Rs (scf/stb)"
sheet["D6"].value = Rs_pr

sheet["C7"].value = "Bo (rb/stb)"
sheet["D7"].value = Bo_pr

sheet["C8"].value = "Co (1/psia)"
sheet["D8"].value = Co_pr

#%% 4) Ejemplo con un arreglo de NumPy

# Arreglo de presiones de prueba
P_array = np.array([pr, 4000.0, 3000.0, 2000.0, 1000.0, 14.7])

# Escribir el arreglo en una columna
sheet["F4"].value = "P (psia) - array prueba"
sheet["F5"].options(transpose=True).value = P_array

# Leer de vuelta ese rango como lista de Python
P_from_excel = sheet["F5:F10"].value
print("Arreglo P leído desde Excel:", P_from_excel)
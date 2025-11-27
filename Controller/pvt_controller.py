import os
import sys

import xlwings as xw
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# Ajustar ruta para importar model.PVT
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from model.PVT import (
    rs_standing,
    bo_vasbeg,
    co_vasquez_beggs,
    ro_standing,
    mu_beggs_robinson,
    muo_vasquez_beggs,
)

SUMMARY = "Summary"
RESULTS = "Results"


def main():
    wb = xw.Book.caller()
    sh_sum = wb.sheets[SUMMARY]
    sh_res = wb.sheets[RESULTS]

    # =========================
    # 1) LEER INPUTS DESDE SUMMARY
    # =========================
    pb = float(sh_sum["B5"].value)      # presión de burbuja
    rsb = float(sh_sum["B6"].value)     # Rs en pb
    api = float(sh_sum["B7"].value)
    sg_gas = float(sh_sum["B8"].value)
    pr = float(sh_sum["B9"].value)      # presión actual del yacimiento
    tr = float(sh_sum["B10"].value)     # temperatura (°F)

    seed = int(sh_sum["B12"].value)     # semilla para NumPy
    n_points = int(sh_sum["B13"].value) # número de realizaciones

    np.random.seed(seed)

    # Valores adicionales necesarios por las correlaciones
    sgo = 0.82       # gravedad específica del petróleo a tanque (supuesto)
    psep = 100.0     # psia
    tsep = 120.0     # °F

    # =========================
    # 2) AJUSTE DE Rs PARA QUE Rs(pb) = Rsb
    # =========================
    rs_pb_corr = rs_standing(api, sg_gas, pb, tr)
    if rs_pb_corr not in (None, 0):
        scale_rs = rsb / rs_pb_corr
    else:
        scale_rs = 1.0

    # =========================
    # 3) CÁLCULO DETERMINÍSTICO EN Pr
    # =========================
    if pr >= pb:
        rs_pr = rsb
    else:
        rs_pr = scale_rs * rs_standing(api, sg_gas, pr, tr)

    bo_pr = bo_vasbeg(rs_pr, api, sg_gas, tr, psep, tsep)
    co_pr = co_vasquez_beggs(rsb, sg_gas, api, tr, pr, psep, tsep)
    rho_pr = ro_standing(rs_pr, sg_gas, sgo, tr)
    mu_ob_pr = mu_beggs_robinson(api, tr, Rs=rs_pr)
    mu_o_pr = muo_vasquez_beggs(mu_ob_pr, pr, pb)

    # Escribir resultados determinísticos en Summary
    sh_sum["C5"].value = "Rs(Pr) [scf/stb]"
    sh_sum["C6"].value = "Bo(Pr) [rb/stb]"
    sh_sum["C7"].value = "Co(Pr) [1/psia]"
    sh_sum["C8"].value = "mu_o(Pr) [cp]"
    sh_sum["C9"].value = "rho(Pr) [lb/ft3]"

    sh_sum["D5"].value = rs_pr
    sh_sum["D6"].value = bo_pr
    sh_sum["D7"].value = co_pr
    sh_sum["D8"].value = mu_o_pr
    sh_sum["D9"].value = rho_pr

    # =========================
    # 4) GENERAR PRESIONES ALEATORIAS
    # =========================
    # Valores aleatorios entre ~atmosférica y la presión Pr
    P = np.random.uniform(
        low=max(14.7, pb * 0.05),
        high=pr,
        size=n_points,
    )
    T = np.full_like(P, tr, dtype=float)

    # =========================
    # 5) PRE-CÁLCULOS EN EL PUNTO DE BURBUJA
    # =========================
    # Bo y rho en pb (para marcar el punto en los gráficos)
    bob = bo_vasbeg(rsb, api, sg_gas, tr, psep, tsep)
    rho_pb = ro_standing(rsb, sg_gas, sgo, tr)
    # μo en pb: en Vasquez–Beggs, μo(pb) = μ_ob
    mu_ob_pb = mu_beggs_robinson(api, tr, Rs=rsb)

    # =========================
    # 6) CÁLCULO PVT PARA CADA PRESIÓN
    # =========================
    Rs_list = []
    Bo_list = []
    Co_list = []
    Rho_list = []
    Mu_o_list = []

    for p in P:
        # ---- Rs saturado / subsaturado con ajuste ----
        if p >= pb:
            rs_p = rsb
        else:
            rs_p = scale_rs * rs_standing(api, sg_gas, p, tr)
        Rs_list.append(rs_p)

        # ---- Co (Vasquez–Beggs) ----
        co_p = co_vasquez_beggs(rsb, sg_gas, api, tr, p, psep, tsep)
        Co_list.append(co_p)

        # ---- Bo usando Bob y compresibilidad ----
        if p >= pb:
            bo_p = bob * np.exp(-co_p * (p - pb))
        else:
            bo_p = bo_vasbeg(rs_p, api, sg_gas, tr, psep, tsep)
        Bo_list.append(bo_p)

        # ---- Densidad ρo ----
        if p >= pb:
            rho_p = rho_pb * (1 + co_p * (p - pb))
        else:
            rho_p = ro_standing(rs_p, sg_gas, sgo, tr)
        Rho_list.append(rho_p)

        # ---- Viscosidad μo ----
        mu_ob_p = mu_beggs_robinson(api, tr, Rs=rs_p)
        mu_o_p = muo_vasquez_beggs(mu_ob_p, p, pb)
        Mu_o_list.append(mu_o_p)

    # =========================
    # 7) DATAFRAME Y ESCRITURA EN RESULTS
    # =========================
    df = pd.DataFrame(
        {
            "P (psia)": P,
            "T (F)": T,
            "Rs (scf/stb)": Rs_list,
            "Bo (rb/stb)": Bo_list,
            "Co (1/psia)": Co_list,
            "rho (lb/ft3)": Rho_list,
            "mu_o (cp)": Mu_o_list,
        }
    )

    sh_res["A1"].options(pd.DataFrame, index=False, expand="table").value = df

    # =========================
    # 8) GRÁFICOS CON LÍNEA SEGMENTADA EN PB
    # =========================
    sns.set_style("whitegrid")

    # Para que la línea se vea ordenada, usamos datos ordenados SOLO para la línea
    P_arr = np.array(P)
    Rs_arr = np.array(Rs_list)
    Bo_arr = np.array(Bo_list)
    Rho_arr = np.array(Rho_list)
    Mu_arr = np.array(Mu_o_list)

    sort_idx = np.argsort(P_arr)
    P_sorted = P_arr[sort_idx]
    Rs_sorted = Rs_arr[sort_idx]
    Bo_sorted = Bo_arr[sort_idx]
    Rho_sorted = Rho_arr[sort_idx]
    Mu_sorted = Mu_arr[sort_idx]

    # ---- 8.1 Rs vs P ----
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.scatter(P_arr, Rs_arr, color="blue", s=20, label="Datos")
    ax1.plot(P_sorted, Rs_sorted, color="blue", linewidth=1, label="Tendencia")

    # Punto en pb
    ax1.scatter(pb, rsb, color="red", s=70, zorder=10, label="Punto de burbuja (pb)")

    # Línea vertical segmentada
    ax1.axvline(pb, color="red", linestyle="--", linewidth=1.5, label=f"pb = {pb} psia")

    ax1.set_title("Solubilidad del Gas (Rs) vs Presión")
    ax1.set_xlabel("P (psia)")
    ax1.set_ylabel("Rs (scf/stb)")
    ax1.grid(True)
    ax1.legend()

    # Insertar en Excel
    for pic in sh_sum.pictures:
        if pic.name == "Rs_vs_P":
            pic.delete()
    sh_sum.pictures.add(fig1, name="Rs_vs_P", update=True,
                        left=sh_sum.range("H2").left,
                        top=sh_sum.range("H2").top)
    plt.close(fig1)

    # ---- 8.2 Bo vs P ----
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.scatter(P_arr, Bo_arr, color="green", s=20, label="Datos")
    ax2.plot(P_sorted, Bo_sorted, color="green", linewidth=1, label="Tendencia")

    # Punto en pb
    ax2.scatter(pb, bob, color="red", s=70, zorder=10, label="Punto de burbuja (pb)")

    # Línea vertical segmentada
    ax2.axvline(pb, color="red", linestyle="--", linewidth=1.5, label=f"pb = {pb} psia")

    ax2.set_title("Factor Volumétrico del Petróleo (Bo) vs Presión")
    ax2.set_xlabel("P (psia)")
    ax2.set_ylabel("Bo (rb/stb)")
    ax2.grid(True)
    ax2.legend()

    for pic in sh_sum.pictures:
        if pic.name == "Bo_vs_P":
            pic.delete()
    sh_sum.pictures.add(fig2, name="Bo_vs_P", update=True,
                        left=sh_sum.range("H20").left,
                        top=sh_sum.range("H20").top)
    plt.close(fig2)

    # ---- 8.3 Densidad vs P ----
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    ax3.scatter(P_arr, Rho_arr, color="orange", s=20, label="Datos")
    ax3.plot(P_sorted, Rho_sorted, color="orange", linewidth=1, label="Tendencia")

    ax3.scatter(pb, rho_pb, color="red", s=70, zorder=10, label="Punto de burbuja (pb)")

    ax3.axvline(pb, color="red", linestyle="--", linewidth=1.5, label=f"pb = {pb} psia")

    ax3.set_title("Densidad del Petróleo (ρo) vs Presión")
    ax3.set_xlabel("P (psia)")
    ax3.set_ylabel("ρo (lb/ft³)")
    ax3.grid(True)
    ax3.legend()

    for pic in sh_sum.pictures:
        if pic.name == "Rho_vs_P":
            pic.delete()
    sh_sum.pictures.add(fig3, name="Rho_vs_P", update=True,
                        left=sh_sum.range("H38").left,
                        top=sh_sum.range("H38").top)
    plt.close(fig3)

    # ---- 8.4 Viscosidad vs P ----
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    ax4.scatter(P_arr, Mu_arr, color="purple", s=20, label="Datos")
    ax4.plot(P_sorted, Mu_sorted, color="purple", linewidth=1, label="Tendencia")

    ax4.scatter(pb, mu_ob_pb, color="red", s=70, zorder=10, label="Punto de burbuja (pb)")

    ax4.axvline(pb, color="red", linestyle="--", linewidth=1.5, label=f"pb = {pb} psia")

    ax4.set_title("Viscosidad del Petróleo (μo) vs Presión")
    ax4.set_xlabel("P (psia)")
    ax4.set_ylabel("μo (cp)")
    ax4.grid(True)
    ax4.legend()

    for pic in sh_sum.pictures:
        if pic.name == "Mu_vs_P":
            pic.delete()
    sh_sum.pictures.add(fig4, name="Mu_vs_P", update=True,
                        left=sh_sum.range("H56").left,
                        top=sh_sum.range("H56").top)
    plt.close(fig4)


if __name__ == "__main__":
    # Para probar sin macro (solo si ejecutas este archivo directamente)
    xw.Book("PVT_App.xlsm").set_mock_caller()
    main()

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import xlwings as xw

# =========================
# Ajustar ruta para importar model.PVT
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from model.PVT import (
    rs_standing,
    rs_velarde,
    bo_standing,
    bo_vasbeg,
    co_petrosk,
    co_vasquez_beggs,
    ro_standing,
    ro_subsaturado,
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
    pb = float(sh_sum["B5"].value)      # Presión de burbuja
    rsb = float(sh_sum["B6"].value)     # Rs en Pb
    api = float(sh_sum["B7"].value)
    sg_gas = float(sh_sum["B8"].value)  # γg
    pr = float(sh_sum["B9"].value)      # Presión de referencia
    tr = float(sh_sum["B10"].value)     # Temperatura (°F)

    seed = int(sh_sum["B12"].value)     # Semilla para NumPy
    n_points = int(sh_sum["B13"].value) # Número de realizaciones

    np.random.seed(seed)

    # Valores adicionales para algunas correlaciones
    sgo = 0.82       # gravedad específica del petróleo a tanque (γo)
    psep = 100.0     # psia
    tsep = 120.0     # °F

    # Densidad en el punto de burbuja: ρob
    rho_pb = ro_standing(rsb, sg_gas, sgo, tr)

    # =========================
    # 2) FUNCIÓN AUXILIAR: CÁLCULO PVT EN UNA PRESIÓN P
    # =========================
    def calc_pvt_at_p(p):
        """
        Devuelve: Rs, Bo, Co, rho, mu_o en la presión p,
        usando una correlación para P <= Pb y otra para P > Pb.
        """

        # --- 2.1 Rs ---
        if p <= pb:
            # Debajo de Pb: Standing
            rs_p = rs_standing(api, sg_gas, p, tr)
        else:
            # Encima de Pb: Velarde (como segunda correlación de Rs)
            rs_p = rs_velarde(rsb, sg_gas, sgo, pb, p, tr)

        # --- 2.2 Co (compresibilidad) ---
        if p <= pb:
            # Región saturada: Vasquez–Beggs
            co_p = co_vasquez_beggs(rsb, sg_gas, api, tr, p, psep, tsep)
        else:
            # Región subsaturada: Petrosky–Farshad
            co_p = co_petrosk(rsb, sg_gas, p, tr, api)

        # --- 2.3 Bo (factor volumétrico) ---
        if p <= pb:
            # Debajo de Pb: Standing
            bo_p = bo_standing(rs_p, sg_gas, sgo, tr)
        else:
            # Encima de Pb: Vasquez–Beggs
            bo_p = bo_vasbeg(rs_p, api, sg_gas, tr, psep, tsep)

        # --- 2.4 ρo (densidad del petróleo) ---
        if p <= pb:
            # Saturado: Standing
            rho_p = ro_standing(rs_p, sg_gas, sgo, tr)
        else:
            # Subsaturado: correlación general ρo = ρob * exp(Co * (P - Pb))
            rho_p = ro_subsaturado(rho_pb, co_p, p, pb)

        # --- 2.5 μo (viscosidad del petróleo) ---
        # Primero viscosidad saturada a partir de Rs
        mu_ob_p = mu_beggs_robinson(api, tr, Rs=rs_p)

        if p <= pb:
            # Debajo de Pb: viscosidad saturada (μob)
            mu_o_p = mu_ob_p
        else:
            # Encima de Pb: Vasquez–Beggs para petróleo subsaturado
            mu_o_p = muo_vasquez_beggs(mu_ob_p, p, pb)

        return rs_p, bo_p, co_p, rho_p, mu_o_p

    # =========================
    # 3) CÁLCULO DETERMINÍSTICO EN Pr
    # =========================
    rs_pr, bo_pr, co_pr, rho_pr, mu_o_pr = calc_pvt_at_p(pr)

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
    # Queremos puntos por debajo y por encima de Pb
    p_min = max(14.7, 0.1 * pb)
    p_max = max(pb * 1.2, pr)

    P = np.random.uniform(low=p_min, high=p_max, size=n_points)
    T = np.full_like(P, tr, dtype=float)

    # =========================
    # 5) CALCULAR PVT PARA CADA P
    # =========================
    Rs_list = []
    Bo_list = []
    Co_list = []
    Rho_list = []
    Mu_list = []

    for p in P:
        rs_p, bo_p, co_p, rho_p, mu_o_p = calc_pvt_at_p(p)
        Rs_list.append(rs_p)
        Bo_list.append(bo_p)
        Co_list.append(co_p)
        Rho_list.append(rho_p)
        Mu_list.append(mu_o_p)

    # =========================
    # 6) ESCRIBIR TABLA EN HOJA RESULTS
    # =========================
    df = pd.DataFrame(
        {
            "P (psia)": P,
            "T (F)": T,
            "Rs (scf/stb)": Rs_list,
            "Bo (rb/stb)": Bo_list,
            "Co (1/psia)": Co_list,
            "rho (lb/ft3)": Rho_list,
            "mu_o (cp)": Mu_list,
        }
    )

    sh_res["A1"].options(pd.DataFrame, index=False, expand="table").value = df

    # =========================
    # 7) GRÁFICOS CON LÍNEA SEGMENTADA EN PB Y LEYENDA
    # =========================
    sns.set_style("whitegrid")

    P_arr = np.array(P)
    Rs_arr = np.array(Rs_list)
    Bo_arr = np.array(Bo_list)
    Rho_arr = np.array(Rho_list)
    Mu_arr = np.array(Mu_list)

    sort_idx = np.argsort(P_arr)
    P_sorted = P_arr[sort_idx]
    Rs_sorted = Rs_arr[sort_idx]
    Bo_sorted = Bo_arr[sort_idx]
    Rho_sorted = Rho_arr[sort_idx]
    Mu_sorted = Mu_arr[sort_idx]

    # Punto de burbuja (usando Rsb para el marcador)
    rs_pb = rsb
    bo_pb = bo_standing(rsb, sg_gas, sgo, tr)
    mu_ob_pb = mu_beggs_robinson(api, tr, Rs=rsb)

    # ===== 7.1 Rs vs P =====
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.scatter(P_arr, Rs_arr, color="blue", s=20, label="Datos")
    ax1.plot(P_sorted, Rs_sorted, color="blue", linewidth=1, label="Tendencia")

    ax1.scatter(pb, rs_pb, color="red", s=70, zorder=10, label="Punto de burbuja (pb)")
    ax1.axvline(pb, color="red", linestyle="--", linewidth=1.5, label=f"pb = {pb} psia")

    ax1.set_title("Solubilidad del Gas (Rs) vs Presión")
    ax1.set_xlabel("P (psia)")
    ax1.set_ylabel("Rs (scf/stb)")
    ax1.grid(True)
    ax1.legend()

    for pic in sh_sum.pictures:
        if pic.name == "Rs_vs_P":
            pic.delete()
    sh_sum.pictures.add(
        fig1,
        name="Rs_vs_P",
        update=True,
        left=sh_sum.range("H2").left,
        top=sh_sum.range("H2").top,
    )
    plt.close(fig1)

    # ===== 7.2 Bo vs P =====
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.scatter(P_arr, Bo_arr, color="green", s=20, label="Datos")
    ax2.plot(P_sorted, Bo_sorted, color="green", linewidth=1, label="Tendencia")

    ax2.scatter(pb, bo_pb, color="red", s=70, zorder=10, label="Punto de burbuja (pb)")
    ax2.axvline(pb, color="red", linestyle="--", linewidth=1.5, label=f"pb = {pb} psia")

    ax2.set_title("Factor Volumétrico del Petróleo (Bo) vs Presión")
    ax2.set_xlabel("P (psia)")
    ax2.set_ylabel("Bo (rb/stb)")
    ax2.grid(True)
    ax2.legend()

    for pic in sh_sum.pictures:
        if pic.name == "Bo_vs_P":
            pic.delete()
    sh_sum.pictures.add(
        fig2,
        name="Bo_vs_P",
        update=True,
        left=sh_sum.range("H20").left,
        top=sh_sum.range("H20").top,
    )
    plt.close(fig2)

    # ===== 7.3 ρo vs P =====
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
    sh_sum.pictures.add(
        fig3,
        name="Rho_vs_P",
        update=True,
        left=sh_sum.range("H38").left,
        top=sh_sum.range("H38").top,
    )
    plt.close(fig3)

    # ===== 7.4 μo vs P =====
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
    sh_sum.pictures.add(
        fig4,
        name="Mu_vs_P",
        update=True,
        left=sh_sum.range("H56").left,
        top=sh_sum.range("H56").top,
    )
    plt.close(fig4)


if __name__ == "__main__":
    # Para pruebas directas sin macro
    xw.Book("PVT_App.xlsm").set_mock_caller()
    main()


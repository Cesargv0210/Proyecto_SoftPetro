import os
import sys

import xlwings as xw
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ajustar ruta para importar model.PVT
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
    # 1) Leer inputs desde Summary
    # =========================
    pb = float(sh_sum["B5"].value)
    rsb = float(sh_sum["B6"].value)
    api = float(sh_sum["B7"].value)
    sg_gas = float(sh_sum["B8"].value)
    pr = float(sh_sum["B9"].value)
    tr = float(sh_sum["B10"].value)

    seed = int(sh_sum["B12"].value)
    n_points = int(sh_sum["B13"].value)

    np.random.seed(seed)

    # Valores adicionales necesarios
    sgo = 0.82
    psep = 100.0
    tsep = 120.0

    # =========================
    # 2) Ajuste de Rs para que Rs(pb) = Rsb
    # =========================
    rs_pb_corr = rs_standing(api, sg_gas, pb, tr)
    scale_rs = rsb / rs_pb_corr if rs_pb_corr not in [0, None] else 1.0

    # =========================
    # 3) Valores determinísticos en Pr
    # =========================
    rs_pr = rsb if pr >= pb else scale_rs * rs_standing(api, sg_gas, pr, tr)

    bo_pr = bo_vasbeg(rs_pr, api, sg_gas, tr, psep, tsep)
    co_pr = co_vasquez_beggs(rsb, sg_gas, api, tr, pr, psep, tsep)
    rho_pr = ro_standing(rs_pr, sg_gas, sgo, tr)
    mu_ob_pr = mu_beggs_robinson(api, tr, Rs=rs_pr)
    mu_o_pr = muo_vasquez_beggs(mu_ob_pr, pr, pb)

    # Escribir resultados base
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
    # 4) Generar presiones ALEATORIAS
    #    (lo que se vio en clase)
    # =========================
    P = np.random.uniform(
        low=max(14.7, pb * 0.05),  # límite inferior razonable
        high=pr,
        size=n_points,
    )

    T = np.full_like(P, tr)

    # =========================
    # 5) Precalcular valores en pb
    # =========================
    bob = bo_vasbeg(rsb, api, sg_gas, tr, psep, tsep)
    rho_pb = ro_standing(rsb, sg_gas, sgo, tr)

    # =========================
    # 6) Cálculo punto a punto
    # =========================
    Rs_list = []
    Bo_list = []
    Co_list = []
    Rho_list = []
    Mu_o_list = []

    for p in P:
        # --- Rs ---
        if p >= pb:
            rs_p = rsb
        else:
            rs_p = scale_rs * rs_standing(api, sg_gas, p, tr)
        Rs_list.append(rs_p)

        # --- Co ---
        co_p = co_vasquez_beggs(rsb, sg_gas, api, tr, p, psep, tsep)
        Co_list.append(co_p)

        # --- Bo ---
        if p >= pb:
            bo_p = bob * np.exp(-co_p * (p - pb))
        else:
            bo_p = bo_vasbeg(rs_p, api, sg_gas, tr, psep, tsep)
        Bo_list.append(bo_p)

        # --- densidad ---
        if p >= pb:
            rho_p = rho_pb * (1 + co_p * (p - pb))
        else:
            rho_p = ro_standing(rs_p, sg_gas, sgo, tr)
        Rho_list.append(rho_p)

        # --- viscosidad ---
        mu_ob_p = mu_beggs_robinson(api, tr, Rs=rs_p)
        mu_o_p = muo_vasquez_beggs(mu_ob_p, p, pb)
        Mu_o_list.append(mu_o_p)

    # =========================
    # 7) DataFrame
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
    # 8) GRÁFICOS
    # =========================
    sns.set_style("whitegrid")

    # -------- Rs vs P --------
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.scatter(df["P (psia)"], df["Rs (scf/stb)"], color="blue")
    ax1.set_title("Solubilidad del Gas (Rs) vs Presión")
    ax1.set_xlabel("P (psia)")
    ax1.set_ylabel("Rs (scf/stb)")
    fig1.tight_layout()
    for pic in sh_sum.pictures:
        if pic.name == "Rs_vs_P":
            pic.delete()
    sh_sum.pictures.add(fig1, name="Rs_vs_P", left=sh_sum.range("H2").left, top=sh_sum.range("H2").top)
    plt.close(fig1)

    # -------- Bo vs P --------
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.scatter(df["P (psia)"], df["Bo (rb/stb)"], color="green")
    ax2.set_title("Factor Volumétrico del Petróleo (Bo) vs Presión")
    ax2.set_xlabel("P (psia)")
    ax2.set_ylabel("Bo (rb/stb)")
    fig2.tight_layout()
    for pic in sh_sum.pictures:
        if pic.name == "Bo_vs_P":
            pic.delete()
    sh_sum.pictures.add(fig2, name="Bo_vs_P", left=sh_sum.range("H20").left, top=sh_sum.range("H20").top)
    plt.close(fig2)

    # -------- rho vs P --------
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    ax3.scatter(df["P (psia)"], df["rho (lb/ft3)"], color="red")
    ax3.set_title("Densidad del Petróleo vs Presión")
    ax3.set_xlabel("P (psia)")
    ax3.set_ylabel("rho (lb/ft3)")
    fig3.tight_layout()
    for pic in sh_sum.pictures:
        if pic.name == "Rho_vs_P":
            pic.delete()
    sh_sum.pictures.add(fig3, name="Rho_vs_P", left=sh_sum.range("H38").left, top=sh_sum.range("H38").top)
    plt.close(fig3)

    # -------- mu_o vs P --------
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    ax4.scatter(df["P (psia)"], df["mu_o (cp)"], color="purple")
    ax4.set_title("Viscosidad del Petróleo (μo) vs Presión")
    ax4.set_xlabel("P (psia)")
    ax4.set_ylabel("μo (cp)")
    fig4.tight_layout()
    for pic in sh_sum.pictures:
        if pic.name == "Mu_vs_P":
            pic.delete()
    sh_sum.pictures.add(fig4, name="Mu_vs_P", left=sh_sum.range("H56").left, top=sh_sum.range("H56").top)
    plt.close(fig4)


if __name__ == "__main__":
    xw.Book("PVT_App.xlsm").set_mock_caller()
    main()


# ============================================
# Test_PVT.py
# Pruebas de todas las funciones del módulo PVT
# ============================================

from PVT import (
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


def main():
    print("\n========== PRUEBAS MÓDULO PVT ==========\n")

    # ------------------------------
    # 1) Datos base (del enunciado)
    # ------------------------------
    pb = 3970.0      # psia
    rsb = 1124.0     # scf/stb
    api = 38.982
    sg_gas = 0.65    # gravedad específica del gas
    pr = 4409.0      # psia (presión de referencia)
    tr = 140.0       # °F

    # Datos adicionales usados por algunas correlaciones
    sgo = 0.82       # gravedad específica del petróleo a tanque (supuesto)
    psep = 100.0     # psia
    tsep = 120.0     # °F

    print("Datos de entrada:")
    print(f"  pb   = {pb:.2f} psia")
    print(f"  rsb  = {rsb:.2f} scf/stb")
    print(f"  API  = {api:.3f}")
    print(f"  sg_g = {sg_gas:.3f}")
    print(f"  sgo  = {sgo:.3f}")
    print(f"  Pr   = {pr:.2f} psia")
    print(f"  T    = {tr:.2f} °F\n")

    # -------------------------------------------------
    # 2) Rs por Standing y por Velarde en la presión Pr
    # -------------------------------------------------
    rs_pr_stand = rs_standing(api, sg_gas, pr, tr)
    rs_pr_vel   = rs_velarde(rsb, sg_gas, sgo, pb, pr, tr)

    print("Rs(Pr)  (Standing, 1947)        ->", rs_pr_stand)
    print("Rs(Pr)  (Velarde, 1997)         ->", rs_pr_vel)

    # ------------------------------
    # 3) Bo (Standing y Vasquez–Beggs)
    # ------------------------------
    bo_pr_stand = bo_standing(rs_pr_stand, sg_gas, sgo, tr)
    bo_pr_vb    = bo_vasbeg(rs_pr_stand, api, sg_gas, tr, psep, tsep)

    print("Bo(Pr)  (Standing, 1981)        ->", bo_pr_stand)
    print("Bo(Pr)  (Vasquez-Beggs, 1980)   ->", bo_pr_vb)

    # ------------------------------
    # 4) Co (Petrosky-Farshad y Vasquez–Beggs)
    # ------------------------------
    co_pr_petrosky = co_petrosk(rsb, sg_gas, pr, tr, api)
    co_pr_vb       = co_vasquez_beggs(rsb, sg_gas, api, tr, pr, psep, tsep)

    print("Co(Pr)  (Petrosky-Farshad, 1993)->", co_pr_petrosky)
    print("Co(Pr)  (Vasquez-Beggs, 1980)    ->", co_pr_vb)

    # ------------------------------
    # 5) Densidad saturada y subsaturada
    # ------------------------------
    # Densidad saturada en Pr usando Rs(Pr) de Standing
    rho_pr_stand = ro_standing(rs_pr_stand, sg_gas, sgo, tr)

    # Densidad en el punto de burbuja usando Rsb
    rho_pb = ro_standing(rsb, sg_gas, sgo, tr)

    # Co en Pb para usar en la correlación de petróleo subsaturado
    co_pb_vb = co_vasquez_beggs(rsb, sg_gas, api, tr, pb, psep, tsep)

    # Densidad subsaturada en Pr usando la ecuación general ρo = ρob * exp(Co*(P-Pb))
    rho_pr_sub = ro_subsaturado(rho_pb, co_pb_vb, pr, pb)

    print("rho_o(Pr) saturado (Standing)   ->", rho_pr_stand)
    print("rho_ob (en Pb) (Standing)       ->", rho_pb)
    print("rho_o(Pr) subsat. (ro_subsaturado)->", rho_pr_sub)

    # ------------------------------
    # 6) Viscosidad (Beggs-Robinson y Vasquez–Beggs)
    # ------------------------------
    # Petróleo muerto (Rs = None)
    mu_od = mu_beggs_robinson(api, tr, Rs=None)

    # Petróleo saturado en Pb (usando Rsb)
    mu_ob = mu_beggs_robinson(api, tr, Rs=rsb)

    # Petróleo subsaturado/saturado en Pr (Vasquez–Beggs)
    mu_o_pr = muo_vasquez_beggs(mu_ob, pr, pb)

    print("mu_od   (Beggs-Robinson, muerto) ->", mu_od)
    print("mu_ob   (Beggs-Robinson, sat.)   ->", mu_ob)
    print("mu_o(Pr)(Vasquez-Beggs, 1975)    ->", mu_o_pr)

    # ------------------------------
    # 7) Chequeos básicos de sanidad
    # ------------------------------
    print("\n--- Chequeos básicos ---")
    resultados = [
        ("Rs(Pr) Standing", rs_pr_stand),
        ("Rs(Pr) Velarde", rs_pr_vel),
        ("Bo(Pr) Standing", bo_pr_stand),
        ("Bo(Pr) Vasquez-Beggs", bo_pr_vb),
        ("Co(Pr) Petrosky-Farshad", co_pr_petrosky),
        ("Co(Pr) Vasquez-Beggs", co_pr_vb),
        ("rho_o(Pr) Standing", rho_pr_stand),
        ("rho_ob(Pb) Standing", rho_pb),
        ("rho_o(Pr) ro_subsaturado", rho_pr_sub),
        ("mu_od", mu_od),
        ("mu_ob", mu_ob),
        ("mu_o(Pr)", mu_o_pr),
    ]

    for nombre, valor in resultados:
        if valor is None:
            print(f"[ADVERTENCIA] {nombre} devolvió None")
        elif isinstance(valor, (int, float)) and valor <= 0:
            print(f"[ADVERTENCIA] {nombre} es <= 0  -> {valor}")
        else:
            print(f"[OK] {nombre} = {valor}")

    print("\n========== FIN DE PRUEBAS ==========\n")


if __name__ == "__main__":
    main()

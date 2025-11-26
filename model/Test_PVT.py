# Archivo para probar todas las funciones del módulo PVT.py

from PVT import (
    rs_standing,
    bo_standing,
    bo_vasbeg,
    co_petrosk,
    co_vasquez_beggs,
    ro_standing,
    mu_beggs_robinson,
    muo_vasquez_beggs,
)

# Valores de prueba "típicos" de un yacimiento de petróleo
api  = 35.0      # °API
sg   = 0.85      # gravedad específica gas en solución
sgo  = 0.82      # gravedad específica petróleo tanque
sgg  = 0.85      # gravedad específica gas
y_g  = 0.85      # mismo que sgg, solo cambia el nombre
y_o  = 0.82      # gravedad específica petróleo
t_f  = 180.0     # °F
p    = 3000.0    # psia (presión de sistema)
pb   = 2500.0    # psia (presión de burbuja)
psep = 100.0     # psia (separador)
tsep = 120.0     # °F (separador)
Rsb  = 650.0     # scf/STB (Rs en punto de burbuja)


def print_result(name, value):
    """Función auxiliar para mostrar resultados de forma ordenada."""
    print(f"{name:30s} -> {value}")


def run_all_tests():
    print("========== PRUEBAS MÓDULO PVT ==========\n")

    # -----------------------
    # 1) Solubilidad del gas
    # -----------------------
    rs = rs_standing(api, sg, p, t_f)
    print_result("Rs (Standing)", rs)

    # -------------------------------
    # 2) Factor volumétrico Bo
    # -------------------------------
    bo_st = bo_standing(Rsb, sg, sgo, t_f)
    print_result("Bo (Standing)", bo_st)

    bo_vb = bo_vasbeg(Rsb, api, sgg, t_f, psep, tsep)
    print_result("Bo (Vasquez-Beggs)", bo_vb)

    # -------------------------------------------
    # 3) Compresibilidad isotérmica del petróleo
    # -------------------------------------------
    co_pet = co_petrosk(Rsb, sgg, p, t_f, api)
    print_result("Co (Petrosky-Farshad)", co_pet)

    co_vb = co_vasquez_beggs(Rsb, y_g, api, t_f, p, psep, tsep)
    print_result("Co (Vasquez-Beggs)", co_vb)

    # ------------------------
    # 4) Densidad del petróleo
    # ------------------------
    ro = ro_standing(Rsb, y_g, y_o, t_f)
    print_result("ρo (Standing)", ro)

    # ----------------------------
    # 5) Viscosidades del petróleo
    # ----------------------------

    # μ_od: petróleo muerto
    mu_od = mu_beggs_robinson(api, t_f)
    print_result("μ_od (Beggs-Robinson)", mu_od)

    # μ_ob: petróleo saturado
    mu_ob = mu_beggs_robinson(api, t_f, Rs=Rsb)
    print_result("μ_ob (Beggs-Robinson)", mu_ob)

    # μ_o: petróleo subsaturado
    mu_o = muo_vasquez_beggs(mu_ob, p, pb)
    print_result("μ_o (Vasquez-Beggs)", mu_o)

    # ----------------------------
    # 6) Chequeos simples (opcional)
    # ----------------------------
    print("\n--- Chequeos básicos ---")
    for nombre, valor in [
        ("Rs", rs),
        ("Bo Standing", bo_st),
        ("Bo Vasquez-Beggs", bo_vb),
        ("Co Petrosky-Farshad", co_pet),
        ("Co Vasquez-Beggs", co_vb),
        ("ρo Standing", ro),
        ("μ_od", mu_od),
        ("μ_ob", mu_ob),
        ("μ_o", mu_o),
    ]:
        if valor is None:
            print(f"[ADVERTENCIA] {nombre} devolvió None (revisar función o datos)")
        elif valor <= 0:
            print(f"[ADVERTENCIA] {nombre} es ≤ 0 (puede ser físicamente extraño)")


if __name__ == "__main__":
    run_all_tests()
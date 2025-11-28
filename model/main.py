
from PVT import (
    rs_standing,
    bo_standing,
    co_vasquez_beggs,
    ro_standing,
    mu_beggs_robinson,
    muo_vasquez_beggs,
)


def main():
    print("\n========== TEST MÓDULO PVT ==========\n")

    # ------------------------------------
    # 1) Datos base (como en el enunciado)
    # ------------------------------------
    pb = 3970.0       # psia
    rsb = 1124.0      # scf/stb
    api = 38.982
    sg_gas = 0.65
    pr = 4409.0       # psia
    tr = 140.0        # °F

    # Valores adicionales que usan algunas correlaciones
    sgo = 0.82        # gravedad específica del petróleo a tanque (supuesto)
    psep = 100.0      # psia
    tsep = 120.0      # °F

    # ------------------------------------
    # 2) Cálculos en la presión Pr
    # ------------------------------------

    # Solubilidad del gas en Pr (Standing)
    rs_pr = rs_standing(api, sg_gas, pr, tr)

    # Factor volumétrico en Pr (Standing)
    bo_pr = bo_standing(rs_pr, sg_gas, sgo, tr)

    # Compresibilidad del petróleo en Pr (Vasquez–Beggs)
    co_pr = co_vasquez_beggs(rsb, sg_gas, api, tr, pr, psep, tsep)

    # Densidad del petróleo en Pr (Standing)
    rho_pr = ro_standing(rs_pr, sg_gas, sgo, tr)

    # Viscosidad:
    #   1) μ_ob (saturada) con Beggs–Robinson
    mu_ob_pr = mu_beggs_robinson(api, tr, Rs=rs_pr)
    #   2) μ_o subsaturada/saturada con Vasquez–Beggs
    mu_o_pr = muo_vasquez_beggs(mu_ob_pr, pr, pb)

    # ------------------------------------
    # 3) Mostrar resultados
    # ------------------------------------
    print(f"pb                = {pb:.2f} psia")
    print(f"rsb               = {rsb:.2f} scf/stb")
    print(f"API               = {api:.3f}")
    print(f"sg_gas            = {sg_gas:.3f}")
    print(f"Pr                = {pr:.2f} psia")
    print(f"T                 = {tr:.2f} °F\n")

    print(f"Rs(Pr)            = {rs_pr:.4f} scf/stb")
    print(f"Bo(Pr)            = {bo_pr:.6f} rb/stb")
    print(f"Co(Pr)            = {co_pr:.8f} 1/psia")
    print(f"rho_o(Pr)         = {rho_pr:.4f} lb/ft³")
    print(f"μ_ob(Pr)          = {mu_ob_pr:.4f} cp")
    print(f"μ_o(Pr)           = {mu_o_pr:.4f} cp")

    print("\n========== FIN DEL TEST PVT ==========\n")


if __name__ == "__main__":
    main()

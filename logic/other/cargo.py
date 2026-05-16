def compute_cargo_structure(L, W, H, t_cargo, rho_cargo):
    A_cargo = L*W + 2*L*H + 2*W*H
    W_cargo = rho_cargo * A_cargo * t_cargo * 9.81
    return {'W_cargo': W_cargo, 'A_cargo': A_cargo}

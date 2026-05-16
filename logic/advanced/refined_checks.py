
def interaction_check(sigma, sigma_cr, tau, tau_cr):
    if sigma_cr <= 0 or tau_cr <= 0:
        return False
    R = sigma/sigma_cr + (tau/tau_cr)**2
    return R <= 1.0

def independent_shear_check(tau, tau_allow):
    return tau <= tau_allow

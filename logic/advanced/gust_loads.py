
import math

def compute_gust_load(V_cruise, rho, CL_alpha, gust_speed, S_wing, WTO):
    q = 0.5 * rho * V_cruise**2
    delta_L = CL_alpha * (gust_speed / V_cruise) * q * S_wing
    delta_n = delta_L / WTO
    return 1.0 + abs(delta_n)

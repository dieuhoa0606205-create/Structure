
import numpy as np

def load_dat(filepath):
    coords = np.loadtxt(filepath, skiprows=1)
    le_idx = np.argmin(coords[:, 0])
    upper = coords[:le_idx+1][::-1]
    lower = coords[le_idx:]
    return coords[:, 0], upper[:, 1], lower[:, 1]

def generate_naca4(code, n=100):
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:]) / 100.0
    x = np.linspace(0, 1, n)
    yt = 5*t*(0.2969*np.sqrt(x) - 0.1260*x - 0.3516*x**2 + 0.2843*x**3 - 0.1015*x**4)
    if p == 0:
        yc = np.zeros_like(x)
        dyc_dx = np.zeros_like(x)
    else:
        yc = np.where(x < p, m/p**2 * (2*p*x - x**2), m/(1-p)**2 * ((1-2*p) + 2*p*x - x**2))
        dyc_dx = np.where(x < p, 2*m/p**2 * (p - x), 2*m/(1-p)**2 * (p - x))
    theta = np.arctan(dyc_dx)
    xu, yu = x - yt*np.sin(theta), yc + yt*np.cos(theta)
    xl, yl = x + yt*np.sin(theta), yc - yt*np.cos(theta)
    return xu, yu, xl, yl

def compute_area_perimeter(xu, yu, xl, yl):
    def poly_area(x, y):
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    a_upper = poly_area(xu, yu)
    a_lower = poly_area(xl, yl)
    area = a_upper + a_lower
    def curve_length(x, y):
        dx = np.diff(x)
        dy = np.diff(y)
        return np.sum(np.sqrt(dx**2 + dy**2))
    perimeter = curve_length(xu, yu) + curve_length(xl, yl)
    return area, perimeter

import streamlit as st

def create_skin_panel(tmax, cw):
    S_airfoil = 2.0 * cw + 0.5 * tmax
    st.caption(f'翼型周长 (自动): {S_airfoil:.3f} m')
    col1, col2 = st.columns(2)
    with col1:
        t_skin = st.number_input('蒙皮厚度 t_skin (m)', value=0.0007, step=0.0001, format='%.4f', key='t_skin')
    with col2:
        rho_skin = st.number_input('蒙皮密度 rho_skin (kg/m3)', value=160.0, format='%.0f', key='rho_skin')
    col3, col4 = st.columns(2)
    with col3:
        E_skin = st.number_input('弹性模量 E_skin (GPa)', value=2.0, step=0.5, format='%.1f', key='E_skin') * 1e9
    with col4:
        tau_allow = st.number_input('许用剪应力 tau_allow (MPa)', value=5.0, step=0.5, format='%.1f', key='tau_allow') * 1e6
    return {
        't_skin': t_skin, 'rho_skin': rho_skin,
        'E_skin': E_skin, 'tau_allow': tau_allow
    }

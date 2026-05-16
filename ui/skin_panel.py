import streamlit as st

def create_skin_panel(tmax, cw):
    S_airfoil = 2.0 * cw + 0.5 * tmax
    st.markdown(f'翼型周长 (自动计算): **{S_airfoil:.3f} m**')
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        t_skin = st.number_input('厚度 (m)', value=0.0008, step=0.0002, format='%.4f')
    with col2:
        rho_skin = st.number_input('密度 (kg/m3)', value=1700.0)
    with col3:
        E_skin = st.number_input('弹性模量 E (GPa)', value=40.0, step=1.0, format='%.1f') * 1e9
    with col4:
        tau_allow = st.number_input('许用剪应力 (MPa)', value=30.0, step=1.0, format='%.1f') * 1e6
    st.caption('气动扭矩由 C_m0 和巡航动压自动估算，用于剪切校核')
    return {'t_skin': t_skin, 'rho_skin': rho_skin, 'E_skin': E_skin, 'tau_allow': tau_allow}

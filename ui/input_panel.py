import streamlit as st

def create_input_panel():
    st.markdown('### 飞行器总体参数')
    col1, col2 = st.columns(2)
    with col1:
        WTO = st.number_input(
            '起飞重量 W_TO (N)', value=98.0, step=5.0, format='%.1f',
            help='飞行器最大起飞重量 (10kg ≈ 98N)', key='WTO')
        kL = st.slider(
            '气囊升力占比 k_L', 0.0, 1.0, 0.35, 0.05,
            help='气囊承担的升力比例', key='kL')
        nvtol = st.number_input(
            '垂飞过载 n_vtol', value=1.3, step=0.1, format='%.1f', key='nvtol')
        fs = st.number_input(
            '安全系数 f_s', value=1.25, step=0.05, format='%.2f', key='fs')
        b = st.number_input(
            '机翼展长 b (m)', value=1.2, step=0.1, format='%.2f', key='b')
        tmax = st.number_input(
            '翼型最大厚度 t_max (m)', value=0.144, step=0.005, format='%.3f',
            help='NACA0012 相对厚度12%', key='tmax')
        cw = st.number_input(
            '外翼弦长 c_w (m)', value=1.2, step=0.05, format='%.2f', key='cw')
    with col2:
        r_env = st.number_input(
            '气囊短半轴半径 r_env (m)', value=0.4, step=0.02, format='%.2f', key='r_env')
        r_env_long = st.number_input(
            '气囊长轴半径 r_env_long (m)', value=1.74, step=0.05, format='%.2f',
            help='气囊长度的一半', key='r_env_long')
        D_rotor = st.number_input(
            '旋翼直径 D_rotor (m)', value=0.15, step=0.01, format='%.2f', key='D_rotor')
        delta = st.number_input(
            '安全距离 delta (m)', value=0.05, step=0.01, format='%.2f', key='delta')
        rho = st.number_input(
            '空气密度 rho (kg/m^3)', value=1.225, format='%.3f', key='rho')
        V_cruise = st.number_input(
            '巡航速度 V_cruise (m/s)', value=10.0, step=1.0, format='%.1f', key='V_cruise')
        Cm0 = st.number_input(
            '翼型零升力矩系数 C_m0', value=-0.05, step=0.01, format='%.2f', key='Cm0')
        k_sec = st.number_input(
            '全局余量系数 k_sec', value=0.15, step=0.01, format='%.2f', key='k_sec')
    return {
        'WTO': WTO, 'kL': kL, 'nvtol': nvtol, 'fs': fs,
        'b': b, 'tmax': tmax, 'cw': cw,
        'r_env': r_env, 'r_env_long': r_env_long,
        'D_rotor': D_rotor, 'delta': delta,
        'rho': rho, 'V_cruise': V_cruise, 'Cm0': Cm0, 'k_sec': k_sec
    }

import streamlit as st

def create_input_panel():
    st.markdown('### 飞行器总体参数')
    col1, col2 = st.columns(2)
    with col1:
        WTO = st.number_input('起飞重量 W_TO (N)', value=100.0, step=10.0, format='%.1f', help='飞行器最大起飞重量')
        kL = st.slider('气囊升力占比 k_L', 0.0, 1.0, 0.5, 0.05, help='气囊承担的升力比例')
        nvtol = st.number_input('垂飞过载 n_vtol', value=2.0, step=0.1, format='%.1f', help='垂直起飞时的过载系数')
        fs = st.number_input('安全系数 f_s', value=1.5, step=0.1, format='%.1f')
        b = st.number_input('机翼展长 b (m)', value=3.0, step=0.1, format='%.2f')
        bfuse = st.number_input('机身宽度 b_fuse (m)', value=0.8, step=0.05, format='%.2f')
        tmax = st.number_input('翼型最大厚度 t_max (m)', value=0.06, step=0.005, format='%.3f')
        cw = st.number_input('外翼弦长 c_w (m)', value=0.4, step=0.05, format='%.2f')
    with col2:
        r_env = st.number_input('气囊短半轴半径 r_env (m)', value=0.25, step=0.05, format='%.2f')
        D_rotor = st.number_input('旋翼直径 D_rotor (m)', value=0.35, step=0.05, format='%.2f')
        delta = st.number_input('安全距离 delta (m)', value=0.08, step=0.02, format='%.2f')
        rho = st.number_input('空气密度 rho (kg/m3)', value=1.225, format='%.3f')
        V_cruise = st.number_input('巡航速度 V_cruise (m/s)', value=30.0, step=1.0, format='%.1f')
        Cm0 = st.number_input('翼型零升力矩系数 C_m0', value=-0.05, step=0.01, format='%.2f', help='用于估算气动扭矩')
        k_sec = st.number_input('全局余量系数 k_sec', value=0.20, step=0.01, format='%.2f')
    return {
        'WTO': WTO, 'kL': kL, 'nvtol': nvtol, 'fs': fs,
        'b': b, 'bfuse': bfuse, 'tmax': tmax, 'cw': cw,
        'r_env': r_env, 'D_rotor': D_rotor, 'delta': delta,
        'rho': rho, 'V_cruise': V_cruise, 'Cm0': Cm0, 'k_sec': k_sec
    }

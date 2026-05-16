import streamlit as st
import math

def create_rib_panel(tmax, cw):
    A_airfoil = 0.68 * tmax * cw
    st.markdown(f'翼型轮廓面积 (自动计算): **{A_airfoil:.4f} m2**')
    st.markdown('#### 普通翼肋')
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rib = st.number_input('数量', value=12, step=1)
    with c2:
        t_rib = st.number_input('厚度 (m)', value=0.002, step=0.0005, format='%.4f', key='t_rib')
    with c3:
        fill_rib = st.number_input('填充系数', value=0.20, step=0.02, key='fill_rib')
    c4, c5 = st.columns(2)
    with c4:
        rho_rib = st.number_input('密度 (kg/m3)', value=120.0, key='rho_rib')
    with c5:
        E_rib = st.number_input('弹性模量 E (GPa)', value=4.0, step=0.5, key='E_rib') * 1e9
    d_rib = st.number_input('参考间距 d_rib (m)', value=0.30, step=0.02, help='用于蒙皮稳定性校核')

    # 重点显示单肋数据
    A_rib_net = A_airfoil * fill_rib
    single_mass = rho_rib * A_rib_net * t_rib
    st.info(f'普通单肋净截面积: {A_rib_net:.4f} m2, 预估质量: {single_mass*1000:.1f} g ({single_mass:.3f} kg)')

    st.markdown('#### 加强翼肋')
    c1r, c2r, c3r = st.columns(3)
    with c1r:
        n_rib_rein = st.number_input('数量', value=2, step=1, key='n_rib_rein')
    with c2r:
        t_rib_rein = st.number_input('厚度 (m)', value=0.003, step=0.0005, format='%.4f', key='t_rib_rein')
    with c3r:
        fill_rib_rein = st.number_input('填充系数', value=0.25, step=0.02, key='fill_rib_rein')
    c4r, c5r = st.columns(2)
    with c4r:
        rho_rib_rein = st.number_input('密度 (kg/m3)', value=120.0, key='rho_rib_rein')
    return {
        'n_rib': n_rib, 't_rib': t_rib, 'fill_rib': fill_rib,
        'rho_rib': rho_rib, 'E_rib': E_rib,
        'n_rib_rein': n_rib_rein, 't_rib_rein': t_rib_rein,
        'fill_rib_rein': fill_rib_rein, 'rho_rib_rein': rho_rib_rein,
        'd_rib': d_rib
    }

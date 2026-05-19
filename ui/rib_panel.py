import streamlit as st

def create_rib_panel(tmax, cw):
    A_airfoil = 0.68 * tmax * cw
    st.caption(f'翼型轮廓面积 (自动): {A_airfoil:.4f} m2')
    st.markdown('##### 普通翼肋')
    col1, col2, col3 = st.columns(3)
    with col1:
        n_rib = st.number_input('普通翼肋总数', value=4, step=1, min_value=0, key='n_rib')
    with col2:
        t_rib = st.number_input('翼肋厚度 (m)', value=0.001, step=0.0002, format='%.4f', key='t_rib')
    with col3:
        fill_rib = st.number_input('填充系数', value=0.15, step=0.02, format='%.2f', key='fill_rib')
    col4, col5 = st.columns(2)
    with col4:
        rho_rib = st.number_input('材料密度 rho (kg/m3)', value=120.0, step=10.0, format='%.0f', key='rho_rib')
    with col5:
        E_rib = st.number_input('弹性模量 E (GPa)', value=4.0, step=0.5, format='%.1f', key='E_rib') * 1e9
    d_rib = st.number_input('翼肋参考间距 d_rib (m)', value=0.3, step=0.02, format='%.2f', key='d_rib')
    st.markdown('##### 加强翼肋')
    col1r, col2r, col3r = st.columns(3)
    with col1r:
        n_rib_rein = st.number_input('加强翼肋总数', value=4, step=1, min_value=0, key='n_rib_rein')
    with col2r:
        t_rib_rein = st.number_input('加强翼肋厚度 (m)', value=0.002, step=0.0002, format='%.4f', key='t_rib_rein')
    with col3r:
        fill_rib_rein = st.number_input('填充系数 (加强)', value=0.25, step=0.02, format='%.2f', key='fill_rib_rein')
    col4r, col5r = st.columns(2)
    with col4r:
        rho_rib_rein = st.number_input('材料密度 rho (kg/m3)', value=650.0, step=10.0, format='%.0f', key='rho_rib_rein')
    return {
        'n_rib': n_rib, 't_rib': t_rib, 'fill_rib': fill_rib,
        'rho_rib': rho_rib, 'E_rib': E_rib,
        'n_rib_rein': n_rib_rein, 't_rib_rein': t_rib_rein,
        'fill_rib_rein': fill_rib_rein, 'rho_rib_rein': rho_rib_rein,
        'd_rib': d_rib
    }

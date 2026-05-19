import streamlit as st

def create_other_panel():
    st.subheader('气囊系统')
    m_env = st.number_input('单个气囊质量 (kg)', value=0.1, step=0.05, format='%.2f', key='m_env')
    st.subheader('起落架')
    k_gear = st.number_input('起落架重量系数 k_gear', value=0.04, step=0.005, format='%.3f', key='k_gear')
    st.subheader('载货仓')
    col1, col2 = st.columns(2)
    with col1:
        L_cargo = st.number_input('长度 (m)', value=0.3, step=0.05, format='%.2f', key='L_cargo')
        H_cargo = st.number_input('高度 (m)', value=0.13, step=0.02, format='%.2f', key='H_cargo')
    with col2:
        W_cargo = st.number_input('宽度 (m)', value=0.2, step=0.05, format='%.2f', key='W_cargo')
        t_cargo = st.number_input('壁厚 (m)', value=0.001, step=0.0002, format='%.4f', key='t_cargo')
    rho_cargo = st.number_input('材料密度 rho_cargo (kg/m3)', value=650.0, step=10.0, format='%.0f', key='rho_cargo')
    W_payload = st.number_input('预期载重 W_payload (N)', value=10.0, step=2.0, format='%.1f', key='W_payload')
    st.subheader('额外质量')
    W_extra = st.number_input('额外质量 (N)', value=2.0, step=0.5, format='%.1f', key='W_extra')
    return {
        'm_env': m_env, 'k_gear': k_gear,
        'L_cargo': L_cargo, 'W_cargo': W_cargo, 'H_cargo': H_cargo,
        't_cargo': t_cargo, 'rho_cargo': rho_cargo,
        'W_payload': W_payload, 'W_extra': W_extra,
        'W_cargo_width': W_cargo
    }

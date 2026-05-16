import streamlit as st

def create_other_panel():
    st.subheader('气囊系统')
    m_env = st.number_input('单个气囊质量 (kg)', value=2.0, step=0.5)
    st.subheader('起落架')
    k_gear = st.number_input('起落架重量系数 k_gear', value=0.04, step=0.005, help='固定滑橇约0.04，轮式约0.06')
    st.subheader('载货仓')
    c1, c2 = st.columns(2)
    with c1:
        L_cargo = st.number_input('长度 (m)', value=0.4, step=0.05)
        H_cargo = st.number_input('高度 (m)', value=0.15, step=0.02)
    with c2:
        W_cargo = st.number_input('宽度 (m)', value=0.3, step=0.05)
        t_cargo = st.number_input('壁厚 (m)', value=0.002, step=0.0005, format='%.4f')
    rho_cargo = st.number_input('材料密度 (kg/m3)', value=1750.0)
    W_payload = st.number_input('预期载重 (N)', value=50.0, step=5.0, help='最大载荷重量')
    st.subheader('额外质量（线缆/胶水等）')
    W_extra = st.number_input('额外质量 (N)', value=5.0, step=1.0)
    return {
        'm_env': m_env, 'k_gear': k_gear,
        'L_cargo': L_cargo, 'W_cargo': W_cargo, 'H_cargo': H_cargo,
        't_cargo': t_cargo, 'rho_cargo': rho_cargo,
        'W_payload': W_payload, 'W_extra': W_extra,
        'W_cargo_width': W_cargo
    }

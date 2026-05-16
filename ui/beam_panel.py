import streamlit as st

def create_beam_panel():
    st.subheader('主梁设计')
    st.warning('注意：梁高度不要超过其所处位置的最大厚度，否则会影响计算精度')
    beam_type = st.radio('梁构型', ['单梁式', '双梁式'], index=0, horizontal=True)
    k_reinforce = st.number_input('加强系数（转接处/加载点补强）', value=0.10, step=0.01, format='%.2f',
                                  help='针对转接处或者加载额外载荷处的加强考虑')

    if beam_type == '单梁式':
        st.markdown('**主梁截面**')
        section_type = st.radio('截面类型', ['碳管梁 (圆管)', '工字梁'], index=0, horizontal=True, key='single_sec')
        front_params = _create_section_inputs(section_type, prefix='single')
        rear_params = {}
        section_type_front = 'tube' if '碳管' in section_type else 'i_beam'
        section_type_rear = None
    else:
        col_f, col_r = st.columns(2)
        with col_f:
            st.markdown('**前梁**')
            sec_f = st.radio('截面类型', ['碳管梁 (圆管)', '工字梁'], index=0, horizontal=True, key='front_sec')
            front_params = _create_section_inputs(sec_f, prefix='front')
            section_type_front = 'tube' if '碳管' in sec_f else 'i_beam'
        with col_r:
            st.markdown('**后梁**')
            sec_r = st.radio('截面类型', ['碳管梁 (圆管)', '工字梁'], index=0, horizontal=True, key='rear_sec')
            rear_params = _create_section_inputs(sec_r, prefix='rear')
            section_type_rear = 'tube' if '碳管' in sec_r else 'i_beam'

    return {
        'beam_type': 'single' if beam_type == '单梁式' else 'double',
        'section_type_front': section_type_front,
        'section_type_rear': section_type_rear,
        'front_params': front_params,
        'rear_params': rear_params,
        'k_reinforce': k_reinforce
    }

def _create_section_inputs(section_type, prefix=''):
    if '碳管' in section_type:
        col1, col2 = st.columns(2)
        with col1:
            D = st.number_input('外径 D (m)', value=0.04, step=0.005, format='%.3f', key=f'{prefix}_D')
        with col2:
            t = st.number_input('壁厚 t (m)', value=0.002, step=0.0005, format='%.4f', key=f'{prefix}_t')
        col3, col4 = st.columns(2)
        with col3:
            rho = st.number_input('材料密度 rho (kg/m3)', value=1600.0, format='%.0f', key=f'{prefix}_rho')
        with col4:
            sigma_allow = st.number_input('许用应力 sigma (MPa)', value=350.0, format='%.0f', key=f'{prefix}_sigma')
        return {'D': D, 't': t, 'rho': rho, 'sigma_allow': sigma_allow * 1e6}
    else:
        st.markdown('工字梁尺寸:')
        col1, col2 = st.columns(2)
        with col1:
            h = st.number_input('梁高 h (m)', value=0.04, step=0.005, format='%.3f', key=f'{prefix}_h')
            b_f = st.number_input('缘条宽度 b_f (m)', value=0.02, step=0.002, format='%.3f', key=f'{prefix}_bf')
        with col2:
            t_f = st.number_input('缘条厚度 t_f (m)', value=0.002, step=0.0005, format='%.4f', key=f'{prefix}_tf')
            t_w = st.number_input('腹板厚度 t_w (m)', value=0.0015, step=0.0005, format='%.4f', key=f'{prefix}_tw')
        col3, col4 = st.columns(2)
        with col3:
            rho = st.number_input('材料密度 rho (kg/m3)', value=1600.0, format='%.0f', key=f'{prefix}_rho_i')
        with col4:
            sigma_allow = st.number_input('许用应力 sigma (MPa)', value=350.0, format='%.0f', key=f'{prefix}_sigma_i')
        return {'h': h, 'b_f': b_f, 't_f': t_f, 't_w': t_w, 'rho': rho, 'sigma_allow': sigma_allow * 1e6}

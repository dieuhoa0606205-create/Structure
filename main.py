import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import tempfile
import os as os_module

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# ---------- 基础计算模块 ----------
from logic.loads import compute_design_loads
from logic.wing.beam import compute_beam
from logic.wing.rib import compute_ribs
from logic.wing.skin import compute_skin
from logic.other.envelope import compute_envelope
from logic.other.gear import compute_gear
from logic.other.cargo import compute_cargo_structure
from logic.other.extra import compute_extra

# ---------- 高级计算模块 ----------
from logic.advanced.loads_advanced import compute_design_loads_advanced
from logic.advanced.beam_advanced import compute_beam_advanced
from logic.advanced.rib_advanced import compute_ribs_advanced
from logic.advanced.skin_advanced import compute_skin_advanced

# ---------- 存储模块 ----------
from storage.material_io import load_materials_from_excel, load_materials_from_json, load_materials_from_csv
from storage.result_export import export_detailed_report

# ---------- 界面模块 ----------
from ui.input_panel import create_input_panel
from ui.beam_panel import create_beam_panel
from ui.rib_panel import create_rib_panel
from ui.skin_panel import create_skin_panel
from ui.other_panel import create_other_panel
from view.airfoil_view import plot_airfoil
from view.loads_view import plot_moment_distribution
from view.outline_view import plot_aircraft_outline

# ---------- 高级功能模块 (可选) ----------
try:
    from logic.advanced.gust_loads import compute_gust_load
    from logic.advanced.airfoil_geometry import generate_naca4, load_dat, compute_area_perimeter
    from logic.advanced.refined_checks import interaction_check, independent_shear_check
    ADV_AVAIL = True
except ImportError:
    ADV_AVAIL = False

G = 9.81

st.set_page_config(page_title='低空联翼式飞艇结构特性估算', page_icon='🪽', layout='wide')

# ---------- 翼型可视化函数 ----------

# ========== 模式选择 ==========
mode = st.sidebar.radio("计算模式", ["基础", "高级"], index=0, key="mode_radio",
                        help="高级模式支持精确翼型、突风载荷及精细校核")

with st.sidebar:
    st.title('📐 总体参数')
    overall_params = create_input_panel()

    # 材料导入/导出
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 文件操作")
    uploaded_mat = st.sidebar.file_uploader("导入材料库", type=["xlsx", "json", "csv"], key="mat_upload")
    if uploaded_mat is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_mat.name)[1]) as tmp:
            tmp.write(uploaded_mat.read())
            tmp_path = tmp.name
        ext = uploaded_mat.name.split(".")[-1].lower()
        if ext == "xlsx":
            materials_db = load_materials_from_excel(tmp_path)
        elif ext == "json":
            materials_db = load_materials_from_json(tmp_path)
        elif ext == "csv":
            materials_db = load_materials_from_csv(tmp_path)
        else:
            materials_db = []
        st.sidebar.success(f"已加载 {len(materials_db)} 种材料")
        os.unlink(tmp_path)

    # 高级选项
    if mode == "高级" and ADV_AVAIL:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 高级选项")
        use_precise_airfoil = st.sidebar.checkbox("精确翼型", value=False, key="precise")
        if use_precise_airfoil:
            airfoil_src = st.sidebar.selectbox("翼型来源", ["NACA四位数字", "上传.dat文件"], key="airfoil_src")
            if airfoil_src == "NACA四位数字":
                naca_code = st.sidebar.text_input("NACA 四位数字", value="4412", key="naca_code")
            else:
                dat_file = st.sidebar.file_uploader("选择 .dat 文件", type=["dat"], key="dat_file")
        use_gust = st.sidebar.checkbox("考虑突风载荷", value=False, key="use_gust")
        if use_gust:
            CL_alpha = st.sidebar.number_input("升力线斜率 (1/rad)", value=5.73, step=0.1, format="%.2f", key="CL_alpha")
            gust_speed = st.sidebar.number_input("突风速度 (m/s)", value=15.0, step=1.0, format="%.1f", key="gust_speed")
        use_refined = st.sidebar.checkbox("精细强度校核", value=False, key="use_refined")
    elif mode == "高级" and not ADV_AVAIL:
        st.sidebar.warning("高级模块未安装，请先执行 setup")
        use_precise_airfoil = False
        use_gust = False
        use_refined = False
    else:
        use_precise_airfoil = False
        use_gust = False
        use_refined = False

st.title('低空联翼式飞艇结构特性估算')
st.markdown('---')

tab1, tab2, tab3, tab4, tab_visual, tab5 = st.tabs(
    ['🪶 主梁', '🪶 翼肋', '🛡️ 蒙皮', '🎈 其他重量', '📈 可视化', '📊 结果汇总'])

with tab1:
    beam_params = create_beam_panel()

with tab2:
    rib_params = create_rib_panel(overall_params['tmax'], overall_params['cw'])

with tab3:
    skin_params = create_skin_panel(overall_params['tmax'], overall_params['cw'])

with tab4:
    other_params = create_other_panel()


with tab_visual:
    st.header('📈 可视化')
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('翼型展示')
        if mode == "高级" and ADV_AVAIL and use_precise_airfoil:
            try:
                if airfoil_src == "NACA四位数字" and naca_code:
                    xu, yu, xl, yl = generate_naca4(naca_code)
                elif airfoil_src == "上传.dat文件" and dat_file is not None:
                    content_dat = dat_file.read().decode("utf-8")
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as tmp:
                        tmp.write(content_dat)
                        tmp_path = tmp.name
                    xu, yu, xl, yl = load_dat(tmp_path)
                    os_module.unlink(tmp_path)
                else:
                    xu = yu = xl = yl = None
                if xu is not None:
                    fig = plot_airfoil(xu, yu, xl, yl, "当前翼型")
                    st.pyplot(fig)
            except Exception as e:
                st.warning(f"翼型可视化失败: {e}")
        else:
            st.info("请切换到高级模式并选择精确翼型以查看翼型形状。")
    with col2:
        st.subheader('飞机外轮廓')
        fig_outline = plot_aircraft_outline(
            overall_params['b'], overall_params['bfuse'], overall_params['cw'],
            overall_params['tmax'], overall_params['r_env'],
            overall_params['D_rotor'], overall_params['delta'])
        st.pyplot(fig_outline)

    if st.button("显示弯矩/剪力分布"):
        try:
            if 'res' in st.session_state:
                loads = st.session_state['res']['loads']
            else:
                # 如果没有计算结果，临时计算一次
                if mode == "高级" and ADV_AVAIL:
                    loads = compute_design_loads_advanced(
                        WTO=overall_params['WTO'], kL=overall_params['kL'],
                        nvtol=overall_params['nvtol'], fs=overall_params['fs'],
                        b=overall_params['b'], bfuse=overall_params['bfuse'],
                        r_env=overall_params['r_env'], D_rotor=overall_params['D_rotor'],
                        delta=overall_params['delta'], cw=overall_params['cw'],
                        rho=overall_params['rho'], V_cruise=overall_params['V_cruise'],
                        Cm0=overall_params['Cm0'], W_payload=other_params['W_payload'],
                        W_cargo_width=other_params['W_cargo_width'],
                        use_elliptic=True)
                else:
                    loads = compute_design_loads(
                        WTO=overall_params['WTO'], kL=overall_params['kL'],
                        nvtol=overall_params['nvtol'], fs=overall_params['fs'],
                        b=overall_params['b'], r_env=overall_params['r_env'],
                        D_rotor=overall_params['D_rotor'], delta=overall_params['delta'],
                        cw=overall_params['cw'], rho=overall_params['rho'],
                        V_cruise=overall_params['V_cruise'], Cm0=overall_params['Cm0'],
                        W_payload=other_params['W_payload'],
                        W_cargo_width=other_params['W_cargo_width'])
            fig_moment = plot_moment_distribution(
                loads, overall_params['WTO'], overall_params['kL'],
                overall_params['b'], overall_params['bfuse'],
                overall_params['cw'], overall_params['V_cruise'])
            st.pyplot(fig_moment)
        except Exception as e:
            st.error(f"弯矩分布图生成失败: {e}")
with tab5:
    st.header('📊 计算结果')
    _, calc_col, _ = st.columns([1, 1, 1])
    with calc_col:
        calc_clicked = st.button('⚡ 开始计算', type='primary', use_container_width=True)

    if calc_clicked:
        try:
            # 1. 载荷计算
            if mode == "高级" and ADV_AVAIL:
                loads = compute_design_loads_advanced(
                    WTO=overall_params['WTO'], kL=overall_params['kL'],
                    nvtol=overall_params['nvtol'], fs=overall_params['fs'],
                    b=overall_params['b'], bfuse=overall_params['bfuse'],
                    r_env=overall_params['r_env'], D_rotor=overall_params['D_rotor'],
                    delta=overall_params['delta'], cw=overall_params['cw'],
                    rho=overall_params['rho'], V_cruise=overall_params['V_cruise'],
                    Cm0=overall_params['Cm0'], W_payload=other_params['W_payload'],
                    W_cargo_width=other_params['W_cargo_width'],
                    use_elliptic=True)
            else:
                loads = compute_design_loads(
                    WTO=overall_params['WTO'], kL=overall_params['kL'],
                    nvtol=overall_params['nvtol'], fs=overall_params['fs'],
                    b=overall_params['b'], r_env=overall_params['r_env'],
                    D_rotor=overall_params['D_rotor'], delta=overall_params['delta'],
                    cw=overall_params['cw'], rho=overall_params['rho'],
                    V_cruise=overall_params['V_cruise'], Cm0=overall_params['Cm0'],
                    W_payload=other_params['W_payload'],
                    W_cargo_width=other_params['W_cargo_width'])

            # 2. 梁计算
            if mode == "高级" and ADV_AVAIL:
                beam_result = compute_beam_advanced(
                    loads=loads,
                    beam_type=beam_params['beam_type'],
                    section_type_front=beam_params.get('section_type_front', 'tube'),
                    section_type_rear=beam_params.get('section_type_rear', 'tube'),
                    front_params=beam_params.get('front_params', {}),
                    rear_params=beam_params.get('rear_params', {}),
                    k_reinforce=beam_params.get('k_reinforce', 0.0),
                    material_E=230e9, material_G=90e9,
                    enable_optimization=True, target_safety=1.5)
            else:
                beam_result = compute_beam(
                    loads=loads,
                    beam_type=beam_params['beam_type'],
                    section_type_front=beam_params.get('section_type_front', 'tube'),
                    section_type_rear=beam_params.get('section_type_rear', 'tube'),
                    front_params=beam_params.get('front_params', {}),
                    rear_params=beam_params.get('rear_params', {}),
                    k_reinforce=beam_params.get('k_reinforce', 0.0))

            # 3. 翼肋计算
            if mode == "高级" and ADV_AVAIL:
                rib_result = compute_ribs_advanced(
                    tmax=overall_params['tmax'], cw=overall_params['cw'],
                    n_rib=rib_params['n_rib'], t_rib=rib_params['t_rib'],
                    fill_rib=rib_params['fill_rib'], rho_rib=rib_params['rho_rib'],
                    E_rib=rib_params['E_rib'],
                    n_rib_rein=rib_params['n_rib_rein'], t_rib_rein=rib_params['t_rib_rein'],
                    fill_rib_rein=rib_params['fill_rib_rein'], rho_rib_rein=rib_params['rho_rib_rein'],
                    V_root=loads['V_root'], M_root=loads['M_root'])
            else:
                rib_result = compute_ribs(
                    tmax=overall_params['tmax'], cw=overall_params['cw'],
                    n_rib=rib_params['n_rib'], t_rib=rib_params['t_rib'],
                    fill_rib=rib_params['fill_rib'], rho_rib=rib_params['rho_rib'],
                    E_rib=rib_params['E_rib'],
                    n_rib_rein=rib_params['n_rib_rein'], t_rib_rein=rib_params['t_rib_rein'],
                    fill_rib_rein=rib_params['fill_rib_rein'], rho_rib_rein=rib_params['rho_rib_rein'],
                    V_root=loads['V_root'])

            # 4. 蒙皮计算
            if mode == "高级" and ADV_AVAIL:
                skin_result = compute_skin_advanced(
                    b=overall_params['b'], cw=overall_params['cw'],
                    tmax=overall_params['tmax'], t_skin=skin_params['t_skin'],
                    rho_skin=skin_params['rho_skin'], E_skin=skin_params['E_skin'],
                    tau_allow=skin_params['tau_allow'], T=loads['T_aero'],
                    d_rib=rib_params['d_rib'])
            else:
                skin_result = compute_skin(
                    b=overall_params['b'], cw=overall_params['cw'],
                    tmax=overall_params['tmax'], t_skin=skin_params['t_skin'],
                    rho_skin=skin_params['rho_skin'], E_skin=skin_params['E_skin'],
                    tau_allow=skin_params['tau_allow'], T=loads['T_aero'],
                    d_rib=rib_params['d_rib'])

            # 5. 其他重量
            envelope_result = compute_envelope(m_env=other_params['m_env'])
            gear_result = compute_gear(WTO=overall_params['WTO'], k_gear=other_params['k_gear'])
            cargo_result = compute_cargo_structure(
                L=other_params['L_cargo'], W=other_params['W_cargo'],
                H=other_params['H_cargo'], t_cargo=other_params['t_cargo'],
                rho_cargo=other_params['rho_cargo'])
            extra_result = compute_extra(W_extra=other_params['W_extra'])

            # 6. 汇总
            W_wing = beam_result['W_beam'] + rib_result['W_ribs_total'] + skin_result['W_skin']
            W_other = (envelope_result['W_env'] + gear_result['W_gear'] +
                       cargo_result['W_cargo'] + extra_result['W_extra'])
            W_struct = (W_wing + W_other) * (1 + overall_params.get('k_sec', 0.2))
            W_remain = overall_params['WTO'] - W_struct

            # 7. 保存结果
            st.session_state['calc_done'] = True
            st.session_state['res'] = {
                'loads': loads,
                'beam': beam_result,
                'ribs': rib_result,
                'skin': skin_result,
                'envelope': envelope_result,
                'gear': gear_result,
                'cargo': cargo_result,
                'extra': extra_result,
                'W_wing': W_wing,
                'W_other': W_other,
                'W_struct': W_struct,
                'W_remain': W_remain,
                'WTO': overall_params['WTO'],
                'beam_params': beam_params,
                'skin_params': skin_params,
                'components': {
                    '梁': beam_result['W_beam'],
                    '翼肋': rib_result['W_ribs_total'],
                    '蒙皮': skin_result['W_skin'],
                    '气囊': envelope_result['W_env'],
                    '起落架': gear_result['W_gear'],
                    '载货仓': cargo_result['W_cargo'],
                    '额外': extra_result['W_extra']
                }
            }

        except Exception as e:
            st.error(f'计算错误: {e}')

    # 8. 展示结果
    if st.session_state.get('calc_done', False):
        res = st.session_state['res']
        col1, col2, col3, col4 = st.columns(4)
        col1.metric('结构总重', f"{res['W_struct']:.1f} N", f"{res['W_struct']/G:.2f} kg")
        col2.metric('剩余重量', f"{res['W_remain']:.1f} N", f"{res['W_remain']/G:.2f} kg")
        col3.metric('结构占比', f"{res['W_struct']/res['WTO']*100:.1f} %")
        col4.metric('起飞重量', f"{res['WTO']:.1f} N", f"{res['WTO']/G:.2f} kg")

        st.markdown('---')
        left, right = st.columns([1.2, 1])
        with left:
            st.subheader('📋 各部件重量分解')
            df = pd.DataFrame({
                '部件': list(res['components'].keys()),
                '重量 (N)': list(res['components'].values()),
                '重量 (kg)': [w/G for w in res['components'].values()],
                '占比 (%)': [w/res['W_struct']*100 for w in res['components'].values()]
            })
            st.dataframe(df.style.format({
                '重量 (N)': '{:.1f}', '重量 (kg)': '{:.2f}', '占比 (%)': '{:.1f}'
            }), use_container_width=True)
        with right:
            st.subheader('📊 重量占比')
            fig, ax = plt.subplots(figsize=(4.5, 3.8))
            labels = list(res['components'].keys())
            values = list(res['components'].values())
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
            ax.axis('equal')
            plt.tight_layout()
            st.pyplot(fig)

        # 强度校核
        st.markdown('---')
        st.subheader('🔬 强度校核')
        beam = res['beam']
        skin = res['skin']

        colA, colB = st.columns(2)
        with colA:
            st.write('**主梁弯曲**')
            sigma = beam.get('sigma_b', 0)/1e6
            allow = beam.get('sigma_allow', 0)/1e6
            st.write(f'应力 {sigma:.2f} MPa (许用 {allow:.1f} MPa)')
            if beam.get('bend_ok'):
                st.success('✅ 通过')
            else:
                st.error('❌ 不通过')

            st.write('**主梁剪切**')
            tau = beam.get('tau_beam', 0)/1e6
            tau_a = beam.get('tau_allow', 0)/1e6
            st.write(f'应力 {tau:.2f} MPa (许用 {tau_a:.1f} MPa)')
            if beam.get('shear_ok'):
                st.success('✅ 通过')
            else:
                st.error('❌ 不通过')

        with colB:
            st.write('**蒙皮剪切**')
            tskin = skin.get('tau_skin', 0)/1e6
            tcr = skin.get('tau_cr', 0)/1e6
            st.write(f'剪应力 {tskin:.2f} MPa | 临界 {tcr:.2f} MPa')
            if skin.get('shear_ok'):
                st.success('✅ 通过')
            else:
                st.error('❌ 不通过')

        # 导出报告
        st.markdown('---')
        if st.button('📥 导出详细报告 Excel'):
            try:
                filepath = "calculation_results.xlsx"
                msg = export_detailed_report(res, filepath)
                st.success(msg)
            except Exception as e:
                st.error(f"导出失败: {e}")

st.markdown('---')
st.caption('AeroStructCalc v2.0 · 全模块集成')
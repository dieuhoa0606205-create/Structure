import streamlit as st
from service.preloader import run_all_preload
run_all_preload()
from service.session_guard import start_watchdog, update_activity, show_exit_button
import math
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import tempfile
import os as os_module
from datetime import datetime

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from logic.loads import compute_design_loads
from logic.wing.beam import compute_beam
from logic.wing.rib import compute_ribs
from logic.wing.skin import compute_skin
from logic.other.envelope import compute_envelope
from logic.other.gear import compute_gear
from logic.other.cargo import compute_cargo_structure
from logic.other.extra import compute_extra
from logic.advanced.loads_advanced import compute_design_loads_advanced
from logic.advanced.beam_advanced import compute_beam_advanced
from logic.advanced.rib_advanced import compute_ribs_advanced
from logic.advanced.skin_advanced import compute_skin_advanced

from ui.input_panel import create_input_panel
from ui.beam_panel import create_beam_panel
from ui.rib_panel import create_rib_panel
from ui.skin_panel import create_skin_panel
from ui.other_panel import create_other_panel

from view.airfoil_view import plot_airfoil
from view.loads_view import plot_moment_distribution
from view.outline_view import plot_aircraft_outline

from storage.material_io import load_materials_from_excel, load_materials_from_json, load_materials_from_csv
from storage.result_export import export_detailed_report
from storage.scheme_manager import save_scheme, load_scheme_from_uploaded, apply_scheme, compare_schemes_detailed, export_scheme_to_folder, create_export_folder, list_saved_schemes, delete_scheme, load_scheme, get_scheme_info, generate_summary_table

from service.logger import get_logger
from service.validator import validate_overall, validate_beam, show_errors, show_warnings

try:
    from logic.advanced.gust_loads import compute_gust_load
    from logic.advanced.airfoil_geometry import generate_naca4, load_dat, compute_area_perimeter
    from logic.advanced.refined_checks import interaction_check, independent_shear_check
    ADV_AVAIL = True
except ImportError:
    ADV_AVAIL = False

G = 9.81

update_activity()
st.set_page_config(page_title='低空联翼式飞艇结构特性估算', page_icon='🪽', layout='wide')
start_watchdog(1800)

mode = st.sidebar.radio("计算模式", ["基础", "高级"], index=0, key="mode_radio")

with st.sidebar:
    st.title('📐 总体参数')
    overall_params = create_input_panel()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 文件操作")
    uploaded_mat = st.sidebar.file_uploader("导入材料库", type=["xlsx", "json", "csv"], key="mat_upload")
    if uploaded_mat is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os_module.path.splitext(uploaded_mat.name)[1]) as tmp:
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
        os_module.unlink(tmp_path)

    show_exit_button()

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
    st.markdown("---")
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
                st.pyplot(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"翼型可视化失败: {e}")
    else:
        st.info("请切换到高级模式并选择精确翼型以查看翼型形状。")

    st.markdown("---")
    st.subheader('飞行器俯视轮廓')
    airfoil_coords_outline = None
    naca_label_outline = None
    if mode == "高级" and ADV_AVAIL and use_precise_airfoil:
        try:
            if airfoil_src == "NACA四位数字" and naca_code:
                xu, yu, xl, yl = generate_naca4(naca_code)
                airfoil_coords_outline = (xu, yu, xl, yl)
                naca_label_outline = naca_code
        except:
            pass
    fig_outline = plot_aircraft_outline(
        overall_params['b'], overall_params['cw'],
        overall_params['tmax'], overall_params['r_env'],
        overall_params.get('r_env_long', 0.15),
        overall_params['D_rotor'], overall_params['delta'],
        airfoil_coords=airfoil_coords_outline,
        naca_label=naca_label_outline)
    st.pyplot(fig_outline, use_container_width=True)

    st.markdown("---")
    st.subheader('展向弯矩与剪力分布')
    if st.button("生成弯矩/剪力分布图"):
        try:
            loads_for_viz = compute_design_loads(
                WTO=overall_params['WTO'], kL=overall_params['kL'],
                nvtol=overall_params['nvtol'], fs=overall_params['fs'],
                b=overall_params['b'], r_env=overall_params['r_env'],
                D_rotor=overall_params['D_rotor'], delta=overall_params['delta'],
                cw=overall_params['cw'], rho=overall_params['rho'],
                V_cruise=overall_params['V_cruise'], Cm0=overall_params['Cm0'],
                W_payload=other_params['W_payload'],
                W_cargo_width=other_params['W_cargo_width'])
            fig_moment = plot_moment_distribution(
                loads_for_viz, overall_params['WTO'], overall_params['kL'],
                overall_params['b'], 0.8,
                overall_params['cw'], overall_params['V_cruise'])
            st.pyplot(fig_moment, use_container_width=True)
        except Exception as e:
            st.error(f"弯矩分布图生成失败: {e}")

with tab5:
    st.header('📊 计算结果')
    _, calc_col, _ = st.columns([1, 1, 1])
    with calc_col:
        calc_clicked = st.button('⚡ 开始计算', type='primary', use_container_width=True)

    if calc_clicked:
        err, warn = validate_overall(overall_params)
        err += validate_beam(beam_params)
        if err:
            show_errors(err)
        else:
            if warn:
                show_warnings(warn)
            try:
                if mode == "高级" and ADV_AVAIL:
                    loads = compute_design_loads_advanced(
                        WTO=overall_params['WTO'], kL=overall_params['kL'],
                        nvtol=overall_params['nvtol'], fs=overall_params['fs'],
                        b=overall_params['b'], r_env=overall_params['r_env'],
                        D_rotor=overall_params['D_rotor'], delta=overall_params['delta'],
                        cw=overall_params['cw'], rho=overall_params['rho'],
                        V_cruise=overall_params['V_cruise'], Cm0=overall_params['Cm0'],
                        W_payload=other_params['W_payload'],
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

                if mode == "高级" and ADV_AVAIL:
                    beam_result = compute_beam_advanced(
                        loads=loads, beam_type=beam_params['beam_type'],
                        section_type_front=beam_params.get('section_type_front', 'tube'),
                        section_type_rear=beam_params.get('section_type_rear', 'tube'),
                        front_params=beam_params.get('front_params', {}),
                        rear_params=beam_params.get('rear_params', {}),
                        k_reinforce=beam_params.get('k_reinforce', 0.0))
                    rib_result = compute_ribs_advanced(
                        tmax=overall_params['tmax'], cw=overall_params['cw'],
                        n_rib=rib_params['n_rib'], t_rib=rib_params['t_rib'],
                        fill_rib=rib_params['fill_rib'], rho_rib=rib_params['rho_rib'],
                        E_rib=rib_params['E_rib'], n_rib_rein=rib_params['n_rib_rein'],
                        t_rib_rein=rib_params['t_rib_rein'], fill_rib_rein=rib_params['fill_rib_rein'],
                        rho_rib_rein=rib_params['rho_rib_rein'], V_root=loads['V_root'],
                        M_root=loads['M_root'])
                    skin_result = compute_skin_advanced(
                        b=overall_params['b'], cw=overall_params['cw'],
                        tmax=overall_params['tmax'], t_skin=skin_params['t_skin'],
                        rho_skin=skin_params['rho_skin'], E_skin=skin_params['E_skin'],
                        tau_allow=skin_params['tau_allow'], T=loads['T_aero'],
                        d_rib=rib_params['d_rib'])
                else:
                    beam_result = compute_beam(
                        loads=loads, beam_type=beam_params['beam_type'],
                        section_type_front=beam_params.get('section_type_front', 'tube'),
                        section_type_rear=beam_params.get('section_type_rear', 'tube'),
                        front_params=beam_params.get('front_params', {}),
                        rear_params=beam_params.get('rear_params', {}),
                        k_reinforce=beam_params.get('k_reinforce', 0.0))
                    rib_result = compute_ribs(
                        tmax=overall_params['tmax'], cw=overall_params['cw'],
                        n_rib=rib_params['n_rib'], t_rib=rib_params['t_rib'],
                        fill_rib=rib_params['fill_rib'], rho_rib=rib_params['rho_rib'],
                        E_rib=rib_params['E_rib'], n_rib_rein=rib_params['n_rib_rein'],
                        t_rib_rein=rib_params['t_rib_rein'], fill_rib_rein=rib_params['fill_rib_rein'],
                        rho_rib_rein=rib_params['rho_rib_rein'], V_root=loads['V_root'])
                    skin_result = compute_skin(
                        b=overall_params['b'], cw=overall_params['cw'],
                        tmax=overall_params['tmax'], t_skin=skin_params['t_skin'],
                        rho_skin=skin_params['rho_skin'], E_skin=skin_params['E_skin'],
                        tau_allow=skin_params['tau_allow'], T=loads['T_aero'],
                        d_rib=rib_params['d_rib'])

                envelope_result = compute_envelope(m_env=other_params['m_env'])
                gear_result = compute_gear(WTO=overall_params['WTO'], k_gear=other_params['k_gear'])
                cargo_result = compute_cargo_structure(
                    L=other_params['L_cargo'], W=other_params['W_cargo'],
                    H=other_params['H_cargo'], t_cargo=other_params['t_cargo'],
                    rho_cargo=other_params['rho_cargo'])
                extra_result = compute_extra(W_extra=other_params['W_extra'])

                W_wing = beam_result['W_beam'] + rib_result['W_ribs_total'] + skin_result['W_skin']
                W_other = (envelope_result['W_env'] + gear_result['W_gear'] +
                           cargo_result['W_cargo'] + extra_result['W_extra'])
                W_struct = (W_wing + W_other) * (1 + overall_params.get('k_sec', 0.2))
                W_remain = overall_params['WTO'] - W_struct

                st.session_state['res'] = {
                    'loads': loads, 'beam': beam_result, 'ribs': rib_result,
                    'skin': skin_result, 'envelope': envelope_result,
                    'gear': gear_result, 'cargo': cargo_result, 'extra': extra_result,
                    'W_wing': W_wing, 'W_other': W_other,
                    'W_struct': W_struct, 'W_remain': W_remain,
                    'WTO': overall_params['WTO'],
                    'beam_params': beam_params, 'skin_params': skin_params,
                    'components': {
                        '梁': beam_result['W_beam'], '翼肋': rib_result['W_ribs_total'],
                        '蒙皮': skin_result['W_skin'], '气囊': envelope_result['W_env'],
                        '起落架': gear_result['W_gear'], '载货仓': cargo_result['W_cargo'],
                        '额外': extra_result['W_extra']
                    }
                }
            except Exception as e:
                st.error(f"计算错误: {e}")

    if 'res' in st.session_state:
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

        st.markdown('---')
        st.subheader('🔬 强度校核')
        beam = res['beam']
        skin = res['skin']

        if beam_params.get('beam_type') == 'double':
            colF, colR = st.columns(2)
            with colF:
                st.write('**前梁弯曲**')
                fc = beam.get('front', {})
                M_front = beam.get('M_front', 0)
                M_allow_f = beam.get('M_allow_front', 0)
                st.write(f'设计弯矩: {M_front:.2f} N·m  |  许用弯矩: {M_allow_f:.2f} N·m')
                sigma_f = fc.get('sigma_b', 0)/1e6
                st.write(f'应力 {sigma_f:.2f} MPa (许用 {fc.get("sigma_allow", 0)/1e6:.1f} MPa)')
                if fc.get('bend_ok'): st.success('✅ 通过')
                else: st.error('❌ 不通过')
                st.write('**前梁剪切**')
                tau_f = fc.get('tau', 0)/1e6
                st.write(f'应力 {tau_f:.2f} MPa (许用 {fc.get("tau_allow", 0)/1e6:.1f} MPa)')
                if fc.get('shear_ok'): st.success('✅ 通过')
                else: st.error('❌ 不通过')
            with colR:
                st.write('**后梁弯曲**')
                rc = beam.get('rear', {})
                if rc:
                    M_rear = beam.get('M_rear', 0)
                    M_allow_r = beam.get('M_allow_rear', 0)
                    st.write(f'设计弯矩: {M_rear:.2f} N·m  |  许用弯矩: {M_allow_r:.2f} N·m')
                    sigma_r = rc.get('sigma_b', 0)/1e6
                    st.write(f'应力 {sigma_r:.2f} MPa (许用 {rc.get("sigma_allow", 0)/1e6:.1f} MPa)')
                    if rc.get('bend_ok'): st.success('✅ 通过')
                    else: st.error('❌ 不通过')
                    st.write('**后梁剪切**')
                    tau_r = rc.get('tau', 0)/1e6
                    st.write(f'应力 {tau_r:.2f} MPa (许用 {rc.get("tau_allow", 0)/1e6:.1f} MPa)')
                    if rc.get('shear_ok'): st.success('✅ 通过')
                    else: st.error('❌ 不通过')
                else:
                    st.write('无后梁数据')
        else:
            colA, colB = st.columns(2)
            with colA:
                st.write('**主梁弯曲**')
                M_root = res['loads'].get('M_root', 0)
                M_allow = beam.get('M_allow', 0)
                st.write(f'设计弯矩: {M_root:.2f} N·m  |  许用弯矩: {M_allow:.2f} N·m')
                sigma = beam.get('sigma_b', 0)/1e6
                allow = beam.get('sigma_allow', 0)/1e6
                st.write(f'应力 {sigma:.2f} MPa (许用 {allow:.1f} MPa)')
                if beam.get('bend_ok'): st.success('✅ 弯曲通过')
                else: st.error('❌ 弯曲不通过')
                st.write('**主梁剪切**')
                tau = beam.get('tau_beam', 0)/1e6
                tau_a = beam.get('tau_allow', 0)/1e6
                st.write(f'应力 {tau:.2f} MPa (许用 {tau_a:.1f} MPa)')
                if beam.get('shear_ok'): st.success('✅ 剪切通过')
                else: st.error('❌ 剪切不通过')
            with colB:
                st.write('**蒙皮剪切**')
                tskin = skin.get('tau_skin', 0)/1e6
                tcr = skin.get('tau_cr', 0)/1e6
                st.write(f'剪应力 {tskin:.2f} MPa | 临界 {tcr:.2f} MPa')
                if skin.get('shear_ok'): st.success('✅ 蒙皮通过')
                else: st.error('❌ 蒙皮屈曲')

        st.markdown('---')
        st.subheader('⚖️ 重量-强度平衡建议')
        suggestions = []
        bend_margin = (beam.get('sigma_allow', 0) - beam.get('sigma_b', 0)) / beam.get('sigma_allow', 1) * 100 if beam.get('sigma_allow', 0) > 0 else 0
        shear_margin = (beam.get('tau_allow', 0) - beam.get('tau_beam', 0)) / beam.get('tau_allow', 1) * 100 if beam.get('tau_allow', 0) > 0 else 0
        if bend_margin > 40:
            suggestions.append('主梁弯曲裕度较大，可适当减小梁截面尺寸以减轻重量。')
        elif not beam.get('bend_ok'):
            suggestions.append('主梁弯曲强度不足！请增大梁截面或选用更高强度材料。')
        if shear_margin > 40:
            suggestions.append('主梁剪切裕度较大，腹板厚度可适当减小。')
        elif not beam.get('shear_ok'):
            suggestions.append('主梁剪切强度不足！需增加腹板或壁厚。')
        if not skin.get('shear_ok'):
            suggestions.append('蒙皮剪切失稳！考虑增加蒙皮厚度或减小翼肋间距。')
        if suggestions:
            for s in suggestions: st.info(s)
        else:
            st.success('当前设计各安全裕度适中，重量与强度达到较好平衡。')

        # 方案管理
        st.markdown('---')
        st.subheader("📁 方案管理")
        with st.expander("💾 保存 / 📂 加载", expanded=True):
            col_save, col_load = st.columns(2)
            with col_save:
                if st.button("💾 保存当前方案", key="save_scheme_btn_final", use_container_width=True):
                    current_params = {}
                    current_params.update(overall_params)
                    current_params.update(beam_params)
                    current_params.update(rib_params)
                    current_params.update(skin_params)
                    current_params.update(other_params)
                    if 'res' in st.session_state:
                        current_params.update(st.session_state['res'])
                    filepath = save_scheme(current_params)
                    st.success(f"方案已保存至: {os_module.path.basename(filepath)}")
            with col_load:
                uploaded_scheme = st.file_uploader("加载方案文件 (JSON)", type=["json"], key="load_scheme_uploader_final")
                if uploaded_scheme is not None:
                    loaded_params = load_scheme_from_uploaded(uploaded_scheme)
                    if loaded_params:
                        if st.button("✅ 应用加载的方案", key="apply_loaded_btn_final", use_container_width=True):
                            apply_scheme(loaded_params)
        with st.expander("📤 导出 / 📊 对比", expanded=False):
            col_export, col_compare = st.columns(2)
            with col_export:
                if st.button("📥 导出当前计算结果", key="export_result_btn_final", use_container_width=True):
                    if 'res' in st.session_state:
                        export_dir = create_export_folder("single_export")
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        folder_path = os_module.path.join(export_dir, f"result_{timestamp}")
                        os_module.makedirs(folder_path, exist_ok=True)
                        export_scheme_to_folder({**overall_params, **beam_params, **rib_params, **skin_params, **other_params}, folder_path, "params_")
                        if 'res' in st.session_state:
                            export_scheme_to_folder(st.session_state['res'], folder_path, "results_")
                        st.success(f"结果已导出至: {folder_path}")
                    else:
                        st.warning("请先进行计算")
            with col_compare:
                compare_file = st.file_uploader("上传对比方案", type=["json"], key="compare_uploader_final")
                if compare_file is not None:
                    compare_params = load_scheme_from_uploaded(compare_file)
                    if compare_params and 'res' in st.session_state:
                        if st.button("📋 生成对比报告", key="gen_compare_btn_final", use_container_width=True):
                            full_current = {}
                            full_current.update(overall_params)
                            full_current.update(beam_params)
                            full_current.update(rib_params)
                            full_current.update(skin_params)
                            full_current.update(other_params)
                            if 'res' in st.session_state:
                                full_current.update(st.session_state['res'])
                            report = compare_schemes_detailed(full_current, compare_params)
                            st.markdown(report)
        with st.expander("📋 已保存方案列表", expanded=False):
            saved_files = list_saved_schemes()
            if saved_files:
                for f in saved_files:
                    info = get_scheme_info(f)
                    col_name, col_del = st.columns([4, 1])
                    with col_name:
                        st.text(f"📄 {info['name']} ({info['mtime']})")
                    with col_del:
                        if st.button("🗑️", key=f"del_btn_{f.replace('.','_').replace('\\\\','_')}", help="删除此方案"):
                            if delete_scheme(f):
                                st.success("已删除")
                                st.rerun()
            else:
                st.text("暂无已保存方案")

st.markdown('---')
st.caption('AeroStructCalc v2.0 · 稳定版')
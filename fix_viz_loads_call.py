# fix_viz_loads_call.py —— 修复可视化选项卡中 compute_design_loads 多余的 bfuse 参数

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 定位到可视化选项卡中生成弯矩图的那一段
old_block = '''            loads_for_viz = compute_design_loads(
                WTO=overall_params['WTO'], kL=overall_params['kL'],
                nvtol=overall_params['nvtol'], fs=overall_params['fs'],
                b=overall_params['b'], r_env=overall_params['r_env'],
                D_rotor=overall_params['D_rotor'], delta=overall_params['delta'],
                cw=overall_params['cw'], rho=overall_params['rho'],
                V_cruise=overall_params['V_cruise'], Cm0=overall_params['Cm0'],
                W_payload=other_params['W_payload'],
                W_cargo_width=other_params['W_cargo_width'])'''

new_block = '''            loads_for_viz = compute_design_loads(
                WTO=overall_params['WTO'], kL=overall_params['kL'],
                nvtol=overall_params['nvtol'], fs=overall_params['fs'],
                b=overall_params['b'], r_env=overall_params['r_env'],
                D_rotor=overall_params['D_rotor'], delta=overall_params['delta'],
                cw=overall_params['cw'], rho=overall_params['rho'],
                V_cruise=overall_params['V_cruise'], Cm0=overall_params['Cm0'],
                W_payload=other_params['W_payload'],
                W_cargo_width=other_params['W_cargo_width'])'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 已移除弯矩图生成中的多余 bfuse 参数。请重启 Streamlit。")
else:
    print("⚠️ 未找到目标代码段，请手动检查 main.py 中的 'loads_for_viz = compute_design_loads(' 附近。")

"""
输入数据校验模块
提供各类参数的合理性检查，并返回警告信息列表
"""

def validate_overall_params(params):
    """校验总体参数"""
    warnings = []
    # 起飞重量
    if params.get('WTO', 0) <= 0:
        warnings.append("起飞重量 WTO 必须大于 0")
    # 展长与机身宽度
    b = params.get('b', 0)
    bfuse = params.get('bfuse', 0)
    if b <= bfuse:
        warnings.append("机翼展长 b 必须大于机身宽度 bfuse")
    # 气囊升力占比
    kL = params.get('kL', 0.5)
    if not (0 <= kL <= 1):
        warnings.append("气囊升力占比 kL 应在 0~1 之间")
    # 安全系数
    fs = params.get('fs', 1.5)
    if fs < 1.0:
        warnings.append("安全系数 fs 通常不小于 1.0")
    return warnings

def validate_beam_params(params):
    """校验梁参数"""
    warnings = []
    if params.get('t', 0) <= 0:
        warnings.append("梁壁厚/缘条厚度必须为正")
    if params.get('D', 0) <= 0 and params.get('h', 0) <= 0:
        warnings.append("梁尺寸 (外径或高度) 未指定")
    return warnings

def validate_skin_params(params):
    """校验蒙皮参数"""
    warnings = []
    if params.get('t_skin', 0) <= 0:
        warnings.append("蒙皮厚度必须为正")
    return warnings

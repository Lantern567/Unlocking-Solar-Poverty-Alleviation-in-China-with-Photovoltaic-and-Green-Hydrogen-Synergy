import pandas as pd
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

def calculate_p_values(poverty_data: pd.DataFrame, params: dict, state_code: int) -> dict:
    """根据 state_code 和相关数据计算每个县不同销售模式下的收入系数 P。

    Args:
        poverty_data: 包含县级数据的 DataFrame，需要包含 'PV_price', 'Hydrogen_Min', 'Hydrogen_Max', 
                      以及根据 state_code 可能需要的 'Peak_Price', 'Dhp_p', 'Dht_p' 列。
        params: 包含参数的字典。
        state_code: 当前处理的状态码 (3, 4, 5, 6)。

    Returns:
        一个字典 P，键是县的索引，值是包含四种销售模式对应 P 值的列表。
        P[i][0] = 自用氢 (通常为0?)
        P[i][1] = 调峰电
        P[i][2] = 第三项 (未使用，为0)
        P[i][3] = 销售氢
    """
    logger.info(f"状态码={state_code}：开始计算收入系数 P 值...")
    P = {}
    num_counties = len(poverty_data)

    # 检查通用列
    required_general_cols = ['PV_price', 'Hydrogen_Min', 'Hydrogen_Max']
    if not all(col in poverty_data.columns for col in required_general_cols):
        missing = [col for col in required_general_cols if col not in poverty_data.columns]
        logger.error(f"P 值计算缺少通用列: {missing}。将为所有县返回默认 P 值 [0, 0, 0, 0]。")
        return {i: [0, 0, 0, 0] for i in poverty_data.index}

    # 根据 state_code 检查特定列
    if state_code == 5: # ROI_E 需要 Dhp_p, Dht_p
        required_specific_cols = ['Dhp_p', 'Dht_p']
        if not all(col in poverty_data.columns for col in required_specific_cols):
            missing = [col for col in required_specific_cols if col not in poverty_data.columns]
            logger.error(f"P 值计算 (state=5) 缺少特定列: {missing}。将为所有县返回默认 P 值 [0, 0, 0, 0]。")
            return {i: [0, 0, 0, 0] for i in poverty_data.index}
    elif state_code == 6: # ROI_C 需要 Peak_Price
        required_specific_cols = ['Peak_Price']
        if 'Peak_Price' not in poverty_data.columns:
            logger.warning(f"P 值计算 (state=6) 缺少 'Peak_Price' 列，将尝试使用 'PV_price' 代替。")
            # 如果需要严格要求，可以在这里返回错误

    # 循环计算每个县的 P 值
    for i in poverty_data.index:
        row = poverty_data.loc[i]
        P_values = [0, 0, 0, 0] # 初始化 [自用, 调峰, 未使用, 销售]

        try:
            if state_code == 5: # ROI_E 场景
                # P[i][0] = 0 (自用)
                P_values[1] = row['PV_price'] # 调峰电价格 = PV上网电价
                # P[i][2] = 0 (未使用)
                # 销售氢价格 = Dhp_p 和 Dht_p 的最小值 (来自 _calculate_distance_prices)
                P_values[3] = min(row['Dhp_p'], row['Dht_p']) 
            elif state_code == 6: # ROI_C 场景
                # P[i][0] = 0
                # 调峰电价格 = Peak_Price (如果存在) 或 PV_price
                peak_price = row.get('Peak_Price', row['PV_price']) 
                P_values[1] = peak_price 
                # P[i][2] = 0
                # 销售氢价格 = Hydrogen_Min 和 Hydrogen_Max 的平均值
                P_values[3] = (row['Hydrogen_Min'] + row['Hydrogen_Max']) / 2 
            else: # 默认场景 (state_code 3 或 4, Hydrogen_Y/M)
                # P[i][0] = 0
                P_values[1] = row['PV_price'] # 调峰电价格 = PV上网电价
                # P[i][2] = 0
                # 销售氢价格 = Hydrogen_Min 和 Hydrogen_Max 的平均值
                P_values[3] = (row['Hydrogen_Min'] + row['Hydrogen_Max']) / 2 
            
            P[i] = P_values
        except KeyError as e:
            logger.error(f"计算县索引 {i} 的 P 值时缺少列: {e}。将使用默认值 [0, 0, 0, 0]。")
            P[i] = [0, 0, 0, 0]
        except Exception as e_calc:
            logger.error(f"计算县索引 {i} 的 P 值时出错: {e_calc}", exc_info=True)
            P[i] = [0, 0, 0, 0]

    logger.info(f"状态码={state_code}：收入系数 P 值计算完成。")
    return P

def calculate_distance_prices(poverty_data: pd.DataFrame, params: dict, state_code: int, transport_cost_func: callable, base_path: str = None) -> pd.DataFrame:
    """计算 ROI_E (state_code=5) 场景下基于距离的氢销售价格 Dhp_p 和 Dht_p。

    读取 vertical.xlsx 和 node.xlsx 文件中预定义的与最近距离相关的价格，
    然后通过比较管道和罐车的运输成本，选择更经济的价格。

    Args:
        poverty_data: 包含县级数据的 DataFrame，需要 'name', 'dim', 'din', 'Q'.
        params: 参数字典，需要管道和罐车成本参数 (Cpi, Csa_p, Spip, Fpi, Fai).
        state_code: 当前状态码。只有当 state_code == 5 时才执行计算。
        transport_cost_func: 一个函数，输入距离(米)返回单位运输成本(元/kg).通常是 CostCalculator 实例的方法.
        base_path: Excel 文件所在目录的路径。如果为 None，则假定在脚本所在目录的父目录下的 '数据存储' 文件夹。

    Returns:
        如果 state_code == 5，返回添加了 'dim_p', 'din_p', 'Dhp_p', 'Dht_p' 列的 DataFrame。
        否则，返回原始 DataFrame。
    """
    if state_code != 5:
        logger.info(f"非 ROI_E 场景 (state={state_code})，跳过距离价格计算。")
        return poverty_data

    logger.info(f"状态码={state_code}：开始计算距离价格 (Dhp_p, Dht_p)...")
    poverty_data_copy = poverty_data.copy()

    # --- 文件路径 --- 
    if base_path is None:
        # 默认路径结构: ../数据存储/file.xlsx 相对于当前脚本
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.join(os.path.dirname(current_script_dir), '数据存储') 
        logger.info(f"未提供 base_path，假设数据文件位于: {base_path}")
        
    vertical_file = os.path.join(base_path, "vertical.xlsx")
    node_file = os.path.join(base_path, "node.xlsx")

    # --- 读取外部价格数据 --- 
    try:
        vertical_prices = pd.read_excel(vertical_file)
        node_prices = pd.read_excel(node_file)
        logger.info(f"成功读取价格文件: {os.path.basename(vertical_file)}, {os.path.basename(node_file)}")
    except FileNotFoundError as e:
        logger.error(f"距离价格文件未找到: {e}。无法计算 Dhp_p, Dht_p。")
        return poverty_data # 返回原始数据
    except Exception as e_read:
        logger.error(f"读取距离价格文件时出错: {e_read}", exc_info=True)
        return poverty_data

    # --- 检查所需列 --- 
    required_poverty_cols = ['name', 'dim', 'din', 'Q']
    if not all(col in poverty_data_copy.columns for col in required_poverty_cols):
        missing = [col for col in required_poverty_cols if col not in poverty_data_copy.columns]
        logger.error(f"Poverty data 缺少计算距离价格所需的列: {missing}。")
        return poverty_data
        
    required_vertical_cols = ['县名', '县中心距离(km)', '调整后价格'] # 假设列名
    if not all(col in vertical_prices.columns for col in required_vertical_cols):
        missing = [col for col in required_vertical_cols if col not in vertical_prices.columns]
        logger.error(f"Vertical price 文件 ({os.path.basename(vertical_file)}) 缺少列: {missing}。")
        return poverty_data
        
    required_node_cols = ['县名', '距离(km)', '节点价格'] # 假设列名
    if not all(col in node_prices.columns for col in required_node_cols):
        missing = [col for col in required_node_cols if col not in node_prices.columns]
        logger.error(f"Node price 文件 ({os.path.basename(node_file)}) 缺少列: {missing}。")
        return poverty_data

    # --- 提取成本参数 (需要从 params 获取) --- 
    try:
        Cpi = params['Cpi']
        Csa_p = params['Csa_p']
        Spip = params['Spip']
        Fpi = params['Fpi']
        Fai = params['Fai']
        N = params.get('N', 20) # 运营年限
    except KeyError as e_param:
        logger.error(f"参数字典中缺少计算距离价格所需的成本参数: {e_param}。")
        return poverty_data

    # --- 计算逻辑 --- 
    dim_p_list = []
    din_p_list = []
    dhp_p_list = []
    dht_p_list = []

    # 内部辅助函数：查找匹配县名的最小距离对应的价格
    def get_price_for_min_distance(target_name: str, price_df: pd.DataFrame, name_col: str, dist_col: str, price_col: str) -> float:
        matched_rows = price_df[price_df[name_col] == target_name]
        if not matched_rows.empty:
            min_dist_row = matched_rows.loc[matched_rows[dist_col].idxmin()]
            return min_dist_row[price_col]
        else:
            # logger.warning(f"在 {price_df.name} 中未找到县 '{target_name}' 的匹配项，返回默认价格 0。") # 添加文件名信息
            return 0.0 # 返回默认价格 0
    
    # 添加文件名到 DataFrame 以改进日志记录
    vertical_prices.name = os.path.basename(vertical_file) 
    node_prices.name = os.path.basename(node_file)

    for i in poverty_data_copy.index:
        row = poverty_data_copy.loc[i]
        county_name = row['name']
        dim = row['dim'] # 米
        din = row['din'] # 米
        Q = row['Q'] # 年产量 m³
        
        # 1. 查找与 dim 和 din 对应的预定义价格
        dim_p = get_price_for_min_distance(county_name, vertical_prices, '县名', '县中心距离(km)', '调整后价格')
        din_p = get_price_for_min_distance(county_name, node_prices, '县名', '距离(km)', '节点价格')
        dim_p_list.append(dim_p)
        din_p_list.append(din_p)

        # 2. 比较运输成本以决定选择哪个价格 (Dhp_p, Dht_p)
        # 这部分逻辑与 _calculate_transport_distances 类似，但用于选择价格
        try:
            # 管道成本比较 (基于 N 年总成本)
            cost_pipe_dim = dim * Cpi + Fpi + (dim * Csa_p + dim * Spip * Q) * N 
            cost_pipe_din = din * Cpi + Fpi + (din * Csa_p + din * Spip * Q) * N 
            # 注意: 备份文件在比较 din 成本时似乎省略了 Fpi 和 Csa_p/Spip 项，这里遵循完整比较
            # cost_pipe_din_backup_logic = din * Cpi # 备份文件逻辑? 
            dhp_p = din_p if cost_pipe_dim >= cost_pipe_din else dim_p

            # 罐车成本比较 (基于 N 年总成本 + 固定成本 Fai)
            # 需要转换 Q (m³/year) 到 kg/year? 假设 transport_cost_func 返回 元/kg
            # kg_per_m3 = params.get('kg_per_m3', 0.0899) # 氢气密度
            # Q_kg = Q * kg_per_m3 
            # 假设 transport_cost_func 的成本单位与 Q 的单位匹配 (例如 元/m³)，或者 Q 本身就是 kg
            # 如果 Q 是 m³, transport_cost_func 是元/kg, 需要转换 Q 或 transport_cost_func
            # 假设 Q 的单位与 transport_cost_func 兼容 (比如 Q 是 kg, func 是 元/kg)
            
            # 检查 transport_cost_func 是否有效
            if not callable(transport_cost_func):
                 logger.error("传递的 transport_cost_func 无效。无法计算 Dht_p。")
                 dht_p = 0.0 # 设置默认值
            else:
                cost_truck_dim = transport_cost_func(dim) * N * Q + Fai
                cost_truck_din = transport_cost_func(din) * N * Q + Fai 
                # 备份文件逻辑似乎是: cost_truck_dim_compare = transport_cost_func(dim) * Q + Fai; cost_truck_din_compare = transport_cost_func(din) * Q
                # 这里也使用完整比较逻辑
                dht_p = din_p if cost_truck_dim >= cost_truck_din else dim_p
               
        except Exception as e_cost_compare:
            logger.error(f"比较县 {county_name} (索引 {i}) 的运输成本以确定价格时出错: {e_cost_compare}", exc_info=True)
            dhp_p = 0.0 # 默认值
            dht_p = 0.0 # 默认值
            
        dhp_p_list.append(dhp_p)
        dht_p_list.append(dht_p)

    # --- 添加新列到 DataFrame --- 
    poverty_data_copy['dim_p'] = dim_p_list
    poverty_data_copy['din_p'] = din_p_list
    poverty_data_copy['Dhp_p'] = dhp_p_list
    poverty_data_copy['Dht_p'] = dht_p_list

    logger.info(f"状态码={state_code}：距离价格 (Dhp_p, Dht_p) 计算完成。")
    return poverty_data_copy 
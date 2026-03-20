import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def prepare_hydrogen_data(poverty_data: pd.DataFrame, params: dict) -> pd.DataFrame:
    """准备氢能计算所需的特定数据列，特别是计算 'Q' (年产氢量 m³)。

    基于备份文件的逻辑，使用 'mean_tiff', 'Curtailed_Rate' 和参数中的固定值。
    Cfa (设施成本) 不在此计算，应由 CostCalculator 处理。

    Args:
        poverty_data: 包含原始数据的 DataFrame，需要 'mean_tiff' 和 'Curtailed_Rate' 列。
        params: 包含参数的字典，需要 'pv_x' 和 'alpha' (电解水效率)。

    Returns:
        添加了 'Electri' 和 'Q' 列的 DataFrame。如果缺少必要输入则返回原始 DataFrame。
    """
    logger.info("开始准备氢能特定数据 (计算 Electri 和 Q)...")
    poverty_data_copy = poverty_data.copy()

    # 获取参数
    pv_x = params.get('pv_x', 10000) # 光伏装机容量因子 (来自备份)
    alpha_eff = params.get('alpha', 1/4.5) # 电解水效率 (m³/kWh) (来自备份)

    # 检查所需列
    required_cols = ['mean_tiff', 'Curtailed_Rate']
    if not all(col in poverty_data_copy.columns for col in required_cols):
        missing = [col for col in required_cols if col not in poverty_data_copy.columns]
        logger.error(f"输入数据缺少必要的列: {missing}。无法计算 Electri 和 Q，将返回原始数据。")
        return poverty_data # 返回未修改的数据

    try:
        # 计算 'Electri' (弃电量 kWh?)
        poverty_data_copy['Electri'] = poverty_data_copy['mean_tiff'] * poverty_data_copy['Curtailed_Rate'] * pv_x
        logger.info(f"计算得到的 'Electri' 值范围: {poverty_data_copy['Electri'].min():.2f} - {poverty_data_copy['Electri'].max():.2f}")

        # 计算 'Q' (年产氢量 m³)
        poverty_data_copy['Q'] = poverty_data_copy['Electri'] * alpha_eff
        logger.info(f"计算得到的 'Q' (年产氢量 m³) 值范围: {poverty_data_copy['Q'].min():.2f} - {poverty_data_copy['Q'].max():.2f}")

        # 不再计算或添加空的 Cfa 列
        # logger.info("'Cfa' 列将由 CostCalculator 计算。")

    except Exception as e:
        logger.error(f"准备氢能数据 (Electri, Q) 时出错: {e}", exc_info=True)
        # 出错时返回原始数据，避免部分计算结果污染后续步骤
        return poverty_data

    logger.info("氢能特定数据 (Electri, Q) 准备完成。")
    return poverty_data_copy 
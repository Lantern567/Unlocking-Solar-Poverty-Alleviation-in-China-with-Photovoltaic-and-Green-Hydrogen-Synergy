import logging
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)

class CostCalculator:
    """封装与氢能项目相关的成本计算逻辑。

    这个类负责计算氢设施、运输、光伏系统以及特定场景（ROI_E, ROI_C）的成本。
    """
    def __init__(self, params: dict, poverty_data: pd.DataFrame, state_code: int):
        """初始化 CostCalculator。

        Args:
            params (dict): 包含所有必要成本参数和常量的字典。
            poverty_data (pd.DataFrame): 包含贫困县数据的 DataFrame，需要包含 'Q', 'Cfa', 'Dhp', 'Dht', 'dim', 'din', 'Curtailed_Rate', 'mean_tiff', 'PV_price', 'Discount_Factor', 'production_scale' 等列。
            state_code (int): 当前处理的状态码，用于某些特定逻辑。
        """
        self.params = params
        self.poverty_data = poverty_data.copy() # 创建副本以避免修改原始数据
        self.state_code = state_code
        
        # 从 params 解包常量以便于访问
        self.Cpi = params.get('Cpi', 0)
        self.Csa_p = params.get('Csa_p', 0)
        self.Spip = params.get('Spip', 0)
        self.Fpi = params.get('Fpi', 0)
        self.Fai = params.get('Fai', 0)
        self.Cas = params.get('Cas', 0)
        self.Cadi = params.get('Cadi', 0)
        self.Csa_h_param = params.get('Csa_h', []) # Csa_h 是一个列表或数组
        self.Csa_d = params.get('Csa_d', 0)
        self.Ca = params.get('Ca', 0)
        self.Csa_a = params.get('Csa_a', 0)
        self.N = params.get('N', 20) # 默认运营年限
        self.C_PV = params.get('C_PV', 0)
        self.C_ES = params.get('C_ES', 0)
        self.O_PV = params.get('O_PV', 0)
        self.O_ES = params.get('O_ES', 0)
        self.C_F = params.get('C_F', 0)
        self.C_tax = params.get('C_tax', 0)
        self.e = params.get('e', 0) # ROI_C 特定参数
        self.Csa_sf = params.get('Csa_sf', 0) # ROI_E/ROI_C 特定参数
        self.a_cost = params.get('a_cost', 0) # ROI_E 特定参数

        # 其他初始化
        self.hydrogen_sales_types = params.get('hydrogen_sales_types', [0, 1, 2, 3]) 
        self.transport_methods = [0, 1, 2]  # 0:不需要运输 1:罐车 2:管道
        self.Cinvest_values = {}
        self.Com_values = {}
        self.Ctrans_values = {}
        self.pv_total_cost = {}
        self.pv_revenue = {}
        self.Csa_h = {} # 需要根据 poverty_data 计算

        # 初始化运输成本函数
        self._initialize_transport_cost_function()
        
        # 预计算 Csa_h
        self._precompute_csa_h()

    def _precompute_csa_h(self):
        """根据 production_scale 预计算 Csa_h。"""
        if len(self.Csa_h_param) < 3:
             logger.warning(f"参数 'Csa_h' 长度不足 ({len(self.Csa_h_param)})，期望至少为 3。将为所有规模使用第一个值。")
             default_csa_h = self.Csa_h_param[0] if self.Csa_h_param else 0
             for i in range(len(self.poverty_data)):
                 self.Csa_h[i] = default_csa_h
             return

        try:
            for i, row in self.poverty_data.iterrows():
                scale = row.get('production_scale')
                if scale == 1:
                    self.Csa_h[i] = self.Csa_h_param[0]
                elif scale == 2:
                    self.Csa_h[i] = self.Csa_h_param[1]
                elif scale == 3:
                    self.Csa_h[i] = self.Csa_h_param[2]
                else:
                    logger.warning(f"县 {i} 的 production_scale ({scale}) 无效或缺失，将使用 Csa_h 的第一个值。")
                    self.Csa_h[i] = self.Csa_h_param[0]
        except KeyError:
            logger.error("数据中缺少 'production_scale' 列，无法计算 Csa_h。将使用 Csa_h 的第一个值。")
            default_csa_h = self.Csa_h_param[0] if self.Csa_h_param else 0
            for i in range(len(self.poverty_data)):
                 self.Csa_h[i] = default_csa_h
        except Exception as e:
            logger.error(f"计算 Csa_h 时出错: {e}", exc_info=True)
            # 提供一个默认值以允许继续运行
            default_csa_h = self.Csa_h_param[0] if self.Csa_h_param else 0
            for i in range(len(self.poverty_data)):
                 self.Csa_h[i] = default_csa_h

    def calculate_all_costs(self):
        """计算所有类型的成本并存储结果。"""
        logger.info(f"状态码={self.state_code}：开始计算所有成本...")
        try:
            self.calculate_hydrogen_facility_cost()
            self.calculate_transport_distances()
            
            # 根据 state_code 选择合适的成本计算方法
            if self.state_code == 5: # ROI_E
                self.calculate_hydrogen_costs_for_roi_e()
            elif self.state_code == 6: # ROI_C
                 self.calculate_hydrogen_costs_for_roi_c()
            else: # Hydrogen_Y, Hydrogen_M 或其他默认场景
                 self.calculate_hydrogen_costs()
                 
            self.calculate_pv_costs_for_hydrogen()
            logger.info(f"状态码={self.state_code}：所有成本计算完成。")
            
            return {
                "invest": self.Cinvest_values,
                "om": self.Com_values,
                "trans": self.Ctrans_values,
                "pv_cost": self.pv_total_cost,
                "pv_revenue": self.pv_revenue,
                "poverty_data_updated": self.poverty_data # 返回可能已更新的数据框 (例如添加了 Dht, Dhp)
            }
        except Exception as e:
            logger.error(f"计算所有成本时出错: {e}", exc_info=True)
            # 返回空的或部分结果，取决于错误发生的位置
            return {
                "invest": self.Cinvest_values,
                "om": self.Com_values,
                "trans": self.Ctrans_values,
                "pv_cost": self.pv_total_cost,
                "pv_revenue": self.pv_revenue,
                "poverty_data_updated": self.poverty_data
            }

    def calculate_hydrogen_facility_cost(self):
        """计算制氢设施相关成本 (Cfa)"""
        logger.info(f"状态码={self.state_code}：开始计算氢设施成本 (Cfa)...")
        # 获取参数
        Cf0 = self.params.get('Cf0', [0, 0, 0])
        Sf0 = self.params.get('Sf0', [0, 0, 0])
        b = self.params.get('b', [0, 0, 0])
        n = self.params.get('n', [1, 1, 1]) # 这个n代表什么需要确认，假设是与年份相关的参数
        Cyear = self.params.get('Cyear', 2023) # 成本基准年

        # 检查参数长度
        if not all(len(lst) == 3 for lst in [Cf0, Sf0, b, n]):
             logger.error("成本模型参数 Cf0, Sf0, b, n 必须包含3个元素。")
             self.poverty_data['Cfa'] = 0 # 设置默认值
             return

        # 成本模型函数
        def cost_model(S, C0, S0, b_val):
            if S <= 0 or S0 <= 0: return np.inf # 避免log(0)或除以0
            return C0 * (S / S0)**b_val

        # 计算每年的累积容量 (这里简化处理，假设只关心一个目标年份)
        # TODO: 需要澄清 n 和 Cyear 的具体用法，以及是否需要计算多年的成本
        # 暂时假设 n 是一个调整因子或指数，Cyear 是目标年份
        # 这里简化为直接使用 production_scale 来选择参数

        cfa_values = []
        for _, row in self.poverty_data.iterrows():
            scale = row.get('production_scale')
            if scale in [1, 2, 3]:
                idx = scale - 1
                S = row.get('Q', 0) # 使用 Q 作为规模 S
                C0_val = Cf0[idx]
                S0_val = Sf0[idx]
                b_val = b[idx]
                # 如何结合 n 和 Cyear 不明确，暂时忽略它们
                # cfa = cost_model(S, C0_val, S0_val, b_val) * n[idx] # 假设 n 是乘数因子
                cfa = cost_model(S, C0_val, S0_val, b_val) 
            else:
                 logger.warning(f"无效的 production_scale ({scale})，Cfa 设置为 0。")
                 cfa = 0
            cfa_values.append(cfa)
            
        self.poverty_data['Cfa'] = cfa_values
        logger.info(f"状态码={self.state_code}：氢设施成本 (Cfa) 计算完成。范围: {self.poverty_data['Cfa'].min():.2f} - {self.poverty_data['Cfa'].max():.2f}")


    def _initialize_transport_cost_function(self):
        """初始化运输成本插值函数"""
        # 从参数中获取运输成本数据点
        transport_distances = self.params.get('Transport_Distance', [0, 50, 100, 200, 500, 1000, 2000]) # 单位: km
        transport_costs = self.params.get('Transport_Cost', [0, 1.5, 2.5, 4.0, 8.0, 15.0, 25.0]) # 单位: 元/kg

        if len(transport_distances) != len(transport_costs) or len(transport_distances) < 2:
            logger.error("运输成本参数 Transport_Distance 和 Transport_Cost 必须长度相同且至少包含两个点。将使用固定成本 0。")
            # 定义一个总是返回 0 的函数
            self._transport_cost_func = lambda d: 0
            return

        # 创建插值函数 (距离单位: km -> 成本单位: 元/kg)
        # 使用 fill_value="extrapolate" 来处理超出范围的距离
        try:
            self._transport_cost_func = interp1d(
                transport_distances, 
                transport_costs, 
                kind='linear', 
                fill_value="extrapolate"
            )
            logger.info("运输成本插值函数已初始化。")
        except Exception as e:
             logger.error(f"初始化运输成本插值函数失败: {e}", exc_info=True)
             self._transport_cost_func = lambda d: 0


    def calculate_transport_cost(self, distance_in_meters):
        """计算给定距离的运输成本 (元/kg)"""
        if distance_in_meters < 0: return 0
        # 将距离从米转换为千米
        distance_in_km = distance_in_meters / 1000.0
        # 使用插值函数计算成本
        cost_per_kg = self._transport_cost_func(distance_in_km)
        return max(0, float(cost_per_kg)) # 确保成本不为负


    def calculate_transport_cost(self, distance_in_meters):
        distance_array = np.asarray(distance_in_meters)
        distance_in_km = distance_array / 1000.0
        cost_per_kg = self._transport_cost_func(distance_in_km)
        cost_per_kg = np.where(distance_array < 0, 0, np.maximum(cost_per_kg, 0))

        if np.isscalar(distance_in_meters):
            return float(cost_per_kg)

        return cost_per_kg.astype(float)

    def calculate_transport_distances(self):
        """计算经济运输距离 Dhp (管道) 和 Dht (罐车)"""
        logger.info(f"状态码={self.state_code}：开始计算运输距离 (Dhp, Dht)...")
        # 确保必要的列存在
        required_cols = ['dim', 'din', 'Q', 'Cfa']
        if not all(col in self.poverty_data.columns for col in required_cols):
            missing = [col for col in required_cols if col not in self.poverty_data.columns]
            logger.error(f"缺少计算运输距离所需的列: {missing}。将设置 Dhp 和 Dht 为 0。")
            self.poverty_data['Dhp'] = 0
            self.poverty_data['Dht'] = 0
            return
            
        # 向量化计算以提高效率
        dim = self.poverty_data['dim'].values
        din = self.poverty_data['din'].values
        Q = self.poverty_data['Q'].values

        # 计算管道运输的成本比较项
        # Cost_pipe_dim = dim * (Cpi + Csa_p * N + Spip * N * Q) + Fpi # 原始公式似乎有误，运维成本应乘以年限N，但运输成本不应乘以N？需要确认 Spip 是单位运量成本还是年总成本
        # 假设 Csa_p 是年运维成本系数，Spip 是单位运量运输成本 (元/kg*m)
        cost_pipe_dim_invest = dim * self.Cpi + self.Fpi # 管道投资成本
        cost_pipe_dim_om = dim * self.Csa_p * self.N # N年管道运维成本
        cost_pipe_dim_trans = dim * self.Spip * self.N * Q # N年管道运输成本（Q为年产量）
        cost_pipe_dim_total = cost_pipe_dim_invest + cost_pipe_dim_om + cost_pipe_dim_trans
        
        cost_pipe_din_invest = din * self.Cpi # 管道投资成本
        cost_pipe_din_om = din * self.Csa_p * self.N # N年管道运维成本
        cost_pipe_din_trans = din * self.Spip * self.N * Q # N年管道运输成本（Q为年产量）
        cost_pipe_din_total = cost_pipe_din_invest + cost_pipe_din_om + cost_pipe_din_trans

        # 计算罐车运输的成本比较项
        # Cost_truck_dim = transport_cost(dim) * N * Q + Fai # Fai 是固定资产投资?
        # 假设 Fai 是罐车的初始投资或其他固定成本
        cost_truck_dim_trans = self.calculate_transport_cost(dim) * self.N * Q
        cost_truck_dim_total = cost_truck_dim_trans + self.Fai # Fai只加一次

        cost_truck_din_trans = self.calculate_transport_cost(din) * self.N * Q
        cost_truck_din_total = cost_truck_din_trans # 如果din < dim，不投资罐车 (Fai=0) ? 这里逻辑需要澄清
        # 假设如果选择 din，则罐车运输不需要额外投资 Fai
        
        # 计算 Dhp
        # 如果 dim 对应的管道总成本 >= din 对应的管道总成本，则选择 din
        self.poverty_data['Dhp'] = np.where(cost_pipe_dim_total >= cost_pipe_din_total, din, dim)

        # 计算 Dht
        # 如果 dim 对应的罐车总成本 >= din 对应的罐车总成本，则选择 din
        # 这里有个逻辑问题：如果 din < dim，选择 din 真的意味着不支付 Fai 吗？
        # 暂时按照原代码逻辑：比较的是运输成本 + Fai vs 运输成本
        # 修正：Fai 应该是与罐车运输本身相关的固定投资，不应依赖于比较 din 和 dim
        # 重新思考：比较应该是 (罐车运dim的总成本) vs (罐车运din的总成本)
        # 假设 Fai 是与罐车运输相关的固定投资，只要选择罐车就需要支付
        cost_truck_dim_total_revised = self.calculate_transport_cost(dim) * self.N * Q + self.Fai
        cost_truck_din_total_revised = self.calculate_transport_cost(din) * self.N * Q + self.Fai # 假设无论din还是dim，都需要Fai
        
        # 原始逻辑似乎是在比较 罐车运dim的变动成本+Fai vs 罐车运din的变动成本
        cost_truck_dim_compare = self.calculate_transport_cost(dim) * self.N * Q + self.Fai
        cost_truck_din_compare = self.calculate_transport_cost(din) * self.N * Q 
        self.poverty_data['Dht'] = np.where(cost_truck_dim_compare >= cost_truck_din_compare, din, dim)


        logger.info(f"状态码={self.state_code}：运输距离计算完成。")
        if not self.poverty_data.empty:
             logger.info(f"- Dhp范围: {self.poverty_data['Dhp'].min()/1000:.2f}km - {self.poverty_data['Dhp'].max()/1000:.2f}km")
             logger.info(f"- Dht范围: {self.poverty_data['Dht'].min()/1000:.2f}km - {self.poverty_data['Dht'].max()/1000:.2f}km")

    def calculate_hydrogen_costs(self):
        """计算不同销售方式和运输方式的投资、运维和运输成本（通用场景）"""
        logger.info(f"状态码={self.state_code}：开始计算氢能成本（通用）...")
        self.Cinvest_values = {}
        self.Com_values = {}
        self.Ctrans_values = {}
        
        # 预计算所有行的运输成本，避免在循环中重复计算
        dht_costs = {dht: self.calculate_transport_cost(dht) for dht in self.poverty_data['Dht'].unique()}

        num_counties = len(self.poverty_data)
        for i in range(num_counties):
            row = self.poverty_data.iloc[i]
            Q = row['Q']
            Cfa = row['Cfa']
            Dhp = row['Dhp']
            Dht = row['Dht']
            dim = row['dim']
            csa_h_i = self.Csa_h.get(i, 0) # 获取预计算的 Csa_h
            dht_cost_i = dht_costs.get(Dht, 0) # 获取预计算的 Dht 成本

            for j_idx, j in enumerate(self.hydrogen_sales_types):
                for k in self.transport_methods:
                    invest_key = (i, j_idx, k)
                    om_key = (i, j_idx, k)
                    trans_key = (i, j_idx, k)

                    if j == 0:  # 自用氢
                        self.Cinvest_values[invest_key] = Cfa + self.Cas * Q + self.Cadi
                        self.Com_values[om_key] = (csa_h_i + self.Csa_d) * self.N * Q
                        self.Ctrans_values[trans_key] = 0
                    elif j == 1:  # 调峰电
                        self.Cinvest_values[invest_key] = Cfa + self.Cas * Q + self.Ca
                        self.Com_values[om_key] = (csa_h_i + self.Csa_a) * self.N * Q
                        self.Ctrans_values[trans_key] = 0
                    elif j == 2:  # 第三项 (假设成本为0)
                        self.Cinvest_values[invest_key] = 0
                        self.Com_values[om_key] = 0
                        self.Ctrans_values[trans_key] = 0
                    elif j == 3:  # 销售氢
                        if k == 1:  # 罐车运输
                            # 原始逻辑：if Dht == dim，投资成本不同
                            # 这似乎暗示 Fpi (管道固定投资?) 只在 Dht==dim 时与罐车运输相关? 逻辑需要确认
                            # 假设 Fpi 是管道固定投资，与罐车无关。罐车固定投资是 Fai
                            # Invest = Cfa (制氢设施) + Fai (罐车固定投资) ?
                            # 简化：假设销售氢的罐车运输，其固定投资包含在 Cfa 中，并需要 Fai
                            # 重新审视原始代码: if Dht == dim: Cinvest = Cfa + Fpi (?) else: Cinvest = Cfa
                            # 这非常奇怪。暂时遵循原逻辑，但标记为需要审查。
                            if Dht == dim:
                                self.Cinvest_values[invest_key] = Cfa + self.Fpi # 为什么是 Fpi?
                            else:
                                self.Cinvest_values[invest_key] = Cfa
                            self.Com_values[om_key] = 0 # 销售氢的运维成本为0?
                            self.Ctrans_values[trans_key] = dht_cost_i * self.N * Q
                        elif k == 2:  # 管道运输
                            # 原始逻辑: if Dhp == dim: Cinvest = Cfa + Dhp*Cpi + Fai (?) else: Cinvest = Cfa + Dhp*Cpi
                            # 这也很奇怪，Fai 似乎是罐车投资。
                            # 假设管道投资是 Cfa + Dhp*Cpi + Fpi
                            if Dhp == dim:
                                self.Cinvest_values[invest_key] = Cfa + Dhp * self.Cpi + self.Fpi # 使用 Fpi 而非 Fai
                            else:
                                self.Cinvest_values[invest_key] = Cfa + Dhp * self.Cpi
                            self.Com_values[om_key] = (csa_h_i + Dhp * self.Csa_p) * self.N # 年运维成本 * N
                            self.Ctrans_values[trans_key] = Dhp * self.Spip * self.N * Q # 年运输成本 * N
                        else:  # k=0 无需运输 (销售给本地?)
                            # 假设本地销售也需要制氢设施成本 Cfa
                            self.Cinvest_values[invest_key] = Cfa
                            self.Com_values[om_key] = csa_h_i * self.N * Q # 只有制氢运维?
                            self.Ctrans_values[trans_key] = 0
                    else: # 其他销售类型 (如果存在)
                         self.Cinvest_values[invest_key] = 0
                         self.Com_values[om_key] = 0
                         self.Ctrans_values[trans_key] = 0
        logger.info(f"状态码={self.state_code}：氢能成本（通用）计算完成。")


    def calculate_pv_costs_for_hydrogen(self):
        """计算每个县的光伏总成本和收益"""
        logger.info(f"状态码={self.state_code}：开始计算光伏成本和收益...")
        required_cols = ['Curtailed_Rate', 'mean_tiff', 'PV_price', 'Discount_Factor']
        if not all(col in self.poverty_data.columns for col in required_cols):
            missing = [col for col in required_cols if col not in self.poverty_data.columns]
            logger.error(f"缺少计算光伏成本/收益所需的列: {missing}。将设置成本和收益为 0。")
            for i in self.poverty_data.index:
                self.pv_total_cost[i] = 0
                self.pv_revenue[i] = 0
            return
            
        self.pv_total_cost = {}
        self.pv_revenue = {}

        # 向量化计算
        pv_invest = self.C_PV + self.C_ES # 光伏和储能的初始投资
        pv_om_annual = self.O_PV + self.O_ES + self.C_F + self.C_tax # 年运维、财务、税费
        
        # 计算总成本 (不考虑折现)
        total_cost_undiscounted = pv_invest + pv_om_annual * self.N 
        # 注意：如果参数已经是 N 年总成本，则不需要乘以 N
        # 假设 C_PV, C_ES 是初始投资，O_PV, O_ES, C_F, C_tax 是年成本
        
        # 计算光伏收益 (非弃电部分)，考虑折扣因子
        alpha = 1 - self.poverty_data['Curtailed_Rate']
        mean_value = self.poverty_data['mean_tiff'] # 年发电量?
        price = self.poverty_data['PV_price'] # 上网电价
        discount_factor = self.poverty_data['Discount_Factor'] # 折扣因子

        E_n = mean_value * alpha # 年上网电量
        total_generation_revenue_undiscounted = E_n * price * self.N # N年总上网收入 (未折现)
        
        # 应用折扣因子到收入 (假设折扣因子应用于总收入)
        total_generation_revenue_discounted = total_generation_revenue_undiscounted * discount_factor

        for i in self.poverty_data.index:
            self.pv_total_cost[i] = total_cost_undiscounted # 成本是否也需要折现? 通常成本发生在初期或每年，收益发生在未来
            self.pv_revenue[i] = total_generation_revenue_discounted[i] 
            
        logger.info(f"状态码={self.state_code}：光伏成本和收益计算完成。")


    def calculate_hydrogen_costs_for_roi_e(self):
        """计算ROI_E场景的氢能成本"""
        logger.info(f"状态码={self.state_code}：开始计算氢能成本（ROI_E）...")
        self.Cinvest_values = {}
        self.Com_values = {}
        self.Ctrans_values = {}
        
        # 预计算所有行的运输成本
        dht_costs = {dht: self.calculate_transport_cost(dht) for dht in self.poverty_data['Dht'].unique()} # 仍然使用基础运输成本函数

        num_counties = len(self.poverty_data)
        for i in range(num_counties):
            row = self.poverty_data.iloc[i]
            Q = row['Q']
            Cfa = row['Cfa'] # 假设 Cfa 仍然适用
            Dhp = row['Dhp']
            Dht = row['Dht']
            dim = row['dim']
            csa_h_i = self.Csa_h.get(i, 0)
            # dht_cost_i = dht_costs.get(Dht, 0) # ROI_E 使用 a_cost?

            for j_idx, j in enumerate(self.hydrogen_sales_types):
                for k in self.transport_methods:
                    invest_key = (i, j_idx, k)
                    om_key = (i, j_idx, k)
                    trans_key = (i, j_idx, k)

                    if j == 0:  # 自用氢 - 同通用
                        self.Cinvest_values[invest_key] = Cfa + self.Cas * Q + self.Cadi
                        self.Com_values[om_key] = (csa_h_i + self.Csa_d) * self.N * Q
                        self.Ctrans_values[trans_key] = 0
                    elif j == 1:  # 调峰电 - 同通用
                        self.Cinvest_values[invest_key] = Cfa + self.Cas * Q + self.Ca
                        self.Com_values[om_key] = (csa_h_i + self.Csa_a) * self.N * Q
                        self.Ctrans_values[trans_key] = 0
                    elif j == 2:  # 第三项 - 同通用
                        self.Cinvest_values[invest_key] = 0
                        self.Com_values[om_key] = 0
                        self.Ctrans_values[trans_key] = 0
                    elif j == 3:  # 销售氢
                        if k == 1:  # 罐车运输 - ROI_E 特定逻辑
                            # 投资成本为 0? 运维包含 Csa_sf，运输成本使用 a_cost
                            self.Cinvest_values[invest_key] = 0 # ?
                            self.Com_values[om_key] = (csa_h_i + Q * self.Csa_sf) * self.N # Csa_sf 是单位产量运维成本?
                            self.Ctrans_values[trans_key] = self.a_cost * Dht * self.N * Q # a_cost 是 元/kg*m ?
                        elif k == 2:  # 管道运输 - ROI_E 特定逻辑
                            # 投资成本为 0?
                            self.Cinvest_values[invest_key] = 0 # ?
                            self.Com_values[om_key] = (csa_h_i + Dhp * self.Csa_p) * self.N
                            self.Ctrans_values[trans_key] = Dhp * self.Spip * self.N * Q
                        else:  # k=0 无需运输 - ROI_E 特定逻辑
                            self.Cinvest_values[invest_key] = 0
                            self.Com_values[om_key] = (csa_h_i + Q * self.Csa_sf) * self.N # ?
                            self.Ctrans_values[trans_key] = 0
                    else:
                         self.Cinvest_values[invest_key] = 0
                         self.Com_values[om_key] = 0
                         self.Ctrans_values[trans_key] = 0
        logger.info(f"状态码={self.state_code}：氢能成本（ROI_E）计算完成。")


    def calculate_hydrogen_costs_for_roi_c(self):
        """计算ROI_C场景的氢能成本"""
        logger.info(f"状态码={self.state_code}：开始计算氢能成本（ROI_C）...")
        self.Cinvest_values = {}
        self.Com_values = {}
        self.Ctrans_values = {}

        dht_costs = {dht: self.calculate_transport_cost(dht) for dht in self.poverty_data['Dht'].unique()}

        num_counties = len(self.poverty_data)
        for i in range(num_counties):
            row = self.poverty_data.iloc[i]
            Q = row['Q']
            Cfa = row['Cfa']
            Dhp = row['Dhp']
            Dht = row['Dht']
            dim = row['dim']
            csa_h_i = self.Csa_h.get(i, 0)
            dht_cost_i = dht_costs.get(Dht, 0)

            for j_idx, j in enumerate(self.hydrogen_sales_types):
                for k in self.transport_methods:
                    invest_key = (i, j_idx, k)
                    om_key = (i, j_idx, k)
                    trans_key = (i, j_idx, k)

                    if j == 0:  # 自用氢 - 同通用
                        self.Cinvest_values[invest_key] = Cfa + self.Cas * Q + self.Cadi
                        self.Com_values[om_key] = (csa_h_i + self.Csa_d) * self.N * Q
                        self.Ctrans_values[trans_key] = 0
                    elif j == 1:  # 调峰电 - 同通用
                        self.Cinvest_values[invest_key] = Cfa + self.Cas * Q + self.Ca
                        self.Com_values[om_key] = (csa_h_i + self.Csa_a) * self.N * Q
                        self.Ctrans_values[trans_key] = 0
                    elif j == 2:  # 第三项 - 同通用
                        self.Cinvest_values[invest_key] = 0
                        self.Com_values[om_key] = 0
                        self.Ctrans_values[trans_key] = 0
                    elif j == 3:  # 销售氢 - ROI_C 特定逻辑
                        if k == 1:  # 罐车运输
                            # 投资成本增加 e，运维包含 Csa_sf
                            if Dht == dim:
                                self.Cinvest_values[invest_key] = self.e + Cfa + self.Fpi # 同样奇怪的 Fpi
                            else:
                                self.Cinvest_values[invest_key] = self.e + Cfa
                            self.Com_values[om_key] = (csa_h_i + Q * self.Csa_sf) * self.N # ?
                            self.Ctrans_values[trans_key] = dht_cost_i * self.N * Q
                        elif k == 2:  # 管道运输
                            # 投资成本增加 e
                             if Dhp == dim:
                                 self.Cinvest_values[invest_key] = self.e + Cfa + Dhp * self.Cpi + self.Fpi # 使用 Fpi
                             else:
                                 self.Cinvest_values[invest_key] = self.e + Cfa + Dhp * self.Cpi
                             self.Com_values[om_key] = (csa_h_i + Dhp * self.Csa_p) * self.N
                             self.Ctrans_values[trans_key] = Dhp * self.Spip * self.N * Q
                        else:  # k=0 无需运输
                             self.Cinvest_values[invest_key] = self.e + Cfa #?
                             self.Com_values[om_key] = (csa_h_i + Q * self.Csa_sf) * self.N #?
                             self.Ctrans_values[trans_key] = 0
                    else:
                         self.Cinvest_values[invest_key] = 0
                         self.Com_values[om_key] = 0
                         self.Ctrans_values[trans_key] = 0
        logger.info(f"状态码={self.state_code}：氢能成本（ROI_C）计算完成。")

# 可以在这里添加一些用于测试 CostCalculator 的代码
# if __name__ == '__main__':
#     # 创建示例参数和数据
#     sample_params = { ... }
#     sample_data = pd.DataFrame({ ... })
#     state = 1
#     
#     calculator = CostCalculator(sample_params, sample_data, state)
#     all_costs = calculator.calculate_all_costs()
#     print(all_costs) 

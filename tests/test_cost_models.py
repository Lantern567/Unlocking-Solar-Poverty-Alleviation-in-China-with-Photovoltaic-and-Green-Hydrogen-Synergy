import os
import sys
import unittest

import pandas as pd


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from methods.modeling.cost_models import CostCalculator


class TestCostCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = {
            "C_PV": 2800,
            "C_ES": 100,
            "O_PV": 80,
            "O_ES": 10,
            "C_F": 5,
            "C_tax": 2,
            "V_R_factor": 0.15,
            "N": 20,
            "i": 0.03,
            "Cas": 1.5,
            "Cadi": 3000,
            "Ca": 5000,
            "Cpi": 2000,
            "Csa_p": 0.01,
            "Spip": 0.0000002,
            "Fpi": 2000,
            "Fai": 1800,
            "Csa_sf": 0.05,
            "Transport_Distance": [0, 50, 100, 200, 500, 1000, 2000],
            "Transport_Cost": [0, 1.5, 2.5, 4.0, 8.0, 15.0, 25.0],
            "hydrogen_sales_types": [0, 1, 2, 3],
            "Csa_h": [0.01, 0.015, 0.02],
            "Csa_d": 0.02,
            "Csa_a": 0.03,
            "Cf0": [10000, 9000, 8000],
            "Sf0": [100, 1000, 10000],
            "b": [0.6, 0.55, 0.5],
            "e": 0.05,
            "a_cost": 0.1,
        }

        cls.base_data = pd.DataFrame(
            {
                "name": ["CountyA", "CountyB", "CountyC"],
                "Curtailed_Rate": [0.10, 0.15, 0.20],
                "mean_tiff": [1200, 1300, 1100],
                "PV_price": [0.40, 0.42, 0.38],
                "dim": [50000, 150000, 300000],
                "din": [60000, 140000, 310000],
                "production_scale": [1, 2, 3],
                "Discount_Factor": [1.00, 0.95, 0.90],
                "Q": [
                    (1 - 0.10) * 1200 * 10000 / 4.5,
                    (1 - 0.15) * 1300 * 10000 / 4.5,
                    (1 - 0.20) * 1100 * 10000 / 4.5,
                ],
            }
        )

    def make_calculator(self, state_code=1):
        return CostCalculator(self.params, self.base_data.copy(), state_code)

    def prepare_calculator(self, state_code=1):
        calculator = self.make_calculator(state_code=state_code)
        calculator.calculate_hydrogen_facility_cost()
        calculator.calculate_transport_distances()
        return calculator

    def test_initialization_sets_basic_state(self):
        calculator = self.make_calculator()

        self.assertEqual(calculator.N, self.params["N"])
        self.assertTrue(callable(calculator._transport_cost_func))
        self.assertIsNot(calculator.poverty_data, self.base_data)
        self.assertEqual(calculator.Csa_h[0], self.params["Csa_h"][0])
        self.assertEqual(calculator.Csa_h[1], self.params["Csa_h"][1])
        self.assertNotIn("Cfa", calculator.poverty_data.columns)
        self.assertNotIn("Dhp", calculator.poverty_data.columns)
        self.assertNotIn("Dht", calculator.poverty_data.columns)

    def test_calculate_transport_cost(self):
        calculator = self.make_calculator()

        self.assertAlmostEqual(calculator.calculate_transport_cost(100 * 1000), 2.5, places=5)
        self.assertAlmostEqual(calculator.calculate_transport_cost(20 * 1000), 0.6, places=5)
        self.assertAlmostEqual(calculator.calculate_transport_cost(3000 * 1000), 35.0, places=5)

    def test_calculate_hydrogen_facility_cost(self):
        calculator = self.make_calculator()
        calculator.calculate_hydrogen_facility_cost()

        expected_cfa = self.params["Cf0"][0] * (
            self.base_data.loc[0, "Q"] / self.params["Sf0"][0]
        ) ** self.params["b"][0]

        self.assertIn("Cfa", calculator.poverty_data.columns)
        self.assertAlmostEqual(calculator.poverty_data.loc[0, "Cfa"], expected_cfa, places=5)

    def test_calculate_transport_distances(self):
        calculator = self.prepare_calculator()

        self.assertIn("Dhp", calculator.poverty_data.columns)
        self.assertIn("Dht", calculator.poverty_data.columns)
        self.assertTrue((calculator.poverty_data["Dhp"] >= 0).all())
        self.assertTrue((calculator.poverty_data["Dht"] >= 0).all())

    def test_calculate_hydrogen_costs(self):
        calculator = self.prepare_calculator()
        calculator.calculate_hydrogen_costs()

        row = calculator.poverty_data.iloc[0]
        key = (0, 0, 0)
        expected_invest = row["Cfa"] + calculator.Cas * row["Q"] + calculator.Cadi
        expected_om = (calculator.Csa_h[0] + calculator.Csa_d) * calculator.N * row["Q"]

        self.assertIn(key, calculator.Cinvest_values)
        self.assertIn(key, calculator.Com_values)
        self.assertIn(key, calculator.Ctrans_values)
        self.assertAlmostEqual(calculator.Cinvest_values[key], expected_invest, places=5)
        self.assertAlmostEqual(calculator.Com_values[key], expected_om, places=5)
        self.assertEqual(calculator.Ctrans_values[key], 0)

    def test_calculate_pv_costs_for_hydrogen(self):
        calculator = self.make_calculator()
        calculator.calculate_pv_costs_for_hydrogen()

        expected_total_cost = (
            calculator.C_PV
            + calculator.C_ES
            + (calculator.O_PV + calculator.O_ES + calculator.C_F + calculator.C_tax) * calculator.N
        )
        expected_revenue = (
            self.base_data.loc[0, "mean_tiff"]
            * (1 - self.base_data.loc[0, "Curtailed_Rate"])
            * self.base_data.loc[0, "PV_price"]
            * calculator.N
            * self.base_data.loc[0, "Discount_Factor"]
        )

        self.assertAlmostEqual(calculator.pv_total_cost[0], expected_total_cost, places=5)
        self.assertAlmostEqual(calculator.pv_revenue[0], expected_revenue, places=5)

    def test_calculate_hydrogen_costs_for_roi_e(self):
        calculator = self.prepare_calculator(state_code=5)
        calculator.calculate_hydrogen_costs_for_roi_e()

        row = calculator.poverty_data.iloc[0]
        key = (0, 3, 1)
        expected_invest = 0
        expected_om = (calculator.Csa_h[0] + row["Q"] * calculator.Csa_sf) * calculator.N
        expected_trans = calculator.a_cost * row["Dht"] * calculator.N * row["Q"]

        self.assertAlmostEqual(calculator.Cinvest_values[key], expected_invest, places=5)
        self.assertAlmostEqual(calculator.Com_values[key], expected_om, places=5)
        self.assertAlmostEqual(calculator.Ctrans_values[key], expected_trans, places=5)

    def test_calculate_hydrogen_costs_for_roi_c(self):
        calculator = self.prepare_calculator(state_code=6)
        calculator.calculate_hydrogen_costs_for_roi_c()

        row = calculator.poverty_data.iloc[0]
        key = (0, 3, 0)
        expected_invest = calculator.e + row["Cfa"]
        expected_om = (calculator.Csa_h[0] + row["Q"] * calculator.Csa_sf) * calculator.N

        self.assertAlmostEqual(calculator.Cinvest_values[key], expected_invest, places=5)
        self.assertAlmostEqual(calculator.Com_values[key], expected_om, places=5)
        self.assertEqual(calculator.Ctrans_values[key], 0)

    def test_calculate_all_costs_returns_expected_structure(self):
        calculator = self.make_calculator()
        results = calculator.calculate_all_costs()

        self.assertIn("invest", results)
        self.assertIn("om", results)
        self.assertIn("trans", results)
        self.assertIn("pv_cost", results)
        self.assertIn("pv_revenue", results)
        self.assertIn("poverty_data_updated", results)
        self.assertTrue(results["invest"])
        self.assertTrue(results["pv_cost"])


if __name__ == "__main__":
    unittest.main()

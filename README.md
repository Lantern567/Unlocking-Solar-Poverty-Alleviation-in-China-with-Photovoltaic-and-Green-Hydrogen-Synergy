# Unlocking Solar Poverty Alleviation in China with Photovoltaic and Green Hydrogen Synergy

This repository is a curated public version of the working research directory for the project on solar poverty alleviation in China through photovoltaic deployment and green hydrogen synergy.

The repository focuses on code, notebooks, methodological notes, and selected final outputs. Large raw datasets, bulky intermediate files, and local development artifacts are intentionally excluded so the project is easier to browse and share on GitHub.

## What is included

- Core analysis notebook in `methods/notebooks/`
- Main analysis script and supporting modeling modules in `methods/`
- Method notes describing hydrogen, storage, and economic indicator calculations
- Final tables and selected figures in `results/`
- A lightweight unit test in `tests/`

## What is intentionally excluded

- Large raster and GIS source files such as `PVOUT.tif` and other raw geospatial layers
- Heavy intermediate CSV outputs such as `temp_results_PV_*.csv`
- Full optimization dumps such as `optimization_results_all_scenarios*.csv`
- Local IDE folders, caches, checkpoints, and virtual environments

See `data/README.md` for a short note on omitted data categories.

## Directory layout

```text
data/
methods/
  analysis_scripts/
  data_processing_scripts/
  documentation/
  modeling/
  notebooks/
results/
  figures/
    charts/
    maps/
  tables/
  supplementary_results/
tests/
```

## Key files

- Notebook: `methods/notebooks/H2-PV_structure.ipynb`
- Main script: `methods/analysis_scripts/auto_adjusted_3d_plot.py`
- Modeling modules:
  - `methods/modeling/cost_models.py`
  - `methods/modeling/economic_parameters.py`
  - `methods/data_processing_scripts/hydrogen_data_preparer.py`
- Representative result tables:
  - `results/tables/economic_assessment_results.csv`
  - `results/tables/final_pv_battery_scenarios.csv`
  - `results/tables/poverty_selected_with_pv_roi.xlsx`

## Quick start

1. Create a Python environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Open the main notebook or run the selected analysis scripts.

Note: some workflows still expect local raw datasets that are not included in this public repository.

## Testing

Run the included unit test with:

```bash
python -m unittest tests.test_cost_models
```

## Notes

This repository is intended as a lightweight research archive for code sharing and result dissemination, not as a full mirror of the original local working directory.

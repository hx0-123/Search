# SKTAQ Demo System

SKTAQ (Secure Keyword-aware Top-k Query) is a privacy-preserving spatial keyword query system supporting cloud-fog collaboration.

## Demo Video

A demonstration video of the SKTAQ privacy-preserving LBS system is available in the GitHub Release:

[SKTAQ Privacy-Preserving LBS Demo Video](https://github.com/hx0-123/Search/releases/tag/demo-v1.0)

The demo video presents the main workflow of the system, including:

- Data owner upload and encrypted preprocessing
- Secure index construction
- User continuous spatial keyword Top-k query
- Fog-side encrypted scoring
- Cloud-side secure ranking
- Safe-zone monitoring and result update
- Frontend visualization

The video is provided for project demonstration and evaluation purposes.  
The source code, dataset verification files, and setup-related materials are available in this repository.

## Real Dataset Verification

The SKTAQ demo system supports real spatial-textual dataset verification for datasets used in related studies, including:

- **POI** - Point of Interest dataset
- **SINA** - SINA Weibo location dataset
- **roadNet-CA** - California Road Network dataset
- **PLI** - Point Location Information dataset
- **HKU** - Hong Kong University dataset
- **RNCA** - Road Network California dataset

Full datasets are not included in this repository due to size and license restrictions.

The project provides auxiliary verification materials instead of complete datasets, including:

- Dataset format examples (`data/sample/*.csv`)
- Configuration templates (`configs/real_datasets/*.yaml`)
- Dataset path checking script (`scripts/check_real_dataset_paths.py`)
- Verification summary file (`logs/real_dataset_test_summary.json`)
- Documentation for reproducibility (`docs/real_dataset_verification.md`)

These auxiliary files are provided only for reproducibility documentation and do not change the original SKTAQ runtime logic.

### Recommended Commands

To check dataset paths and view verification summary:

```bash
python scripts/check_real_dataset_paths.py
python scripts/show_real_dataset_verification.py
```

### Sample Data Format

The sample CSV files under `data/sample/` are small illustrative examples and are not used as performance benchmarks.

Unified data format:

```csv
id,x,y,keywords
1,116.397,39.908,"restaurant,noodles,coffee"
2,121.473,31.230,"museum,history,tourism"
```

### Recommended Dataset Directory Structure

```
data/
  POI/
    poi.csv
  SINA/
    sina.csv
  roadNet-CA/
    roadnet_ca.txt
  PLI/
    pli.csv
  HKU/
    hku.csv
  RNCA/
    rnca.csv
```

For more details, please refer to [docs/real_dataset_verification.md](docs/real_dataset_verification.md).

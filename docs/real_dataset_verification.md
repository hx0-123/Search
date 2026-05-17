# Real Dataset Verification Notes for SKTAQ

This document records how the SKTAQ demo system is designed and verified with real spatial-textual datasets used in related studies. The purpose of these auxiliary materials is to provide reproducibility documentation and demonstration evidence for reviewers, without changing the existing demo runtime workflow.

## Supported Real Dataset Families

The SKTAQ workflow is prepared for the following real spatial-textual datasets and benchmark-style inputs referenced by related SKTAQ/SKCQ studies, including SKQ_TCC.pdf, paper_758.pdf, and YBF thesis materials:

- POI
- SINA
- roadNet-CA
- PLI
- HKU
- RNCA

## Verified Workflow Scope

These datasets are used to validate, or to preserve a documented validation entry for, the following SKTAQ workflow stages:

1. dataset import
2. local preprocessing
3. Paillier-based encryption
4. secure index construction
5. encrypted continuous spatial keyword query
6. fog-side scoring
7. cloud-side Top-k ranking
8. safe-zone-based continuous update

## Repository Scope and Dataset Availability

The full datasets are not included in this repository due to size and license restrictions.

The provided files are dataset adapters, configuration templates, sample data, and verification records. These files are intended for reproducibility documentation and demonstration evidence. They do not represent complete benchmark datasets and should not be interpreted as performance benchmark results.

The auxiliary files added for real dataset verification do not change the original SKTAQ demo system runtime logic. They do not modify the frontend, backend, database schema, encryption implementation, secure index construction, cloud-fog collaboration workflow, or query processing pipeline.

## Recommended Local Dataset Directory Structure

When a reviewer or developer prepares the full datasets locally, the recommended directory layout is:

```text
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

The helper scripts only check whether these paths exist. They do not import data into the database, encrypt data, build indexes, or execute queries.

## Unified CSV Format

For compatibility with the SKTAQ data import and preprocessing pipeline, datasets should be converted or adapted to the following unified CSV schema:

```csv
id,x,y,keywords
```

Field meanings:

- `id`: unique object identifier.
- `x`: longitude or projected X coordinate, depending on the dataset preprocessing strategy.
- `y`: latitude or projected Y coordinate, depending on the dataset preprocessing strategy.
- `keywords`: comma-separated textual keywords associated with the spatial object.

Example:

```csv
id,x,y,keywords
1,116.397,39.908,"restaurant,noodles,coffee"
2,121.473,31.230,"museum,history,tourism"
```

If an original dataset does not contain textual keywords, users may supplement or generate keywords according to the experimental preprocessing strategy described in the related study. For example, road-network vertices can be associated with semantic labels generated from nearby POIs, category dictionaries, or controlled synthetic keyword assignments used only for experimental evaluation.

## Provided Auxiliary Materials

This repository provides the following non-invasive verification materials:

- `data/README.md`: instructions for placing full datasets and understanding the sample format.
- `data/sample/*.csv`: small illustrative examples for each dataset family.
- `configs/real_datasets/*.yaml`: dataset configuration templates for documented experiments.
- `logs/real_dataset_test_summary.json`: a documented test summary template.
- `scripts/check_real_dataset_paths.py`: a path-checking script that only reports whether expected files exist.
- `scripts/show_real_dataset_verification.py`: a display script that prints the documented verification summary.

These files are documentation/evidence/helper materials only. They are intentionally separated from the main SKTAQ runtime code.

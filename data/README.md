# Dataset Directory Notes

The full real spatial-textual datasets are not included in this repository due to size and license restrictions.

To reproduce real-dataset experiments, please download or prepare the datasets independently and place them under the corresponding directories in `data/`.

Recommended layout:

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

## Unified Data Format

The recommended unified CSV schema is:

```csv
id,x,y,keywords
```

Example:

```csv
id,x,y,keywords
1,116.397,39.908,"restaurant,noodles,coffee"
2,121.473,31.230,"museum,history,tourism"
```

Field meanings:

- `id`: unique object identifier.
- `x`: longitude or projected X coordinate.
- `y`: latitude or projected Y coordinate.
- `keywords`: comma-separated English keywords.

The files under `data/sample/` are small illustrative examples used only to demonstrate the required format. They do not represent complete real datasets and must not be used as performance benchmarks.

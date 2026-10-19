# Global human oral microbiome metadata

This repository contains the data harmonization and visualization code used in:

> Chen X, Jamieson L, Weyrich LS, Nath S. **Global Landscape of Publicly Available Human Oral Microbiome Data.** *Journal of Dental Research*. Published online July 9, 2026.
>
> Paper: [https://doi.org/10.1177/00220345261456612](https://doi.org/10.1177/00220345261456612)

The complete archived project, including the harmonized dataset, raw and intermediate data, analysis inputs, results, and a snapshot of the code, is available on Zenodo:

> Zenodo: [https://doi.org/10.5281/zenodo.19663092](https://doi.org/10.5281/zenodo.19663092)

## Overview

The code is organized into two components:

1. **Harmonization**
   - Construction of a standardized global oral microbiome metadata dataset from NCBI BioSample records
   - See [`harmonization/README.md`](harmonization/README.md)

2. **Visualization and analysis**
   - Generation of the tables and figures reported in the manuscript
   - See [`visualization/README.md`](visualization/README.md)

## Repository structure

```text
.
├── harmonization/   # Metadata retrieval, harmonization, filtering, and linking
├── visualization/   # Table, analysis, and figure-generation scripts
├── LICENSE
└── README.md
```

This GitHub repository intentionally contains code only. Large raw files, intermediate datasets, the final harmonized dataset, and generated results are distributed through the Zenodo archive.

## Main output

The primary dataset produced by the workflow is `final_biosample.csv`. It is included in the Zenodo archive and is not duplicated in this GitHub repository.

## Reproducibility

Detailed workflow instructions, expected inputs, and outputs are documented separately:

- Data harmonization: [`harmonization/README.md`](harmonization/README.md)
- Tables and figures: [`visualization/README.md`](visualization/README.md)

## License

The code in this repository is available under the [MIT License](LICENSE).

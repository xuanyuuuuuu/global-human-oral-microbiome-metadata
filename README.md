# Global inequities of the human oral microbiome

This repository contains code and derived data files used to analyse global representation patterns of human oral microbiome samples.

The materials are organised to reflect the analytical workflow and figure groupings described in the manuscript. 
Large intermediate files and raw sequencing data are not included.

---

## Contents

### Code

- `python/`  
  Python scripts used for metadata inspection, harmonisation, filtering, and quantitative analyses. 
  All method-level calculations reported in the manuscript are performed in Python.

- `R/`  
  R scripts used exclusively for figure generation and visualisation.
  No analytical or statistical calculations are implemented in R.

---

### Data

- `data/`  
  Derived, analysis-ready metadata tables used as inputs for figures and summary tables in the manuscript.

  These files include sample-level metadata (BioSample-based), country- and region-level mapping tables, and harmonisation reference tables.

  Raw sequencing reads, run-level metadata (e.g. SRR accessions), and large intermediate processing files are not included.

---

## Figure organisation

R scripts are grouped according to the major figure sections in the manuscript:

- **Global human oral microbiome representation**
- **Global temporal patterns of human oral microbiome samples**
- **Sampling-site composition, temporal trends, and regional patterns of human oral microbiome samples**

---

## Notes

- The unit of analysis throughout this study is the BioSample.

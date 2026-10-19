
## Harmonization 

### Overview

XML → attributes → values → filtering → runinfo → linking → final dataset

---

### Raw data

The analysis started from four raw XML files downloaded from the NCBI BioSample database.

Four taxonomy categories were used:
- human oral metagenome (txid447426)
- human saliva metagenome (txid1679718)
- oral metagenome (txid646099)
- human metagenome (txid1227552)

Query:
txidXXXXXXX[organism:exp] AND public[filter] AND biosample sra[filter] AND ("2011/01/01"[PDAT] : "2025/12/31"[PDAT])

Download format: Full XML (text)

Files:
- human_biosample.xml
- oral_biosample.xml
- human_oral_biosample.xml
- human_saliva_biosample.xml

---

### Step 1: Attribute extraction

Extract and count all attribute names from XML.

Script:
- attributes_count.py

Input:
- *_biosample.xml

Output:
- attribute_counts.csv

Select relevant attribute names for country, host and sampling type. (Corresponding to Appendix Tables 1 in manuscript)

---

### Step 2: Attribute harmonization

Extract standardized fields from XML.

Script:
- attributes_unify.py

Input:
- *_biosample.xml

Output:
- human_biosample.csv
- oral_biosample.csv
- human_oral_biosample.csv
- human_saliva_biosample.csv

Output columns:
- accession
- country
- host
- sampling_type

---

### Step 3: Value extraction

Check raw value distributions.

Script:
- value_count.py

Input:
- *_biosample.csv

Output:
- country_value_count.csv
- sampling_type_value_count.csv
- host_value_count.csv

These summaries were used to construct mapping dictionaries for value harmonization (Appendix Tables 2 to 4 in the manuscript).

Mapping files:
- country_map.csv
- host_map.csv
- sampling-type_map.csv

---

### Step 4: Value harmonization

Standardize values using mapping dictionaries.

Script:
- value_unify.py

Input:
- *_biosample.csv
- country_map.csv
- host_map.csv
- sampling_type_map.csv

Output:
- clean_human_biosample.csv
- clean_oral_biosample.csv
- clean_human_oral_biosample.csv
- clean_human_saliva_biosample.csv

---

### Step 5: Filtering and merging

Filter BioSamples based on site and host and merge.

Script:
- filter.py

Input:
- clean_*.csv

Output:
- merged_filtered_biosample.csv

---

### Step 6: Run metadata retrieval

Retrieve sequencing metadata using ENA API.

Script:
- runinfo.py

Input:
- merged_filtered_biosample.csv

Output:
- runmeta_all_runs.csv

---

### Step 7: Linking

Link BioSample metadata with run-level metadata.

Script:
- link.py

Input:
- merged_filtered_biosample.csv
- runmeta_all_runs.csv.gz

Output:
- final_biosample.csv


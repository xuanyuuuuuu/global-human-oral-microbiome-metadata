## Visualization

### 1. Country counts (corresponding to Table 1 in the manuscript)

Script:
- country_counts.py

Input:
- final_biosample.csv

Output:
- table1_country_counts.csv 

---


### 2. Representation by region and income group (corresponding to Table 2 in the manuscript)

Script:
- region_group_representation.py  

Input:
- final_biosample.csv  
- country_population_group.csv  
- region_population.csv  

Output:
- sdg_representation.csv  
- income_representation.csv 

---
### 3. Sampling-type counts (corresponding to Table 3 in the manuscript)

Script:
- sampling_type_counts.py  

Input:
- final_biosample.csv  

Output:
- sampling_type_counts.csv

---
### 4. Country-level representation (corresponding to Table S6 in the manuscript)

Script:
- country_representation.py  

Input:
- final_biosample.csv  
- country_population_group.csv  
- region_population.csv  

Output:
- country_representation.csv 

---
### 5. Country-level sample map (corresponding to Figure 1A in the manuscript)

Script:
- map_samples.R  

Input:
- table1_country_counts.csv  

Output:
- figure1A_map_samples.svg

---
### 6. Country-level representation map (corresponding to Figure 1B in the manuscript)

Script:
- map_representation.R  

Input:
- country_representation.csv  

Output:
- figure1B_map_representation.svg

---
### 7. SDG region temporal patterns (corresponding to Figure 1C-D and Figure S2A-B in the manuscript)

Script:
- sdg_cumulative_samples.R  
- sdg_cumulative_proportion.R  
- sdg_new_samples.R  
- sdg_yearly_proportion.R  

Input:
- final_biosample.csv  
- country_population_group.csv  
- oral_theme.R  

Output:
- sdg_cumulative_samples.svg (Figure 1C)  
- sdg_cumulative_proportion.svg (Figure 1D)  
- sdg_new_samples.svg (Figure S2A)  
- sdg_yearly_proportion.svg (Figure S2B)

---
### 8. Sampling-type patterns (corresponding to Figure 1E-H in the manuscript)

Script:
- sampling_type_pie.R  
- sampling_type_cumulative.R  
- sampling_type_by_region_counts.R  
- sampling_type_by_region_proportion.R  

Input:
- final_biosample.csv  
- country_population_group.csv  
- oral_theme.R  

Output:
- sampling_type_pie.svg (Figure 1E)  
- sampling_type_cumulative.svg (Figure 1F)  
- sampling_type_by_region_counts.svg (Figure 1G)  
- sampling_type_by_region_proportion.svg (Figure 1H)

---

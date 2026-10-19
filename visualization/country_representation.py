import pandas as pd
import numpy as np
import argparse
from pathlib import Path


def compute_representation_index(rp: pd.Series) -> pd.Series:
    ri = pd.Series(np.nan, index=rp.index, dtype="float64")

    ge1 = rp >= 1
    lt1 = (rp < 1) & rp.notna()

    ri.loc[ge1] = rp.loc[ge1]
    ri.loc[lt1] = -1 / rp.loc[lt1]

    return ri


def main():
    # -------------------------------
    # Arguments
    # -------------------------------
    parser = argparse.ArgumentParser(description="Country-level RI calculation")
    parser.add_argument("--biosample", required=True)
    parser.add_argument("--population", required=True)
    parser.add_argument("--region_population", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # -------------------------------
    # Load data
    # -------------------------------
    biosample = pd.read_csv(args.biosample, low_memory=False)
    population = pd.read_csv(args.population, low_memory=False)
    region_population = pd.read_csv(args.region_population, low_memory=False)

    # -------------------------------
    # Basic checks
    # -------------------------------
    if "iso3" not in biosample.columns:
        raise ValueError("final_biosample.csv must contain 'iso3'")

    required_pop_cols = ["iso3", "country_clean", "Population_2023_thousands"]
    for col in required_pop_cols:
        if col not in population.columns:
            raise ValueError(f"country_population_group.csv missing: {col}")

    if "Region" not in region_population.columns:
        raise ValueError("region_population.csv must contain 'Region'")
    if "Population_2023_thousands" not in region_population.columns:
        raise ValueError("region_population.csv missing Population_2023_thousands")

    # -------------------------------
    # Clean
    # -------------------------------
    biosample["iso3"] = biosample["iso3"].astype(str).str.strip().str.upper()
    population["iso3"] = population["iso3"].astype(str).str.strip().str.upper()

    biosample["iso3"] = biosample["iso3"].replace({
        "": "UNK",
        "NAN": "UNK",
        "NONE": "UNK",
        "<NA>": "UNK"
    })

    population["country_clean"] = population["country_clean"].astype(str).str.strip()
    population["Population_2023_thousands"] = pd.to_numeric(
        population["Population_2023_thousands"], errors="coerce"
    )

    region_population["Region"] = region_population["Region"].astype(str).str.strip()
    region_population["Population_2023_thousands"] = pd.to_numeric(
        region_population["Population_2023_thousands"], errors="coerce"
    )

    # -------------------------------
    # Get WORLD population
    # -------------------------------
    world_rows = region_population.loc[
        region_population["Region"] == "WORLD",
        "Population_2023_thousands"
    ]

    if world_rows.empty:
        raise ValueError("No row found where Region == 'WORLD'")
    if len(world_rows) > 1:
        raise ValueError("Multiple WORLD rows found")

    world_pop = world_rows.iloc[0]

    print(f"[INFO] World population (thousands): {world_pop}")

    # -------------------------------
    # Sample counts
    # -------------------------------
    sample_counts = (
        biosample.groupby("iso3")
        .size()
        .reset_index(name="Samples")
    )

    # -------------------------------
    # Merge population
    # -------------------------------
    pop = population[["iso3", "country_clean", "Population_2023_thousands"]].drop_duplicates("iso3")
    result = sample_counts.merge(pop, on="iso3", how="left")

    # -------------------------------
    # Country names
    # -------------------------------
    result["Country"] = result["country_clean"]
    result.loc[result["iso3"] == "UNK", "Country"] = "Unknown"
    result.loc[result["iso3"] == "ATA", "Country"] = "Antarctica"

    unmatched = result["Country"].isna() & ~result["iso3"].isin(["UNK", "ATA"])
    result.loc[unmatched, "Country"] = result.loc[unmatched, "iso3"]

    # -------------------------------
    # Sample proportions
    # -------------------------------
    n_all = result["Samples"].sum()
    result["Sample Proportion"] = result["Samples"] / n_all

    is_excluded = result["iso3"].isin(["UNK", "ATA"])
    n_known = result.loc[~is_excluded, "Samples"].sum()

    result["Sample Proportion (known location)"] = np.nan
    result.loc[~is_excluded, "Sample Proportion (known location)"] = (
        result.loc[~is_excluded, "Samples"] / n_known
    )

    # -------------------------------
    # Population proportion (GLOBAL)
    # -------------------------------
    result["Population Proportion"] = np.nan
    result.loc[~is_excluded, "Population Proportion"] = (
        result.loc[~is_excluded, "Population_2023_thousands"] / world_pop
    )

    # -------------------------------
    # RP
    # -------------------------------
    result["Representation Proportion"] = np.nan

    valid = (
        ~is_excluded
        & result["Sample Proportion (known location)"].notna()
        & result["Population Proportion"].notna()
        & (result["Population Proportion"] > 0)
    )

    result.loc[valid, "Representation Proportion"] = (
        result.loc[valid, "Sample Proportion (known location)"]
        / result.loc[valid, "Population Proportion"]
    )

    # -------------------------------
    # RI
    # -------------------------------
    result["Representation Index"] = compute_representation_index(
        result["Representation Proportion"]
    )

    # -------------------------------
    # Clean UNK / ATA
    # -------------------------------
    cols_to_blank = [
        "Population_2023_thousands",
        "Sample Proportion (known location)",
        "Population Proportion",
        "Representation Proportion",
        "Representation Index",
    ]
    result.loc[is_excluded, cols_to_blank] = np.nan

    # -------------------------------
    # Final table
    # -------------------------------
    final = result[
        [
            "Country",
            "iso3",
            "Samples",
            "Population_2023_thousands",
            "Sample Proportion",
            "Sample Proportion (known location)",
            "Population Proportion",
            "Representation Proportion",
            "Representation Index",
        ]
    ].copy()

    final = final.rename(
        columns={
            "Population_2023_thousands": "2023 Population (estimated, in thousands)"
        }
    )

    # -------------------------------
    # Sort
    # -------------------------------
    regular = final.loc[~result["iso3"].isin(["UNK", "ATA"])].sort_values(by="Samples", ascending=False)
    special = final.loc[result["iso3"].isin(["UNK", "ATA"])]

    final = pd.concat([regular, special], ignore_index=True)

    # -------------------------------
    # Save
    # -------------------------------
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(args.output, index=False, encoding="utf-8-sig")

    print("[DONE]")
    print(f"Total samples: {n_all}")
    print(f"Known samples: {n_known}")


if __name__ == "__main__":
    main()
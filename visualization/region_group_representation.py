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


def build_group_table(
    df_samples: pd.DataFrame,
    region_population: pd.DataFrame,
    group_col: str,
    output_group_name: str,
    world_pop: float
) -> pd.DataFrame:
    """
    Build representation table for one grouping level:
    - SDG_Region
    - Income_Group
    """

    # sample denominators
    n_all = int(df_samples["sample_count"].sum())
    n_known = int(df_samples.loc[~df_samples["iso3"].isin(["UNK", "ATA"]), "sample_count"].sum())

    if n_all == 0:
        raise ValueError("n_all = 0")
    if n_known == 0:
        raise ValueError("n_known = 0")

    # regular known-country rows only
    known = df_samples.loc[~df_samples["iso3"].isin(["UNK", "ATA"])].copy()

    # -----------------------------
    # Group sample counts
    # -----------------------------
    grouped = (
        known.groupby(group_col, dropna=False)["sample_count"]
        .sum()
        .reset_index()
        .rename(columns={group_col: output_group_name, "sample_count": "Samples"})
    )

    grouped["Sample Proportion"] = grouped["Samples"] / n_all
    grouped["Sample Proportion (known location)"] = grouped["Samples"] / n_known

    # -----------------------------
    # Merge population
    # -----------------------------
    pop_sub = region_population[["Region", "Population_2023_thousands"]].copy()
    pop_sub = pop_sub.drop_duplicates(subset="Region", keep="first")

    grouped = grouped.merge(
        pop_sub,
        left_on=output_group_name,
        right_on="Region",
        how="left"
    ).drop(columns="Region")

    grouped = grouped.rename(
        columns={"Population_2023_thousands": "2023 Population (estimated, in thousands)"}
    )

    # -----------------------------
    # Population proportion
    # -----------------------------
    grouped["Population Proportion"] = (
        grouped["2023 Population (estimated, in thousands)"] / world_pop
    )

    # -----------------------------
    # RP / RI
    # -----------------------------
    grouped["Representation Proportion"] = (
        grouped["Sample Proportion (known location)"] / grouped["Population Proportion"]
    )

    grouped["Representation Index"] = compute_representation_index(
        grouped["Representation Proportion"]
    )

    # -----------------------------
    # Unknown / Antarctica rows
    # -----------------------------
    special = df_samples.loc[df_samples["iso3"].isin(["UNK", "ATA"])].copy()

    if not special.empty:
        special[output_group_name] = special["iso3"].map({
            "UNK": "Unknown",
            "ATA": "Antarctica"
        })

        special = special[[output_group_name, "sample_count"]].rename(
            columns={"sample_count": "Samples"}
        )

        special["Sample Proportion"] = special["Samples"] / n_all
        special["Sample Proportion (known location)"] = np.nan
        special["2023 Population (estimated, in thousands)"] = np.nan
        special["Population Proportion"] = np.nan
        special["Representation Proportion"] = np.nan
        special["Representation Index"] = np.nan

        grouped = pd.concat([grouped, special], ignore_index=True)

    # -----------------------------
    # Sort
    # -----------------------------
    regular = grouped.loc[~grouped[output_group_name].isin(["Unknown", "Antarctica"])].copy()
    regular = regular.sort_values(by="Samples", ascending=False)

    special = grouped.loc[grouped[output_group_name].isin(["Unknown", "Antarctica"])].copy()
    if not special.empty:
        special["__order"] = special[output_group_name].map({"Unknown": 1, "Antarctica": 2})
        special = special.sort_values("__order").drop(columns="__order")

    grouped = pd.concat([regular, special], ignore_index=True)

    return grouped


def main():
    parser = argparse.ArgumentParser(description="Calculate SDG-region and income-group representation tables.")
    parser.add_argument("--biosample", required=True, help="Path to final_biosample.csv")
    parser.add_argument("--population", required=True, help="Path to country_population_group.csv")
    parser.add_argument("--region_population", required=True, help="Path to region_population.csv")
    parser.add_argument("--output_dir", required=True, help="Directory for output CSV files")
    args = parser.parse_args()

    biosample = pd.read_csv(args.biosample, low_memory=False)
    population = pd.read_csv(args.population, low_memory=False)
    region_population = pd.read_csv(args.region_population, low_memory=False)

    # -----------------------------
    # Checks
    # -----------------------------
    if "iso3" not in biosample.columns:
        raise ValueError("final_biosample.csv must contain 'iso3'")

    required_population_cols = [
        "iso3", "country_clean", "SDG_Region", "Income_Group", "Population_2023_thousands"
    ]
    for col in required_population_cols:
        if col not in population.columns:
            raise ValueError(f"country_population_group.csv missing: {col}")

    if "Region" not in region_population.columns:
        raise ValueError("region_population.csv must contain 'Region'")
    if "Population_2023_thousands" not in region_population.columns:
        raise ValueError("region_population.csv missing Population_2023_thousands")

    # -----------------------------
    # Clean
    # -----------------------------
    biosample["iso3"] = biosample["iso3"].astype(str).str.strip().str.upper()
    population["iso3"] = population["iso3"].astype(str).str.strip().str.upper()

    biosample["iso3"] = biosample["iso3"].replace({
        "": "UNK",
        "NAN": "UNK",
        "NONE": "UNK",
        "<NA>": "UNK"
    })

    population["country_clean"] = population["country_clean"].astype(str).str.strip()
    population["SDG_Region"] = population["SDG_Region"].astype(str).str.strip()
    population["Income_Group"] = population["Income_Group"].astype(str).str.strip()
    population["Population_2023_thousands"] = pd.to_numeric(
        population["Population_2023_thousands"], errors="coerce"
    )

    region_population["Region"] = region_population["Region"].astype(str).str.strip()
    region_population["Population_2023_thousands"] = pd.to_numeric(
        region_population["Population_2023_thousands"], errors="coerce"
    )

    # -----------------------------
    # WORLD population
    # -----------------------------
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

    # -----------------------------
    # Count samples by iso3
    # -----------------------------
    sample_counts = (
        biosample.groupby("iso3")
        .size()
        .reset_index(name="sample_count")
    )

    # -----------------------------
    # Merge country/group mapping
    # -----------------------------
    pop_map = population[
        ["iso3", "country_clean", "SDG_Region", "Income_Group", "Population_2023_thousands"]
    ].drop_duplicates(subset="iso3", keep="first")

    df_samples = sample_counts.merge(pop_map, on="iso3", how="left")

    # -----------------------------
    # Build SDG table
    # -----------------------------
    sdg_table = build_group_table(
        df_samples=df_samples,
        region_population=region_population,
        group_col="SDG_Region",
        output_group_name="SDG Region",
        world_pop=world_pop
    )

    # -----------------------------
    # Build income table
    # -----------------------------
    income_table = build_group_table(
        df_samples=df_samples,
        region_population=region_population,
        group_col="Income_Group",
        output_group_name="Income Group",
        world_pop=world_pop
    )

    # -----------------------------
    # Save
    # -----------------------------
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sdg_out = output_dir / "sdg_representation.csv"
    income_out = output_dir / "income_representation.csv"

    sdg_table.to_csv(sdg_out, index=False, encoding="utf-8-sig")
    income_table.to_csv(income_out, index=False, encoding="utf-8-sig")

    print("[DONE]")
    print(f"SDG output: {sdg_out}")
    print(f"Income output: {income_out}")


if __name__ == "__main__":
    main()
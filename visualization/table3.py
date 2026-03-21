import argparse
import os
import sys
import pandas as pd
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"File not found: {args.input}")

    os.makedirs(args.outdir, exist_ok=True)

    out_country = os.path.join(args.outdir, "country_sample_distribution.csv")
    out_region = os.path.join(args.outdir, "sdg_region_sample_distribution.csv")
    out_income = os.path.join(args.outdir, "income_group_sample_distribution.csv")

    df = pd.read_csv(args.input, dtype="string")

    required = {
        "country_clean",
        "iso3",
        "sample_count",
        "sample_share",
        "SDG_Region",
        "Income_Group",
    }
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"Missing columns: {missing}")

    df["country_clean"] = df["country_clean"].str.strip()
    df["iso3"] = df["iso3"].str.strip().str.upper()
    df["SDG_Region"] = df["SDG_Region"].str.strip()
    df["Income_Group"] = df["Income_Group"].str.strip()
    df["sample_count"] = pd.to_numeric(df["sample_count"], errors="coerce").fillna(0).astype(int)
    df["sample_share"] = pd.to_numeric(df["sample_share"], errors="coerce")

    is_known = (
        df["country_clean"].notna()
        & ~df["country_clean"].isin(["Antarctica", "Unknown"])
    )

    N_all = int(df["sample_count"].sum())
    N_known = int(df.loc[is_known, "sample_count"].sum())

    if N_all == 0 or N_known == 0:
        sys.exit("Invalid denominators")

    country_out = pd.DataFrame({
        "Country": df["country_clean"],
        "iso3": df["iso3"],
        "Samples": df["sample_count"],
        "sample_proportion_all": df["sample_count"] / N_all,
        "sample_proportion_known": np.where(
            is_known,
            df["sample_count"] / N_known,
            np.nan
        )
    }).sort_values("Samples", ascending=False)

    country_out.to_csv(out_country, index=False, encoding="utf-8-sig")

    region_counts = (
        df.loc[is_known]
          .groupby("SDG_Region", dropna=False)["sample_count"]
          .sum()
          .reset_index()
          .rename(columns={"SDG_Region": "Region", "sample_count": "Samples"})
    )

    region_out = pd.DataFrame({
        "Region": region_counts["Region"],
        "Samples": region_counts["Samples"].astype(int),
        "sample_proportion_all": region_counts["Samples"] / N_all,
        "sample_proportion_known": region_counts["Samples"] / N_known,
    }).sort_values("Samples", ascending=False)

    region_out.to_csv(out_region, index=False, encoding="utf-8-sig")

    income_counts = (
        df.loc[is_known]
          .groupby("Income_Group", dropna=False)["sample_count"]
          .sum()
          .reset_index()
          .rename(columns={"Income_Group": "Income Group", "sample_count": "Samples"})
    )

    income_out = pd.DataFrame({
        "Income Group": income_counts["Income Group"],
        "Samples": income_counts["Samples"].astype(int),
        "sample_proportion_all": income_counts["Samples"] / N_all,
        "sample_proportion_known": income_counts["Samples"] / N_known,
    }).sort_values("Samples", ascending=False)

    income_out.to_csv(out_income, index=False, encoding="utf-8-sig")

    print(f"[OK] N_all={N_all:,} N_known={N_known:,}")
    print(out_country)
    print(out_region)
    print(out_income)


if __name__ == "__main__":
    main()

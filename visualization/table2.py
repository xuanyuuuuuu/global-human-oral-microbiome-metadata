import argparse
import os
import sys
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Generate Table 2: samples and countries per oral sampling site."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input CSV (must contain sampling_site_main_category, sampling_site_subcategory, country_clean)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV path, e.g., outputs/table2_samples_per_sampling_site.csv",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"File not found: {args.input}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    df = pd.read_csv(args.input)

    required_cols = [
        "sampling_site_main_category",
        "sampling_site_subcategory",
        "country_clean",
    ]
    for col in required_cols:
        if col not in df.columns:
            sys.exit(f"Missing required column: {col}")

    df = df[required_cols].copy()

    df = df.dropna(subset=["sampling_site_subcategory"])

    samples_df = (
        df.groupby(
            ["sampling_site_main_category", "sampling_site_subcategory"],
            dropna=False,
        )
        .size()
        .reset_index(name="Samples")
    )

    df_country = df[~df["country_clean"].isin(["Antarctica", "Unknown"])]

    countries_df = (
        df_country.groupby(
            ["sampling_site_main_category", "sampling_site_subcategory"],
            dropna=False,
        )["country_clean"]
        .nunique()
        .reset_index(name="Countries")
    )

    table2 = samples_df.merge(
        countries_df,
        on=["sampling_site_main_category", "sampling_site_subcategory"],
        how="left",
    )

    table2["Countries"] = table2["Countries"].fillna(0).astype(int)

    main_order = (
        table2.groupby("sampling_site_main_category")["Samples"]
        .sum()
        .sort_values(ascending=False)
        .index
    )

    table2["sampling_site_main_category"] = pd.Categorical(
        table2["sampling_site_main_category"],
        categories=main_order,
        ordered=True,
    )

    table2 = table2.sort_values(
        ["sampling_site_main_category", "Samples"],
        ascending=[True, False],
    )

    table2 = table2.rename(
        columns={
            "sampling_site_main_category": "Group",
            "sampling_site_subcategory": "Sampling site",
        }
    )

    table2.to_csv(args.out, index=False, encoding="utf-8")

    print("[OK] Table 2 generated")
    print(f"Rows: {len(table2)}")
    print(f"Saved to: {args.out}")


if __name__ == "__main__":
    main()

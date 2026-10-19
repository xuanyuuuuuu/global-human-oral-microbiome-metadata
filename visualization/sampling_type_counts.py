import argparse
import os
import sys
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"File not found: {args.input}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    df = pd.read_csv(args.input)

    required_cols = [
        "sampling_type_main_category",
        "sampling_type_subcategory",
        "country_clean",
    ]
    for col in required_cols:
        if col not in df.columns:
            sys.exit(f"Missing required column: {col}")

    df = df[required_cols].copy()
    df = df.dropna(subset=["sampling_type_subcategory"])

    samples_df = (
        df.groupby(
            ["sampling_type_main_category", "sampling_type_subcategory"],
            dropna=False,
        )
        .size()
        .reset_index(name="Samples")
    )

    df_country = df[~df["country_clean"].isin(["Antarctica", "Unknown"])]

    countries_df = (
        df_country.groupby(
            ["sampling_type_main_category", "sampling_type_subcategory"],
            dropna=False,
        )["country_clean"]
        .nunique()
        .reset_index(name="Countries")
    )

    table3 = samples_df.merge(
        countries_df,
        on=["sampling_type_main_category", "sampling_type_subcategory"],
        how="left",
    )

    table3["Countries"] = table3["Countries"].fillna(0).astype(int)

    main_order = (
        table3.groupby("sampling_type_main_category")["Samples"]
        .sum()
        .sort_values(ascending=False)
        .index
    )

    table3["sampling_type_main_category"] = pd.Categorical(
        table3["sampling_type_main_category"],
        categories=main_order,
        ordered=True,
    )

    table3 = table3.sort_values(
        ["sampling_type_main_category", "Samples"],
        ascending=[True, False],
        kind="mergesort",
    )

    table3 = table3.rename(
        columns={
            "sampling_type_main_category": "Group",
            "sampling_type_subcategory": "Sampling Types",
        }
    )

    table3 = table3[["Group", "Sampling Types", "Samples", "Countries"]]

    table3.to_csv(args.out, index=False, encoding="utf-8")

    print(f"Saved to: {args.out}")


if __name__ == "__main__":
    main()
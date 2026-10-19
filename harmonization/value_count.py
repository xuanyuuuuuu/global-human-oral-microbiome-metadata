import argparse
import os
import sys
import pandas as pd


def count_values(series: pd.Series, value_label: str) -> pd.DataFrame:
    """
    Count value frequencies in a column.
    - strip whitespace
    - empty strings ("") -> 'blank'
    - keep NaN as NaN
    """
    s = series.astype("object")
    s = s.apply(lambda x: x.strip() if isinstance(x, str) else x)
    s = s.replace("", "blank")
    vc = s.value_counts(dropna=False)

    df = vc.reset_index()
    df.columns = [value_label, "count"]
    df = df.sort_values(
        by=["count", value_label],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Count raw value frequencies for country and sampling type columns"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input CSV file"
    )
    parser.add_argument(
        "--country_col",
        default="country",
        help="Column name for country (default: country)"
    )
    parser.add_argument(
        "--type_col",
        default="sampling_type",
        help="Column name for sampling type (default: sampling_type)"
    )
    parser.add_argument(
        "--outdir",
        required=True,
        help="Output directory"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"File not found: {args.input}")

    os.makedirs(args.outdir, exist_ok=True)

    df_head = pd.read_csv(args.input, nrows=0)
    for col in [args.country_col, args.type_col]:
        if col not in df_head.columns:
            sys.exit(f"Missing required column: {col}")

    df = pd.read_csv(
        args.input,
        usecols=[args.country_col, args.type_col],
        dtype="object",
        low_memory=True,
    )

    country_df = count_values(df[args.country_col], "raw_geo_name")
    country_out = os.path.join(args.outdir, "country_value_count.csv")
    country_df.to_csv(country_out, index=False)
    print(f"Saved: {country_out} ({len(country_df)} rows)")

    type_df = count_values(df[args.type_col], "raw_type_name")
    type_out = os.path.join(args.outdir, "sampling_type_value_count.csv")
    type_df.to_csv(type_out, index=False)
    print(f"Saved: {type_out} ({len(type_df)} rows)")

    print("Done: NaN kept as NaN; empty strings converted to 'blank'.")


if __name__ == "__main__":
    main()

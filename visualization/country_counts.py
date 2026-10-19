import argparse
import os
import sys
import pandas as pd


EXCLUDED_FROM_SHARE = {"Unknown", "Antarctica"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"File not found: {args.input}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    df = pd.read_csv(args.input)

    for col in ["country_clean", "iso3"]:
        if col not in df.columns:
            sys.exit(f"Missing required column: {col}")

    res = (
        df.groupby(["country_clean", "iso3"], dropna=False)
        .size()
        .reset_index(name="sample_count")
    )

    known_total_n = (~df["country_clean"].isin(EXCLUDED_FROM_SHARE)).sum()

    if known_total_n == 0:
        sys.exit("No eligible country records found for share calculation.")

    res["sample_share"] = res["sample_count"] / known_total_n
    res.loc[res["country_clean"].isin(EXCLUDED_FROM_SHARE), "sample_share"] = pd.NA

    res["sort_group"] = res["country_clean"].isin(EXCLUDED_FROM_SHARE).astype(int)
    res = res.sort_values(
        by=["sort_group", "sample_count"],
        ascending=[True, False],
        kind="mergesort"
    ).drop(columns="sort_group")

    res = res[["country_clean", "iso3", "sample_count", "sample_share"]]

    known_sum = int(res.loc[~res["country_clean"].isin(EXCLUDED_FROM_SHARE), "sample_count"].sum())
    if known_sum != int(known_total_n):
        sys.exit("Sanity check failed: eligible country sample_count sum != known_total_n")

    res.to_csv(args.out, index=False, encoding="utf-8")

    print(f"[OK] Total samples: {len(df):,}")
    print(f"[OK] Samples used for share: {known_total_n:,}")
    print(f"[OK] Countries (incl. Unknown and Antarctica): {len(res):,}")
    print(f"[OK] Saved: {args.out}")


if __name__ == "__main__":
    main()
import argparse
import os
import sys
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Generate Table 1: sample counts and shares by country.")
    parser.add_argument("--input", required=True, help="Input CSV (must contain country_clean and iso3)")
    parser.add_argument("--out", required=True, help="Output CSV path, e.g., outputs/sample_by_country.csv")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"File not found: {args.input}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    df = pd.read_csv(args.input)

    # Required columns
    for col in ["country_clean", "iso3"]:
        if col not in df.columns:
            sys.exit(f"Missing required column: {col}")

    total_n = len(df)

    res = (
        df.groupby(["country_clean", "iso3"], dropna=False)
          .size()
          .reset_index(name="sample_count")
    )

    res["sample_share"] = res["sample_count"] / total_n
    res = res.sort_values("sample_count", ascending=False, kind="mergesort")
    res = res[["country_clean", "iso3", "sample_count", "sample_share"]]

    # Sanity check
    if int(res["sample_count"].sum()) != total_n:
        sys.exit("Sanity check failed: sum(sample_count) != total_n")

    res.to_csv(args.out, index=False, encoding="utf-8")

    print(f"[OK] Total samples: {total_n:,}")
    print(f"[OK] Countries (incl. Unknown): {len(res):,}")
    print(f"[OK] Saved: {args.out}")


if __name__ == "__main__":
    main()

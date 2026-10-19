import argparse
import os
import sys
import pandas as pd


def read_csv_or_exit(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        sys.exit(f"File not found: {path}")
    return pd.read_csv(path)


def ensure_cols(df: pd.DataFrame, cols, name: str):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        sys.exit(f"Missing required column(s) in {name}: {missing}")


def main():
    parser = argparse.ArgumentParser(
        description="Filter clean biosample subsets and export filtered tables + audit summary"
    )
    parser.add_argument("--clean_human_biosample", required=True, help="clean_human_biosample.csv")
    parser.add_argument("--clean_human_oral_biosample", required=True, help="clean_human_oral_biosample.csv")
    parser.add_argument("--clean_human_saliva_biosample", required=True, help="clean_human_saliva_biosample.csv")
    parser.add_argument("--clean_oral_biosample", required=True, help="clean_oral_biosample.csv")
    parser.add_argument("--outdir", required=True, help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    INPUTS = {
        "clean_human_biosample": args.clean_human_biosample,
        "clean_human_oral_biosample": args.clean_human_oral_biosample,
        "clean_human_saliva_biosample": args.clean_human_saliva_biosample,
        "clean_oral_biosample": args.clean_oral_biosample,
    }


    KEEP_UNKNOWN_TYPE_DATASETS = {
        "clean_human_oral_biosample",
        "clean_human_saliva_biosample",
        "clean_oral_biosample",
    }

    required_cols = ["sampling_type_include_flag", "host_clean"]

    filtered_dfs = []
    summary_rows = []

    for name, path in INPUTS.items():
        print(f"\n=== Processing {name} ===")
        df0 = read_csv_or_exit(path)
        ensure_cols(df0, required_cols, name)
        n_start = len(df0)

        mask_non_oral = df0["sampling_type_include_flag"] == 0
        n_non_oral_removed = int(mask_non_oral.sum())
        df1 = df0.loc[~mask_non_oral].copy()

        if name == "clean_oral_biosample":
            mask_non_human = df1["host_clean"] != "Human"
        else:
            mask_non_human = df1["host_clean"] == "Non-human"

        n_non_human_removed = int(mask_non_human.sum())
        df2 = df1.loc[~mask_non_human].copy()

        n_unknown_type_removed = 0
        if name not in KEEP_UNKNOWN_TYPE_DATASETS:
            mask_unknown_type = df2["sampling_type_include_flag"] == 2
            n_unknown_type_removed = int(mask_unknown_type.sum())
            df3 = df2.loc[~mask_unknown_type].copy()
        else:
            df3 = df2

        n_final = len(df3)
        n_total_removed = n_start - n_final

        out_path = os.path.join(args.outdir, f"filtered_{name}.csv")
        df3.to_csv(out_path, index=False)
        print(f"Saved: {out_path}")
        print(f"  Start: {n_start}")
        print(f"  Removed non-oral (include=0): {n_non_oral_removed}")
        print(f"  Removed non-human: {n_non_human_removed}")
        if name not in KEEP_UNKNOWN_TYPE_DATASETS:
            print(f"  Removed unknown type (include=2): {n_unknown_type_removed}")
        else:
            print("  Removed unknown type (include=2): 0  (kept for this subset)")
        print(f"  Total removed: {n_total_removed}")
        print(f"  Final kept: {n_final}")

        summary_rows.append({
            "dataset": name,
            "start_n": int(n_start),
            "removed_non_oral_include0": int(n_non_oral_removed),
            "removed_non_human": int(n_non_human_removed),
            "removed_unknown_type_include2": int(n_unknown_type_removed),
            "total_removed": int(n_total_removed),
            "final_n": int(n_final),
        })

        filtered_dfs.append(df3)

    summary_df = pd.DataFrame(summary_rows)
    summary_path = os.path.join(args.outdir, "filtering_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print("\n=== Filtering summary table ===")
    print(summary_df)
    print(f"Saved summary: {summary_path}")

    merged_df = pd.concat(filtered_dfs, ignore_index=True)
    merged_path = os.path.join(args.outdir, "merged_filtered_biosample.csv")
    merged_df.to_csv(merged_path, index=False)
    print("\n=== Final merged dataset ===")
    print(f"Total remaining biosamples: {len(merged_df)}")
    print(f"Saved merged: {merged_path}")


if __name__ == "__main__":
    main()

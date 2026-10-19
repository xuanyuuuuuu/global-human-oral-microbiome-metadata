import argparse
import pandas as pd


def clean_col(s):
    return (
        s.astype(str)
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runmeta", required=True)
    parser.add_argument("--biosample", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    runmeta = pd.read_csv(args.runmeta, dtype=str)
    biosample = pd.read_csv(args.biosample, dtype=str)

    runmeta["sample_accession"] = clean_col(runmeta["sample_accession"])
    biosample["accession"] = clean_col(biosample["accession"])

    runmeta = runmeta.dropna(subset=["sample_accession"])
    biosample = biosample.dropna(subset=["accession"])

    if "release_date" in runmeta.columns:
        runmeta = runmeta.sort_values("release_date")

    runmeta = runmeta.drop_duplicates(subset=["sample_accession"], keep="first")

    merged = biosample.merge(runmeta, left_on="accession", right_on="sample_accession", how="inner")

    merged["host_clean"] = merged["host_clean"].replace({"Unknown": "Human"})
    merged["sampling_type_main_category"] = merged["sampling_type_main_category"].replace({"Unknown": "Unspecified"})
    merged["sampling_type_subcategory"] = merged["sampling_type_subcategory"].replace({"Unknown": "Oral cavity (unspecified)"})

    merged = merged[
        [
            "sample_accession",
            "country",
            "country_clean",
            "iso3",
            "sampling_type_main_category",
            "sampling_type_subcategory",
            "host_clean",
            "run_accession",
            "study_accession",
            "release_date",
            "library_strategy",
            "library_source",
            "library_layout",
            "instrument_model",
        ]
    ]

    merged.to_csv(args.out, index=False)

    print("Rows:", len(merged))
    print("BioSamples:", merged["sample_accession"].nunique())
    print("Studies:", merged["study_accession"].nunique())


if __name__ == "__main__":
    main()
import argparse
import xml.etree.ElementTree as ET
import pandas as pd
import os
import sys

SAMPLING_TYPE_FIELDS = [
    "isolation_source",
    "sample_type",
    "sample_label",
    "sample_description",
    "host_body_site",
    "host_tissue_sampled",
    "env_medium",
    "niche",
]

HOST_FIELDS = [
    "host",
    "host_taxid",
    "host_scientific_name",
    "host_common_name",
]

COUNTRY_FIELDS = [
    "geo_loc_name",
    "geo loc name",
    "geographic location (country and/or sea)",
    "geographic location",
    "Geographical Location",
    "country",
    "nationality",
    "geographic location (region and locality)",
]


def pick_first_value(biosample, field_list):
    """
    Return the first non-empty attribute value according to priority order.
    """
    for field in field_list:
        for attr in biosample.iter("Attribute"):
            if attr.get("attribute_name") == field and attr.text:
                value = attr.text.strip()
                if value:
                    return value
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Extract and unify country, sampling-type, and host from a BioSample XML file"
    )
    parser.add_argument(
        "--xml",
        required=True,
        help="Input BioSample XML file"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV file"
    )
    args = parser.parse_args()

    if not os.path.exists(args.xml):
        sys.exit(f"File not found: {args.xml}")

    tree = ET.parse(args.xml)
    root = tree.getroot()

    rows = []

    for biosample in root.iter("BioSample"):
        rows.append({
            "accession": biosample.get("accession"),
            "country": pick_first_value(biosample, COUNTRY_FIELDS),
            "sampling_type": pick_first_value(biosample, SAMPLING_TYPE_FIELDS),
            "host": pick_first_value(biosample, HOST_FIELDS),
        })

    df = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    df.to_csv(args.out, index=False)

    print(f"Saved: {args.out}")
    print(df.head())


if __name__ == "__main__":
    main()

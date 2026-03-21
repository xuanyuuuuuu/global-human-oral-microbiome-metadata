import argparse
import xml.etree.ElementTree as ET
from collections import Counter
import pandas as pd
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Count attribute_name frequencies from BioSample XML files"
    )
    parser.add_argument(
        "--xml",
        nargs="+",
        required=True,
        help="One or more BioSample XML files"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV file"
    )
    args = parser.parse_args()

    total_counts = Counter()

    for xml_path in args.xml:
        if not os.path.exists(xml_path):
            sys.exit(f"File not found: {xml_path}")

        tree = ET.parse(xml_path)
        root = tree.getroot()

        for attr in root.iter("Attribute"):
            name = attr.get("attribute_name")
            if name:
                total_counts[name] += 1

    df = (
        pd.DataFrame(total_counts.items(), columns=["attribute_name", "count"])
        .sort_values("count", ascending=False)
    )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    df.to_csv(args.out, index=False)

    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()

import argparse
import os
import re
import sys
from pathlib import Path
from collections import Counter

import pandas as pd

def norm_text(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip().lower()
    s = re.sub(r"[\t\r\n]+", " ", s)
    s = s.replace("_", " ").replace("-", " ").replace("/", " ").replace(",", " ")
    s = s.replace(":", " ").replace(";", " ").replace("(", " ").replace(")", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_blank(x) -> bool:
    return (x is None) or (isinstance(x, float) and pd.isna(x)) or (str(x).strip() == "")


def load_host_map(path: str):
    df = pd.read_csv(path)
    term2cat = {}
    for _, r in df.iterrows():
        cat = str(r["Category"]).strip()
        raw_terms = "" if is_blank(r["Common Raw Values"]) else str(r["Common Raw Values"])
        terms = [t.strip() for t in raw_terms.split(";") if t.strip()]
        for t in terms:
            term2cat[norm_text(t)] = cat
    return term2cat


def load_type_map(path: str):
    df = pd.read_csv(path)
    exact_map = {}
    contains_list = []

    for _, r in df.iterrows():
        main = "" if is_blank(r["main_category"]) else str(r["main_category"]).strip()
        sub = "" if is_blank(r["subcategory"]) else str(r["subcategory"]).strip()
        amb = int(r["ambiguous_flag"]) if not is_blank(r["ambiguous_flag"]) else 0
        inc = int(r["include_flag"]) if not is_blank(r["include_flag"]) else 1

        raw_terms = "" if is_blank(r["terms"]) else str(r["terms"])
        terms = [t.strip() for t in raw_terms.split(";") if t.strip()]

        payload = (main, sub, amb, inc)
        for t in terms:
            t_norm = norm_text(t)
            if not t_norm:
                continue
            exact_map[t_norm] = payload
            contains_list.append((t_norm, payload))

    contains_list.sort(key=lambda x: len(x[0]), reverse=True)
    return exact_map, contains_list


def map_type(value_raw, exact_map, contains_list):
    if is_blank(value_raw):
        return ("Unknown", "Unknown", 0, 2)

    v = norm_text(value_raw)
    if v in exact_map:
        return exact_map[v]

    for t_norm, payload in contains_list:
        if t_norm and (t_norm in v):
            return payload

    return ("Unknown", "Unknown", 0, 2)


def load_country_map(path: str):
    df = pd.read_csv(path)
    exact_keyword_map = {}
    keywords_long = []
    keywords_short = []

    for _, r in df.iterrows():
        country = str(r["Country"]).strip()
        iso3 = str(r["ISO3"]).strip()
        raw_kw = "" if is_blank(r["Keywords"]) else str(r["Keywords"])
        kws = [k.strip() for k in raw_kw.split(";") if k.strip()]

        for kw in kws:
            kw_norm = norm_text(kw)
            if not kw_norm:
                continue
            exact_keyword_map[kw_norm] = (country, iso3)
            if len(kw_norm) < 4:
                keywords_short.append((kw_norm, (country, iso3)))
            else:
                keywords_long.append((kw_norm, (country, iso3)))

    keywords_long.sort(key=lambda x: len(x[0]), reverse=True)
    keywords_short.sort(key=lambda x: len(x[0]), reverse=True)
    return exact_keyword_map, keywords_long, keywords_short


def word_boundary_match(text_norm: str, token_norm: str) -> bool:
    pattern = r"\b" + re.escape(token_norm) + r"\b"
    return re.search(pattern, text_norm) is not None


def map_country(value_raw, exact_keyword_map, keywords_long, keywords_short):
    if is_blank(value_raw):
        return ("Unknown", "UNK")

    v = norm_text(value_raw)
    if v in exact_keyword_map:
        return exact_keyword_map[v]

    for kw_norm, payload in keywords_long:
        if kw_norm and (kw_norm in v):
            return payload

    for kw_norm, payload in keywords_short:
        if kw_norm and word_boundary_match(v, kw_norm):
            return payload

    return ("Unknown", "UNK")


def export_unmatched(raw_series: pd.Series, clean_series: pd.Series, out_path: Path):
    raw_vals = raw_series.fillna("").astype(str)
    clean_vals = clean_series.fillna("").astype(str)

    unmatched = []
    for rv, cv in zip(raw_vals, clean_vals):
        if rv.strip() == "":
            continue
        if cv.strip() == "" or cv.strip().lower() == "unknown":
            unmatched.append(rv.strip())

    c = Counter(unmatched)
    df_out = (
        pd.DataFrame(c.items(), columns=["raw_value", "count"])
        .sort_values("count", ascending=False)
    )
    df_out.to_csv(out_path, index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Harmonize raw country / sampling_type / host values using mapping CSV files"
    )
    parser.add_argument("--input", required=True, help="Input raw CSV (accession, country, sampling_type, host)")
    parser.add_argument("--country_map", required=True, help="country_map.csv")
    parser.add_argument("--host_map", required=True, help="host_map.csv")
    parser.add_argument("--type_map", required=True, help="sampling_type_map.csv")
    parser.add_argument("--outdir", required=True, help="Output directory")
    args = parser.parse_args()

    for p in [args.input, args.country_map, args.host_map, args.type_map]:
        if not os.path.isfile(p):
            sys.exit(f"File not found: {p}")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)

    expected_cols = ["accession", "country", "sampling_type", "host"]
    for col in expected_cols:
        if col not in df.columns:
            sys.exit(f"Missing required column: {col}")

    host_term2cat = load_host_map(args.host_map)
    type_exact, type_contains = load_type_map(args.type_map)
    country_exact, country_long, country_short = load_country_map(args.country_map)

    # Host clean
    HUMAN_CONTAINS_TOKENS = ["homo sapiens", "human", "people", "children", "patient", "patinet"]
    host_clean = []
    for v in df["host"]:
        if is_blank(v):
            host_clean.append("Unknown")
            continue

        vn = norm_text(v)

        if vn in host_term2cat:
            host_clean.append(host_term2cat[vn])
            continue

        is_human = False
        for token in HUMAN_CONTAINS_TOKENS:
            if token == "human":
                if re.search(r"\bhuman(?:\b|[\s#_\-]*\d+)", vn):
                    is_human = True
                    break
            else:
                if token in vn:
                    is_human = True
                    break

        host_clean.append("Human" if is_human else "Unknown")

    df["host_clean"] = host_clean

    # Type clean
    type_main, type_sub, type_amb, type_inc = [], [], [], []
    for v in df["sampling_type"]:
        main_cat, sub_cat, amb, inc = map_type(v, type_exact, type_contains)
        type_main.append(main_cat)
        type_sub.append(sub_cat)
        type_amb.append(int(amb))
        type_inc.append(int(inc))

    df["sampling_type_main_category"] = type_main
    df["sampling_type_subcategory"] = type_sub
    df["sampling_type_ambiguous_flag"] = type_amb
    df["sampling_type_include_flag"] = type_inc

    # Country clean
    country_clean, iso3 = [], []
    for v in df["country"]:
        c_std, c_iso3 = map_country(v, country_exact, country_long, country_short)
        country_clean.append(c_std)
        iso3.append(c_iso3)

    df["country_clean"] = country_clean
    df["iso3"] = iso3

    # Output clean table (minimal columns, fixed order)
    out_cols = [
        "accession",
        "country",
        "country_clean",
        "iso3",
        "sampling_type_main_category",
        "sampling_type_subcategory",
        "sampling_type_ambiguous_flag",
        "sampling_type_include_flag",
        "host",
        "host_clean",
    ]
    df_out = df[out_cols].copy()

    input_stem = Path(args.input).stem
    clean_path = outdir / f"clean_{input_stem}.csv"
    df_out.to_csv(clean_path, index=False)
    print(f"Saved: {clean_path}")

    # Unmatched exports
    export_unmatched(df["country"], df["country_clean"], outdir / f"unmatched_country_{input_stem}.csv")
    export_unmatched(df["sampling_type"], df["sampling_type_subcategory"], outdir / f"unmatched_sampling_type_{input_stem}.csv")
    export_unmatched(df["host"], df["host_clean"], outdir / f"unmatched_host_{input_stem}.csv")

    print("Saved unmatched files.")


if __name__ == "__main__":
    main()

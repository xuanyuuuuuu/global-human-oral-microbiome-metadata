import argparse
import csv
import gzip
import os
import time
import datetime as dt
from io import StringIO
from typing import List, Optional, Tuple

import pandas as pd
import requests

ENA_SEARCH_URL = "https://www.ebi.ac.uk/ena/portal/api/search"

ENA_FIELDS = [
    "run_accession",
    "sample_accession",
    "study_accession",
    "first_public",
    "last_updated",
    "library_strategy",
    "library_source",
    "library_layout",
    "instrument_model",
]

SLEEP_BASE_DEFAULT = 2.0

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def log_line(log_path: str, msg: str) -> None:
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def read_accessions(input_csv: str, col: str) -> List[str]:
    df = pd.read_csv(input_csv)
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in {input_csv}")

    acc = (
        df[col]
        .astype(str)
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
        .dropna()
        .tolist()
    )

    seen = set()
    out = []
    for a in acc:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def chunk_list(xs: List[str], n: int) -> List[List[str]]:
    return [xs[i:i + n] for i in range(0, len(xs), n)]


def build_terms(sample_ids: List[str], sub_batch_size: int, max_query_chars: int) -> List[List[str]]:
    terms, current = [], []
    for sid in sample_ids:
        candidate = current + [sid]
        q = " OR ".join([f'sample_accession="{x}"' for x in candidate])
        if len(candidate) > sub_batch_size or len(q) > max_query_chars:
            if current:
                terms.append(current)
            current = [sid]
        else:
            current = candidate
    if current:
        terms.append(current)
    return terms


def ena_request(query: str, fields: List[str], timeout: int) -> str:
    data = {
        "result": "read_run",
        "query": query,
        "fields": ",".join(fields),
        "format": "tsv",
        "download": "true",
        "limit": "0",
    }
    r = requests.post(ENA_SEARCH_URL, data=data, timeout=timeout)
    r.raise_for_status()
    return r.text


def tsv_to_df(tsv_text: str) -> pd.DataFrame:
    tsv_text = (tsv_text or "").strip()
    if not tsv_text:
        return pd.DataFrame()
    if tsv_text.startswith("<!DOCTYPE html"):
        raise ValueError("ENA returned HTML (temporary block or maintenance).")
    return pd.read_csv(StringIO(tsv_text), sep="\t", dtype=str)


def write_csv_gz(df: pd.DataFrame, out_path: str) -> None:
    ensure_dir(os.path.dirname(out_path))
    with gzip.open(out_path, "wt", encoding="utf-8") as gz:
        df.to_csv(gz, index=False)


def read_csv_gz(path: str) -> pd.DataFrame:
    with gzip.open(path, "rt", encoding="utf-8") as gz:
        return pd.read_csv(gz, dtype=str)


def batch_file_ok(path: str) -> bool:
    try:
        _ = read_csv_gz(path).head(1)
        return True
    except Exception:
        return False

def fetch_runmeta(
    sample_ids: List[str],
    log_path: str,
    retries: int,
    timeout: int,
    sub_batch_size: int,
    max_query_chars: int,
    sleep_base: float,
) -> Tuple[pd.DataFrame, List[str]]:

    terms = build_terms(sample_ids, sub_batch_size, max_query_chars)
    frames = []
    matched = set()

    for term_ids in terms:
        query = " OR ".join([f'sample_accession="{x}"' for x in term_ids])

        for attempt in range(1, retries + 1):
            try:
                df = tsv_to_df(ena_request(query, ENA_FIELDS, timeout))
                if not df.empty:
                    frames.append(df)
                    matched.update(df["sample_accession"].dropna())
                break
            except Exception as e:
                sleep_s = sleep_base * (2 ** (attempt - 1))
                log_line(log_path, f"ENA retry {attempt}/{retries}, sleep {sleep_s:.1f}s ({e})")
                time.sleep(sleep_s)

    if frames:
        out = pd.concat(frames, ignore_index=True)[ENA_FIELDS]
    else:
        out = pd.DataFrame(columns=ENA_FIELDS)

    unmatched = sorted(set(sample_ids) - set(matched))
    return out, unmatched

def main():
    p = argparse.ArgumentParser(description="Fetch minimal ENA run metadata by BioSample accession")
    p.add_argument("--input", required=True, help="Input CSV with BioSample accessions")
    p.add_argument("--accession_col", default="accession")
    p.add_argument("--outdir", required=True)
    p.add_argument("--batch_size", type=int, default=500)
    p.add_argument("--sub_batch_size", type=int, default=80)
    p.add_argument("--max_query_chars", type=int, default=1800)
    p.add_argument("--retries", type=int, default=4)
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--sleep_base", type=float, default=SLEEP_BASE_DEFAULT)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()

    ensure_dir(args.outdir)
    batch_dir = os.path.join(args.outdir, "runmeta_batches")
    log_dir = os.path.join(args.outdir, "logs")
    ensure_dir(batch_dir)
    ensure_dir(log_dir)

    log_path = os.path.join(log_dir, f"ena_runmeta_{dt.datetime.now():%Y%m%d}.log")
    log_line(log_path, "ENA minimal run metadata fetch started")

    ids = read_accessions(args.input, args.accession_col)
    batches = chunk_list(ids, args.batch_size)

    all_unmatched = []

    for i, batch in enumerate(batches, 1):
        out_name = f"runmeta_batch_{i:05d}.csv.gz"
        out_path = os.path.join(batch_dir, out_name)

        if args.resume and os.path.exists(out_path) and batch_file_ok(out_path):
            log_line(log_path, f"Skip batch {i} (resume)")
            continue

        df, unmatched = fetch_runmeta(
            batch,
            log_path,
            args.retries,
            args.timeout,
            args.sub_batch_size,
            args.max_query_chars,
            args.sleep_base,
        )

        write_csv_gz(df, out_path)
        log_line(log_path, f"Batch {i}: {len(df)} rows")

        all_unmatched.extend(unmatched)

    merged = pd.concat(
        [read_csv_gz(os.path.join(batch_dir, f)) for f in os.listdir(batch_dir)],
        ignore_index=True
    )
    merged = merged.rename(columns={
        "first_public": "release_date",
        "last_updated": "load_date",
    })
    final_cols = [
        "run_accession",
        "sample_accession",
        "study_accession",
        "release_date",
        "load_date",
        "library_strategy",
        "library_source",
        "library_layout",
        "instrument_model",
    ]
    merged = merged[final_cols]
    merged_out = os.path.join(args.outdir, "runmeta_all_runs.csv.gz")
    write_csv_gz(merged, merged_out)
    log_line(log_path, f"Merged rows: {len(merged)}")

    if all_unmatched:
        pd.Series(sorted(set(all_unmatched))).to_csv(
            os.path.join(args.outdir, "unmatched_biosamples.csv"),
            index=False,
            header=["sample_accession"],
        )

    log_line(log_path, "Done")


if __name__ == "__main__":
    main()

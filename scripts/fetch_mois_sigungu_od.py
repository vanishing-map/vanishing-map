#!/usr/bin/env python3
import argparse
import csv
import getpass
import json
import math
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path


ENDPOINT = "https://apis.data.go.kr/1741000/ppltnDataStus/selectPpltnDataStus"
SOURCE_ENDPOINT = "ppltnDataStus/selectPpltnDataStus"

REGIONS = [
    ("1100000000", "서울특별시"),
    ("2600000000", "부산광역시"),
    ("2700000000", "대구광역시"),
    ("2800000000", "인천광역시"),
    ("2900000000", "광주광역시"),
    ("3000000000", "대전광역시"),
    ("3100000000", "울산광역시"),
    ("3600000000", "세종특별자치시"),
    ("4100000000", "경기도"),
    ("4300000000", "충청북도"),
    ("4400000000", "충청남도"),
    ("4600000000", "전라남도"),
    ("4700000000", "경상북도"),
    ("4800000000", "경상남도"),
    ("5000000000", "제주특별자치도"),
    ("5100000000", "강원특별자치도"),
    ("5200000000", "전북특별자치도"),
]

AGE_BINS = {
    "age_0_14": range(0, 15),
    "age_15_24": range(15, 25),
    "age_25_39": range(25, 40),
    "age_40_54": range(40, 55),
    "age_55_64": range(55, 65),
    "age_65_plus": range(65, 111),
}

FIELDS = [
    "period",
    "origin_province_code",
    "origin_province",
    "origin_code",
    "origin",
    "destination_province_code",
    "destination_province",
    "destination_code",
    "destination",
    "people",
    "male",
    "female",
    "age_0_14",
    "age_0_14_male",
    "age_0_14_female",
    "age_15_24",
    "age_15_24_male",
    "age_15_24_female",
    "age_25_39",
    "age_25_39_male",
    "age_25_39_female",
    "age_40_54",
    "age_40_54_male",
    "age_40_54_female",
    "age_55_64",
    "age_55_64_male",
    "age_55_64_female",
    "age_65_plus",
    "age_65_plus_male",
    "age_65_plus_female",
    "level",
    "source_status",
    "source_endpoint",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", default="202605")
    parser.add_argument("--out", default="data/mois-ppltn-data-stus-sigungu-od-202605-age-gender.csv")
    parser.add_argument("--metadata-out", default="data/mois-ppltn-data-stus-sigungu-od-202605-age-gender-metadata.json")
    parser.add_argument("--sleep", type=float, default=0.04)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--retries", type=int, default=2)
    return parser.parse_args()


def number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def age_count(item, prefix, ages):
    return sum(number(item.get(f"{prefix}{age}AgeNmprCnt")) for age in ages)


def fetch_page(service_key, period, origin_code, destination_code, page_no, timeout):
    params = {
        "serviceKey": service_key,
        "mvinAdmmCd": destination_code,
        "mvtAdmmCd": origin_code,
        "srchFrYm": period,
        "srchToYm": period,
        "lv": "2",
        "type": "json",
        "numOfRows": "100",
        "pageNo": str(page_no),
    }
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    obj = json.loads(payload)
    response = obj.get("Response", {})
    head = response.get("head", {})
    if str(head.get("resultCode")) != "0":
        raise RuntimeError(f"{head.get('resultCode')}: {head.get('resultMsg')}")
    items = response.get("items", {}).get("item", [])
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        items = []
    total_count = number(head.get("totalCount"))
    return total_count, items


def fetch_pair(service_key, period, origin_code, destination_code, timeout, retries):
    rows = []
    total_count = None
    page_count = 1
    for page_no in range(1, 1000):
        last_error = None
        for attempt in range(retries + 1):
            try:
                total_count, items = fetch_page(service_key, period, origin_code, destination_code, page_no, timeout)
                break
            except Exception as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(0.6 + attempt * 0.8)
        else:
            raise last_error
        rows.extend(items)
        page_count = max(1, math.ceil((total_count or 0) / 100))
        if page_no >= page_count:
            return rows, total_count or len(rows), page_count
    return rows, total_count or len(rows), page_count


def normalize(item, origin_province_code, destination_province_code):
    male = number(item.get("maleNmprCnt")) or age_count(item, "male", range(0, 111))
    female = number(item.get("femlNmprCnt")) or age_count(item, "feml", range(0, 111))
    row = {
        "period": str(item.get("statsYm", ""))[:6],
        "origin_province_code": origin_province_code,
        "origin_province": item.get("mvtCtpvNm", ""),
        "origin_code": item.get("mvtAdmmCd", ""),
        "origin": item.get("mvtSggNm", "") or item.get("mvtCtpvNm", ""),
        "destination_province_code": destination_province_code,
        "destination_province": item.get("mvinCtpvNm", ""),
        "destination_code": item.get("mvinAdmmCd", ""),
        "destination": item.get("mvinSggNm", "") or item.get("mvinCtpvNm", ""),
        "people": number(item.get("totNmprCnt")) or male + female,
        "male": male,
        "female": female,
        "level": "sigungu",
        "source_status": "official_mois",
        "source_endpoint": SOURCE_ENDPOINT,
    }
    for key, ages in AGE_BINS.items():
        row[f"{key}_male"] = age_count(item, "male", ages)
        row[f"{key}_female"] = age_count(item, "feml", ages)
        row[key] = row[f"{key}_male"] + row[f"{key}_female"]
    return row


def main():
    args = parse_args()
    service_key = os.environ.get("MOIS_SERVICE_KEY") or getpass.getpass("MOIS serviceKey: ").strip()
    rows = []
    errors = []
    requested_pages = 0
    total_pairs = len(REGIONS) * len(REGIONS)
    done = 0

    for origin_code, origin_name in REGIONS:
        for destination_code, destination_name in REGIONS:
            done += 1
            try:
                items, total_count, page_count = fetch_pair(
                    service_key,
                    args.period,
                    origin_code,
                    destination_code,
                    args.timeout,
                    args.retries,
                )
                requested_pages += page_count
                rows.extend(normalize(item, origin_code, destination_code) for item in items)
                print(f"{done}/{total_pairs} {origin_name}->{destination_name} rows={len(items)}/{total_count} pages={page_count}", flush=True)
            except Exception as exc:
                errors.append({
                    "origin_code": origin_code,
                    "destination_code": destination_code,
                    "error": str(exc),
                })
                print(f"{done}/{total_pairs} {origin_name}->{destination_name} error={exc}", flush=True)
            time.sleep(args.sleep)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    interregional = out.with_name(out.stem + "-interregional.csv")
    with interregional.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(row for row in rows if row["origin_code"] != row["destination_code"])

    metadata = {
        "source": "행정안전부_지역별 인구이동 현황",
        "endpoint": ENDPOINT,
        "period": args.period,
        "level": "sigungu",
        "province_count": len(REGIONS),
        "requested_province_pairs": total_pairs,
        "requested_pages": requested_pages,
        "normalized_rows": len(rows),
        "interregional_rows": sum(1 for row in rows if row["origin_code"] != row["destination_code"]),
        "age_bins": list(AGE_BINS.keys()),
        "gender_fields": ["all", "male", "female"],
        "error_count": len(errors),
        "errors": errors[:100],
        "api_key_saved": False,
    }
    Path(args.metadata_out).write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"wrote {interregional}")
    print(f"wrote {args.metadata_out}")
    print(f"errors {len(errors)}")


if __name__ == "__main__":
    main()

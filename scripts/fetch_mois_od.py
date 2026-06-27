#!/usr/bin/env python3
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import getpass
import json
import subprocess
import urllib.parse
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

FIELDS = [
    "period",
    "origin_code",
    "origin",
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

AGE_BINS = {
    "age_0_14": range(0, 15),
    "age_15_24": range(15, 25),
    "age_25_39": range(25, 40),
    "age_40_54": range(40, 55),
    "age_55_64": range(55, 65),
    "age_65_plus": range(65, 111),
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="202210")
    parser.add_argument("--end", default="202605")
    parser.add_argument("--out", default="data/mois-ppltn-data-stus-sido-od-monthly-age-gender.csv")
    parser.add_argument("--metadata-out", default="data/mois-ppltn-data-stus-sido-od-monthly-age-gender-metadata.json")
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--workers", type=int, default=10)
    return parser.parse_args()


def month_range(start, end):
    year = int(start[:4])
    month = int(start[4:])
    end_i = int(end)
    while year * 100 + month <= end_i:
        yield f"{year}{month:02d}"
        month += 1
        if month == 13:
            year += 1
            month = 1


def number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def age_count(item, prefix, ages):
    return sum(number(item.get(f"{prefix}{age}AgeNmprCnt")) for age in ages)


def item_period(item, fallback):
    for key in ("statsYm", "statsYmd", "srchYm", "prdDe", "baseYm"):
        value = str(item.get(key, "")).strip()
        if len(value) >= 6 and value[:6].isdigit():
            return value[:6]
    return fallback


def normalize(item, fallback_period, origin_code, origin_name, destination_code, destination_name):
    male = age_count(item, "male", range(0, 111))
    female = age_count(item, "feml", range(0, 111))
    row = {
        "period": item_period(item, fallback_period),
        "origin_code": origin_code,
        "origin": item.get("mvtCtpvNm") or origin_name,
        "destination_code": destination_code,
        "destination": item.get("mvinCtpvNm") or destination_name,
        "male": male,
        "female": female,
        "people": male + female,
        "level": "sido",
        "source_status": "official_mois",
        "source_endpoint": SOURCE_ENDPOINT,
    }
    for key, ages in AGE_BINS.items():
        row[f"{key}_male"] = age_count(item, "male", ages)
        row[f"{key}_female"] = age_count(item, "feml", ages)
        row[key] = row[f"{key}_male"] + row[f"{key}_female"]
    return row


def chunks(items, size):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def fetch_range(service_key, start_period, end_period, origin_code, destination_code, timeout):
    params = {
        "serviceKey": service_key,
        "mvinAdmmCd": destination_code,
        "mvtAdmmCd": origin_code,
        "srchFrYm": start_period,
        "srchToYm": end_period,
        "lv": "1",
        "type": "json",
        "numOfRows": "100",
        "pageNo": "1",
    }
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
    result = subprocess.run(
        ["curl", "-fsS", "--max-time", str(timeout), url],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = result.stdout
    obj = json.loads(payload)
    response = obj.get("Response", {})
    head = response.get("head", {})
    if str(head.get("resultCode")) != "0":
        raise RuntimeError(f"{head.get('resultCode')}: {head.get('resultMsg')}")
    items = response.get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return items
    return []


def fetch_task(service_key, task, timeout, retries):
    start_period, end_period, origin_code, origin_name, destination_code, destination_name = task
    label = f"{start_period}-{end_period}"
    last_error = None
    for _attempt in range(retries + 1):
        try:
            items = fetch_range(service_key, start_period, end_period, origin_code, destination_code, timeout)
            rows = [
                normalize(item, start_period, origin_code, origin_name, destination_code, destination_name)
                for item in items
            ]
            errors = []
            if not items:
                errors.append({"period": label, "origin_code": origin_code, "destination_code": destination_code, "error": "empty"})
            return rows, errors
        except Exception as exc:
            last_error = exc
    return [], [{"period": label, "origin_code": origin_code, "destination_code": destination_code, "error": str(last_error)}]


def main():
    args = parse_args()
    service_key = getpass.getpass("MOIS serviceKey: ").strip()
    rows = []
    errors = []
    months = list(month_range(args.start, args.end))
    request_chunks = list(chunks(months, 3))
    tasks = []
    for period_chunk in request_chunks:
        start_period = period_chunk[0]
        end_period = period_chunk[-1]
        for origin_code, origin_name in REGIONS:
            for destination_code, destination_name in REGIONS:
                tasks.append((start_period, end_period, origin_code, origin_name, destination_code, destination_name))

    done = 0
    total_requests = len(tasks)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(fetch_task, service_key, task, args.timeout, args.retries) for task in tasks]
        for future in as_completed(futures):
            task_rows, task_errors = future.result()
            rows.extend(task_rows)
            errors.extend(task_errors)
            done += 1
            if done % 25 == 0 or done == total_requests:
                print(f"progress {done}/{total_requests}", flush=True)

    rows.sort(key=lambda row: (str(row["period"]), str(row["origin_code"]), str(row["destination_code"])))

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
        writer.writerows(row for row in rows if row["origin"] != row["destination"])

    metadata = {
        "source": "행정안전부_지역별 인구이동 현황",
        "endpoint": ENDPOINT,
        "period_start": args.start,
        "period_end": args.end,
        "level": "sido",
        "region_count": len(REGIONS),
        "months_requested": len(months),
        "requested_pairs": total_requests,
        "normalized_rows": len(rows),
        "interregional_rows": sum(1 for row in rows if row["origin"] != row["destination"]),
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

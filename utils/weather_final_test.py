"""weather_forecast.py – v1.11 (2025‑06‑09)
================================================
CLI 스크립트 하나로 **단기(0‑4일)** · **중기(5‑10일)** 예보를 조회합니다.

- 단기 예보: `getVilageFcst` API
- 중기 예보: `getMidLandFcst`, `getMidTa` API

특징
-----
* **네트워크 예외**를 삼켜 가급적 스크립트가 중단되지 않음.
* `pandas` 미설치 환경에서도 동작하지만, 설치돼 있으면 더 깔끔한 요약.
* 인자 없이 실행하면 **대화형**으로 시작·종료 날짜와 지역을 물어봄.
* `python weather_forecast.py --test` 로 단위 테스트 8건 실행 가능.

> ⚠️ 실제 실행 전 `SERVICE_KEY` 변수에 발급받은 *기상청 인증키*를 입력하세요.
"""

from __future__ import annotations

# ───────────────────────── Imports ──────────────────────────
import argparse
import datetime as _dt
import sys
import unittest
from datetime import timedelta
from typing import Optional, Tuple, List
import xml.etree.ElementTree as ET

try:
    import requests  # HTTP 호출용 (없을 수도 있음)
except ImportError:  # pragma: no cover – 테스트·로컬 환경 대응
    requests = None  # type: ignore

try:
    import pandas as pd  # 단기 예보 요약용(선택)
except ImportError:  # pragma: no cover
    pd = None  # type: ignore

# ───────────────────────── Settings ─────────────────────────
SERVICE_KEY = "YOUR_KMA_SERVICE_KEY"  # ← 여기에 서비스키 입력

region_xy: dict[str, Tuple[int, int]] = {
    "강원": (83, 130),
    "경기": (61, 124),
    "경남": (85, 77),
    "경북": (91, 100),
    "광주": (59, 74),
    "대구": (89, 91),
    "대전": (67, 100),
    "부산": (98, 75),
    "서울": (60, 126),
    "세종": (65, 104),
    "울산": (102, 84),
    "인천": (54, 125),
    "전남": (60, 68),
    "전북": (62, 87),
    "제주": (53, 36),
    "충남": (58, 104),
    "충북": (73, 109),
}

REGION_CODE_MAP: dict[str, Tuple[str, str]] = {
    "서울": ("11B00000", "11B10101"),
    "인천": ("11B00000", "11B20201"),
    "경기": ("11B00000", "11B20601"),
    "강원": ("11D10000", "11D10301"),
    "대전": ("11C20000", "11C20401"),
    "세종": ("11C20000", "11C20404"),
    "충북": ("11C10000", "11C10301"),
    "충남": ("11C20000", "11C20101"),
    "광주": ("11F20000", "11F20501"),
    "전북": ("11F10000", "11F10201"),
    "전남": ("11F20000", "11F20401"),
    "대구": ("11H10000", "11H10201"),
    "경북": ("11H10000", "11H10701"),
    "부산": ("11H20000", "11H20201"),
    "울산": ("11H20000", "11H20101"),
    "경남": ("11H20000", "11H20301"),
    "제주": ("11G00000", "11G00201"),
}

sky_map = {"1": "맑음", "3": "구름많음", "4": "흐림"}
pty_map = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}

# ───────────────────────── Helpers ──────────────────────────

def safe_get(url: str, *, params: dict) -> Optional[bytes]:
    """`requests.get` 래퍼 – 네트워크 오류 시 None 반환"""
    if requests is None:
        return None
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def get_latest_tmfc(now: Optional[_dt.datetime] = None) -> str:
    """가장 최근(06·18시) 중기예보 발표 시각을 반환 (YYYYMMDDHHMM)"""
    now = now or _dt.datetime.now()
    if now.hour < 6:
        return (now - timedelta(days=1)).strftime("%Y%m%d") + "1800"
    if now.hour < 18:
        return now.strftime("%Y%m%d") + "0600"
    return now.strftime("%Y%m%d") + "1800"

# ─────────────────────── Short‑term Forecast ───────────────────────


def _get_base_datetime(now: Optional[_dt.datetime] = None) -> Tuple[str, str]:
    now = now or _dt.datetime.now()
    base_times = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]
    hm = now.strftime("%H%M")
    for bt in reversed(base_times):
        if hm >= bt:
            return now.strftime("%Y%m%d"), bt
    return (now - timedelta(days=1)).strftime("%Y%m%d"), "2300"


def get_short_term_forecast(
    date: _dt.date, region: str, *, now: Optional[_dt.datetime] = None
) -> str:
    nx, ny = region_xy.get(region, region_xy["서울"])
    base_date, base_time = _get_base_datetime(now)

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    p = {
        "serviceKey": SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "XML",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    content = safe_get(url, params=p)
    if content is None:
        return f"📅 {date:%Y-%m-%d} 🌐 네트워크 오류: 단기 예보 불가"

    root = ET.fromstring(content)
    rows: List[dict[str, str]] = []
    for it in root.findall(".//item"):
        if it.findtext("fcstDate") != date.strftime("%Y%m%d"):
            continue
        rows.append(
            {
                "시간": it.findtext("fcstTime"),
                "항목": it.findtext("category"),
                "값": it.findtext("fcstValue"),
            }
        )

    if not rows:
        return f"📅 {date:%Y-%m-%d} 📭 단기 예보 데이터 없음"

    if pd is None:
        return f"📅 {date:%Y-%m-%d} (pandas 미설치로 요약 불가)"

    df = pd.DataFrame(rows)
    sky = df[df["항목"] == "SKY"]["값"].mode()
    pty = df[df["항목"] == "PTY"]["값"].mode()
    pop = df[df["항목"] == "POP"]["값"].astype(int).max()
    tmp = df[df["항목"] == "TMP"]["값"].astype(float)

    min_tmp = tmp.min() if not tmp.empty else "-"
    max_tmp = tmp.max() if not tmp.empty else "-"
    sky_txt = sky_map.get(sky.iloc[0], "정보 없음") if not sky.empty else "정보 없음"
    pty_txt = pty_map.get(pty.iloc[0], "정보 없음") if not pty.empty else "정보 없음"

    return (
        f"📅 {date:%Y-%m-%d} 단기 예보\n"
        f"☁️ 하늘 상태: {sky_txt}\n"
        f"🌧️ 강수 형태: {pty_txt}\n"
        f"🌂 강수 확률: {pop}%\n"
        f"🌡️ 최저/최고 기온: {min_tmp}℃ / {max_tmp}℃\n"
    )

# ─────────────────────── Mid‑term Forecast ───────────────────────

MID_LAND_URL = "http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst"
MID_TEMP_URL = "http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa"


def _parse_mid_land(item: ET.Element, delta: int) -> Tuple[str, str]:
    """delta(3‑10) 파싱 → (weather, rainProb)"""
    if 3 <= delta <= 7:
        wf_am = item.findtext(f"wf{delta}Am") or "-"
        wf_pm = item.findtext(f"wf{delta}Pm") or "-"
        rn_am = item.findtext(f"rnSt{delta}Am") or "-"
        rn_pm = item.findtext(f"rnSt")

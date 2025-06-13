from typing import List, Dict
from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
from urllib.request import Request, urlopen
import os
import time

# ⏱️ 캐시 저장소 (메모리)
_accommodation_cache: Dict[tuple, tuple] = {}


def get_accommodations(
    region: str,
    checkin: str,
    checkout: str,
    person: str
) -> List[Dict[str, str]]:
    """
    지정된 지역, 체크인/체크아웃 일정, 인원 수로 숙소를 검색해서
    상위 3개의 숙소 정보를 [
      {"name": ..., "image": ..., "url": ...},
      ...
    ] 형태로 반환합니다.
    - image: 다운로드된 로컬 파일 경로 (이미 존재하면 재사용)
    - url: 예약 페이지(검색 결과) URL
    """
    key = (region, checkin, checkout, person)
    now = time.time()

    # 1) 캐시 확인 (유효시간: 1시간)
    if key in _accommodation_cache:
        data, ts = _accommodation_cache[key]
        if now - ts < 3600:
            return data

    # 2) 검색 URL 생성
    region_encoded = urllib.parse.quote(region)
    search_url = (
        f"https://www.yeogi.com/domestic-accommodations"
        f"?keyword={region_encoded}"
        f"&checkIn={checkin}"
        f"&checkOut={checkout}"
        f"&personal={person}"
        f"&freeForm=false"
    )

    # 3) HTTP 요청 및 파싱
    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/123.0.0.0 Safari/537.36"
    }
    req = Request(search_url, headers=headers)
    page = urlopen(req)
    soup = BeautifulSoup(page, "html.parser")

    # 4) 숙소 이름 및 이미지 URL 추출 (상위 3개)
    names = [tag.get_text() for tag in soup.find_all("h3")[:3]]
    images = [img["src"] for img in soup.find_all("img", alt=True)[:3]]

    # 5) 결과 목록 생성
    results: List[Dict[str, str]] = []
    for idx, name in enumerate(names):
        img_url = images[idx]
        local_filename = f"{region}_숙소{idx+1}.jpg"

        # 이미지가 없으면 다운로드
        if not os.path.exists(local_filename):
            urllib.request.urlretrieve(img_url, local_filename)

        results.append({
            "name": name,
            "image": local_filename,
            "url": search_url,
        })

    # 6) 캐시 저장
    _accommodation_cache[key] = (results, now)

    return results

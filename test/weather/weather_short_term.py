import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

# 지역 좌표 사전
region = {
    "강원도": [83, 130],
    "경기도": [61, 124],
    "경상남도": [85, 77],
    "경상북도": [91, 100],
    "광주광역시": [59, 74],
    "대구광역시": [89, 91],
    "대전광역시": [67, 100],
    "부산광역시": [98, 75],
    "서울특별시": [60, 126],
    "세종특별자치시": [65, 104],
    "울산광역시": [102, 84],
    "인천광역시": [54, 125],
    "전라남도": [60, 68],
    "전라북도": [62, 87],
    "제주특별자치도": [53, 36],
    "충청남도": [58, 104],
    "충청북도": [73, 109]
}

# 사용자 입력
region_input = input("지역을 입력하세요 (예: 서울특별시): ").strip()
input_date = input("조회할 날짜를 입력하세요 (예: 20250521, 비워두면 오늘 기준): ").strip()

# 기본값: 오늘 날짜
if not input_date:
    input_date = datetime.now().strftime('%Y%m%d')

# 지역 좌표 확인 및 설정
if region_input in region:
    nx, ny = map(str, region[region_input])
else:
    print("입력한 지역이 목록에 없습니다.")
    exit()

# 예보 발표 기준 시각 계산 함수
def get_base_datetime(now):
    base_times = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']
    current_time = now.strftime('%H%M')
    for bt in reversed(base_times):
        if current_time >= bt:
            return now.strftime('%Y%m%d'), bt
    yesterday = now - timedelta(days=1)
    return yesterday.strftime('%Y%m%d'), '2300'

now = datetime.now()
base_date, base_time = get_base_datetime(now)

# API 요청
url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
params = {
    'serviceKey': 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A==',
    'pageNo': '1',
    'numOfRows': '1000',
    'dataType': 'XML',
    'base_date': base_date,
    'base_time': base_time,
    'nx': nx,
    'ny': ny
}

response = requests.get(url, params=params)
root = ET.fromstring(response.content)

# 항목 파싱
items = root.findall('.//item')
data = []
for item in items:
    try:
        category = item.findtext('category')
        fcst_date = item.findtext('fcstDate')
        fcst_time = item.findtext('fcstTime')
        fcst_value = item.findtext('fcstValue')

        if None in (category, fcst_date, fcst_time, fcst_value):
            continue

        data.append({
            '날짜': fcst_date,
            '시간': fcst_time,
            '항목': category,
            '값': fcst_value
        })
    except Exception as e:
        print("파싱 중 오류:", e)
        continue

# DataFrame 생성
df = pd.DataFrame(data)
if df.empty:
    print("📭 예보 데이터가 없습니다.")
    exit()

# 입력 날짜 필터링
df_day = df[df['날짜'] == input_date]

if df_day.empty:
    print(f"⛅ {input_date} 예보 데이터가 존재하지 않습니다.")
    exit()

# 오전/오후 구분
am_times = [f"{h:02}00" for h in range(6, 12)]
pm_times = [f"{h:02}00" for h in range(12, 18)]

# 하늘 상태 코드 해석
sky_map = {
    '1': '맑음',
    '3': '구름많음',
    '4': '흐림'
}

# 강수 형태 코드 해석
pty_map = {
    '0': '없음',
    '1': '비',
    '2': '비/눈',
    '3': '눈',
    '4': '소나기'
}


def describe_weather(sub_df):
    desc = {}
    if not sub_df.empty:
        # 하늘 상태
        sky = sub_df[sub_df['항목'] == 'SKY']['값'].mode()
        if not sky.empty:
            desc['하늘'] = sky_map.get(sky.iloc[0], '알 수 없음')

        # 강수 형태
        pty = sub_df[sub_df['항목'] == 'PTY']['값'].mode()
        if not pty.empty:
            desc['강수'] = pty_map.get(pty.iloc[0], '알 수 없음')

        # 강수 확률
        pop = sub_df[sub_df['항목'] == 'POP']['값'].astype(int).max()
        desc['강수확률'] = f"{pop}%" if not pd.isna(pop) else None

    return desc

# 최저/최고기온 계산
temps = df_day[df_day['항목'] == 'TMP']
temps['값'] = temps['값'].astype(float)
min_temp = temps['값'].min()
max_temp = temps['값'].max()

# 오전/오후 날씨 요약
am_df = df_day[df_day['시간'].isin(am_times)]
pm_df = df_day[df_day['시간'].isin(pm_times)]

am_desc = describe_weather(am_df)
pm_desc = describe_weather(pm_df)

# 출력
print(f"\n📍 [{region_input}] {input_date} 날씨 정보")
print(f" 🥶 최저기온: {min_temp} ℃")
print(f" 🔥 최고기온: {max_temp} ℃")

print("\n☀️ 오전 예보:")
if am_desc:
    print(f"  - 하늘 상태: {am_desc.get('하늘', '정보 없음')}")
    print(f"  - 강수 형태: {am_desc.get('강수', '정보 없음')}")
    print(f"  - 강수 확률: {am_desc.get('강수확률', '정보 없음')}")
else:
    print("  - 데이터 없음")

print("\n🌇 오후 예보:")
if pm_desc:
    print(f"  - 하늘 상태: {pm_desc.get('하늘', '정보 없음')}")
    print(f"  - 강수 형태: {pm_desc.get('강수', '정보 없음')}")
    print(f"  - 강수 확률: {pm_desc.get('강수확률', '정보 없음')}")
else:
    print("  - 데이터 없음")


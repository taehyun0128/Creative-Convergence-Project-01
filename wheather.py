import requests
import xml.etree.ElementTree as ET
import pandas as pd

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
input_date = input("조회할 날짜를 입력하세요 (예: 20250521): ").strip()
input_time = input("조회할 시간(24시간 형식, 예: 1500): ").strip()

# 지역 좌표 확인 및 설정
if region_input in region:
    nx, ny = map(str, region[region_input])
    print(nx,ny)
else:
    print("입력한 지역이 목록에 없습니다.")
    print(region_input)
    exit()

# 예보 기준 날짜와 시간 (오늘 날짜 이전이어야 함!)
base_date = '20250521'
base_time = '0200'

# 요청
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
    category = item.find('category').text
    fcst_date = item.find('fcstDate').text
    fcst_time = item.find('fcstTime').text
    fcst_value = item.find('fcstValue').text
    data.append({
        '날짜': fcst_date,
        '시간': fcst_time,
        '항목': category,
        '값': fcst_value
    })

df = pd.DataFrame(data)

# 필터링
target_categories = ['TMP', 'SKY', 'PTY', 'POP']
filtered = df[(df['날짜'] == input_date) & (df['시간'] == input_time) & (df['항목'].isin(target_categories))]

# 항목별 해석 딕셔너리
sky_map = {'1': '맑음', '3': '구름많음', '4': '흐림'}
pty_map = {'0': '없음', '1': '비', '2': '비/눈', '3': '눈', '4': '소나기'}

# 출력
print(f"\n[{region_input}] {input_date} {input_time} 기준 날씨 정보:")
for _, row in filtered.iterrows():
    item = row['항목']
    value = row['값']
    
    if item == 'TMP':
        print(f" 기온: {value} ℃")
    elif item == 'SKY':
        print(f" 하늘 상태: {sky_map.get(value, '알 수 없음')}")
    elif item == 'PTY':
        print(f" 강수 형태: {pty_map.get(value, '알 수 없음')}")
    elif item == 'POP':
        print(f" 강수 확률: {value}%")

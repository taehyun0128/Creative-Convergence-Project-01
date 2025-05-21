import requests
import xml.etree.ElementTree as ET
import pandas as pd

# 사용자 입력
input_date = input("조회할 날짜를 입력하세요 (예: 20250521): ").strip()
input_time = input("조회할 시간(24시간 형식, 예: 1500): ").strip()

# 예보 기준 날짜와 시간 (오늘 날짜 이전이어야 함!)
base_date = '20250521'
base_time = '0800'
nx, ny = '55', '127'  # 서울 종로구 기준

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
print(f"\n📅 {input_date} ⏰ {input_time} 기준 날씨 정보:")
for _, row in filtered.iterrows():
    item = row['항목']
    value = row['값']
    
    if item == 'TMP':
        print(f"🌡️ 기온: {value}℃")
    elif item == 'SKY':
        print(f"🌤️ 하늘 상태: {sky_map.get(value, '알 수 없음')}")
    elif item == 'PTY':
        print(f"🌧️ 강수 형태: {pty_map.get(value, '알 수 없음')}")
    elif item == 'POP':
        print(f"☔ 강수 확률: {value}%")

import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt

day = input("year:month:day ex) 20250521 |")
time = input("time ex)0600 |")

# API 요청 설정
url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
params = {
    'serviceKey': 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A==',
    'pageNo': '1',
    'numOfRows': '1000',
    'dataType': 'XML',
    'base_date': day,
    'base_time': time,
    'nx': '55',
    'ny': '127'
}
# 요청
response = requests.get(url, params=params)
xml_data = response.content
root = ET.fromstring(xml_data)

# 카테고리 한글 매핑
category_map = {
    'PTY': '강수형태',
    'REH': '습도 (%)',
    'RN1': '1시간 강수량',
    'T1H': '기온 (℃)',
    'UUU': '동서 바람성분',
    'VEC': '풍향 (°)',
    'VVV': '남북 바람성분',
    'WSD': '풍속 (m/s)'
}

# 데이터 파싱
items = root.find('.//items')
data = []

for item in items.findall('item'):
    code = item.find('category').text
    entry = {
        '항목': category_map.get(code, code),
        '값': float(item.find('obsrValue').text)
    }
    data.append(entry)


df = pd.DataFrame(data)
print(df)

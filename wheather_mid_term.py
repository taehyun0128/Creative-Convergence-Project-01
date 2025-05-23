import requests
import datetime
import xml.etree.ElementTree as ET

def get_mid_weather(date_str, region_code='11B00000'):
    today = datetime.datetime.now()
    base_time = "0600" if today.hour < 18 else "1800"
    tmFc = today.strftime("%Y%m%d") + base_time

    # 날짜 차이 계산
    target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    delta_days = (target_date - today.date()).days

    if delta_days < 3 or delta_days > 10:
        return "❌ 중기 예보는 오늘로부터 3~10일 뒤까지만 제공됩니다."

    # API 요청 1 - 강수확률 및 날씨 상태
    url_land = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst'
    params_land = {
        'serviceKey': 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A==',
        'pageNo': '1',
        'numOfRows': '10',
        'dataType': 'XML',
        'regId': region_code,
        'tmFc': tmFc
    }

    res_land = requests.get(url_land, params_land)
    root_land = ET.fromstring(res_land.content)
    item_land = root_land.find('.//item')

    # 오전/오후 구분은 delta_days가 3~7일까지만 존재함
    if 3 <= delta_days <= 7:
        wf_am = item_land.findtext(f'wf{delta_days}Am')
        wf_pm = item_land.findtext(f'wf{delta_days}Pm')
        rn_am = item_land.findtext(f'rnSt{delta_days}Am')
        rn_pm = item_land.findtext(f'rnSt{delta_days}Pm')
        weather = f"오전: {wf_am}, 오후: {wf_pm}"
        rain = f"오전: {rn_am}%, 오후: {rn_pm}%"
    else:
        weather = item_land.findtext(f'wf{delta_days}')
        rain = item_land.findtext(f'rnSt{delta_days}') + "%"

    # API 요청 2 - 기온 정보
    url_temp = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'
    params_temp = {
        'serviceKey': 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A==',
        'pageNo': '1',
        'numOfRows': '10',
        'dataType': 'XML',
        'regId': region_code,
        'tmFc': tmFc
    }

    res_temp = requests.get(url_temp, params_temp)
    root_temp = ET.fromstring(res_temp.content)
    item_temp = root_temp.find('.//item')

    min_temp = item_temp.findtext(f'taMin{delta_days}')
    max_temp = item_temp.findtext(f'taMax{delta_days}')

    # 최종 출력
    result = f"""📅 {date_str} 중기 예보:
🔸 날씨 상태: {weather}
🔸 강수 확률: {rain}
🌡️ 최저기온: {min_temp}℃ / 최고기온: {max_temp}℃
"""
    print(weather)
    print(rain)
    print(min_temp,max_temp)
    return result


# 테스트
day = input("날짜를 알려주세요! 예)2025-05-30\t")
print(get_mid_weather(day, region_code="11B00000"))  # 서울/경기/인천

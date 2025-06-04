#여향지지역 : region
#체크인 날짜 : checkin
#체크아웃 날짜 : checkout
#사람 수 : person

#숙소 이름 : accommodation_name[]
#숙소 가격 : accommodation_price[]

from bs4 import BeautifulSoup
import pandas as pd
from urllib.request import Request, urlopen, urlretrieve
from urllib.parse import quote

checkin = "2025-05-15"
checkout = "2025-05-16"
person = "2"

region = quote("강릉")  # UnicodeEncodeError | urlopen은  ASCII로 인코딩 하기에 한글은 인코딩이 안됨 -> 인코딩 시켜줌 
url = f"https://www.yeogi.com/domestic-accommodations?keyword={region}&checkIn={checkin}&checkOut={checkout}&personal={person}&freeForm=false"


# 브라우저처럼 가장하는 헤더 추가 | 웹에서 일반 브라우저처럼 안보이면 봇으로 간주하기에 전근 허용을 못하게함
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

req = Request(url, headers=headers)
page = urlopen(req)

soup = BeautifulSoup(page, "html.parser")
accommodation_name = []
accommodation_price= []
# 숙소 이름,가격 리스스트 저장 및 출력
for i in range(3):
    accommodation_name.append(soup.find_all('h3')[i].get_text())
    print(accommodation_name[i], end="\t\t")
    accommodation_price.append(soup.find_all('div', class_='css-yeouz0')[i].get_text())
    if(accommodation_price[i]):
        print(accommodation_price[i])
    else:
        print("sold out")

# 이미지 저장
image_divs = soup.find_all('div', class_='css-1l3t175')

for idx, div in enumerate(image_divs[:3]):
    img_tag = div.find('img')
    if img_tag and img_tag.has_attr('src'):
        img_url = img_tag['src']
        save_path = f"thumbnail_{idx+1}.jpg"
        urlretrieve(img_url, save_path)
        print(f">>> 이미지 저장 완료: {save_path}")
    else:
        print(f"{idx+1}번 숙소 이미지 없음 또는 src 속성 없음")

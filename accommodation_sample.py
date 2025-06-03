from bs4 import BeautifulSoup
import urllib.request
from urllib.request import Request, urlopen
# 검색 조건 

"""""
checkin = "2025-05-17"
checkout = "2025-05-18"
person = "2"
region = "대구"
"""

def accomdation(region, checkin, checkout, person):
   

    #urlopen이 비 ASCII 문자(예: 한글)을 못 받기에 quote로 encod해서 해야함 
    region_encoded = urllib.parse.quote(region)
    url = f"https://www.yeogi.com/domestic-accommodations?keyword={region_encoded}&checkIn={checkin}&checkOut={checkout}&personal={person}&freeForm=false"


    # 브라우저처럼 가장하는 헤더 추가 | 웹에서 일반 브라우저처럼 안보이면 봇으로 간주하기에 전근 허용을 못하게함
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }

    req = Request(url, headers=headers)
    page = urlopen(req)

    soup = BeautifulSoup(page, "html.parser")
    accommodation_name = []

    # 숙소 정보 수집
    names = [tag.get_text() for tag in soup.find_all('h3')[:3]] #숙소이름 저장
    rent = [tag.get_text() for tag in soup.find_all('div', class_='css-sg6wi7')[:3]] #대실,숙박 정보저장 
    prices = [tag.get_text() for tag in soup.find_all('div', class_='css-yeouz0')[:6]] #
    images = [tag['src'] for tag in soup.find_all('img', alt=True)[:3]] #이미지링크 저장
    
    """"
    print(names, rent, prices)
    print(rent[1][0:2])
    """

    for i in range(len(names)):
        print(names[i], end=("\t\t "))
        if(rent[i][0:2]=="대실"):  # 대실이면 대실 가격을 삭제하고 숙박가격만 출력 
            del prices[i:i+1]
        if(prices[i]):
            print(prices[i])
        else:
            print("sold out")
        img_url = images[i]
        urllib.request.urlretrieve(img_url, f"{region} 숙소{i+1}.jpg")
        print(f">>> 이미지 저장 완료: {region} 숙소{i+1}.jpg \n")
    print(url)

accomdation("수성못", "2025-05-21", "2025-05-22", "2" )

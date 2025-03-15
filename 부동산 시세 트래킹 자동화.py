import requests
import csv
import io
import time
import os
import re

import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("현재 작업 디렉토리:", os.getcwd())

# --- 구글 스프레드 시트 인증 및 접근 ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 서비스 계정 JSON 파일 경로 (실제 경로로 수정)
CREDENTIALS_PATH = "C:/Users/bumiv/Downloads/bradypark-d85853dc0602.json"

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
except Exception as e:
    print(f"서비스 계정 인증 실패: {e}")
    exit(1)

client = gspread.authorize(creds)

# 스프레드 시트 고유 키로 열기
SPREADSHEET_KEY = "1a9uXj4BMcWCey7lNvmDjFouK0OW4DczRatoJM4wLBkE"
try:
    spreadsheet = client.open_by_key(SPREADSHEET_KEY)
except Exception as e:
    print(f"스프레드 시트 열기 실패: {e}")
    exit(1)

# --- Sheet1에서 복합번호(complex no) 읽기 ---
sheet1 = spreadsheet.sheet1
# Sheet1의 C열 값을 읽어오되, 첫 행(헤더)는 제외
complex_numbers = sheet1.col_values(3)[1:]

# --- Sheet2 준비 (결과 기록용) ---
try:
    sheet2 = spreadsheet.worksheet("Sheet2")
except gspread.WorksheetNotFound:
    sheet2 = spreadsheet.add_worksheet(title="Sheet2", rows="100", cols="20")

# --- 네이버 부동산 API 설정 ---
cookies = {
    'NNB': 'LITD5PGRM5YWM',
    'NFS': '2',
    'ASID': 'd376cbfd000001903090fc2d0000004c',
    'tooltipDisplayed': 'true',
    'NV_WETR_LOCATION_RGN_M': '"MDk2ODAxMDE="',
    'SHOW_FIN_BADGE': 'Y',
    '_fwb': '214KbAdyxCP4gfE7pDedQRH.1730544214469',
    'landHomeFlashUseYn': 'Y',
    '_fwb': '214KbAdyxCP4gfE7pDedQRH.1730544214469',
    'wcs_bt': '4f99b5681ce60:1731830669',
    'nstore_session': 'HjCAKkZFYLPM6X7a/0T3a9bB',
    'NV_WETR_LAST_ACCESS_RGN_M': '"MDk2ODAxMDE="',
    'nstore_pagesession': 'iGMTsdqWES7KClsdyO4-038592',
    '_fbp': 'fb.1.1737030925706.180921923182844543',
    'NAC': 'jlJVBcw2dzEk',
    'page_uid': 'i9nIQlqX5E0ssi3MaYCssssssy0-394131',
    'NACT': '1',
    'SRT30': '1742006497',
    'nid_inf': '1916623152',
    'NID_AUT': 'u1wUR/HnpKp1uD2iQ8y4GXGlObw3i+LNJVIr1ePEX8EmdP+kExCMxs5h7onx63u8',
    'NID_JKL': '53vCIypgu97U0FqrV8pH6QwVatbeI3NlFNN9bFlumzc=',
    'NID_SES': 'AAABo99YSKEZZ9DSS09QGnvKqU271zwbnUfv/RtKJ3fXODzjyaacjx/eNE1HcyUDzwVaYZNZ/IUMP2XNj+Iy6nUA3NSd8q+Nbt/8Ycqhn0D/W/sXGuDa8tKG40rU7lITM3r4Ad/Z9hKnto7+IMTPLKBVIihpi1dl5vcw5ZjcN6yAJjVLGLBIjPSbp96OoP61/CC72SFputngI5Xsqw3b74Ss1WFZGQ/W3mGRQnWlkv1q0WcGUyieTrkCp2wUevVz05gcxS3ArXRvzB6f4h5ai1OuAywzuXhG0rMSOBG37CM9nveHh4WqAr9mKH56T7Q96ZLswTdaSflUJEyucH+zYYmClzt2WNFyzrd/bFQEMK34pjwBE4wFUWRL/+ldLRV/oVWcy45aI1kbqZdMruRWgUefefBMi7BK7rJ3zUwPjaaG8qd7pzwJECZSB6gR660HWZJiqE/O10Nx+HvCiPiaPet96gJbcKQanf0Y41kXPXdGaWo+t1d8vGG/XX84RZ+208UTzH9tEV801q5nGP6BiDKOZBV1Fgc1ERP3+tab4svl+klHxREyFoQqxzrWmtv0RVS/qA==',
    'nhn.realestate.article.rlet_type_cd': 'A01',
    'nhn.realestate.article.trade_type_cd': '""',
    'SRT5': '1742008793',
    'BUC': 'EjGzSswEUvaTfhEb8zRutzyM42slonTJcew4gHxumBI=',
    'REALESTATE': 'Sat%20Mar%2015%202025%2012%3A22%3A50%20GMT%2B0900%20(Korean%20Standard%20Time)',
}

headers = {
    'accept': '*/*',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3NDIwMDg5NzAsImV4cCI6MTc0MjAxOTc3MH0.5hGfBlCT1mvllmxRpNpNUOHUEPHX1g47yOTsNa4IVAw',
    'priority': 'u=1, i',
    'referer': 'https://new.land.naver.com/complexes/128528?ms=36.896987,126.639686,17&a=APT:ABYG:JGC:PRE&b=A1:B1&e=RETAIL&ad=true',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

# --- 가격 변환 함수 (숫자형 정수로 변환) ---
def convert_price(price_str):
    price_str = price_str.strip().replace(",", "")
    # 패턴: "숫자 억 [숫자 천]?" 또는 "숫자 억 [숫자]?"
    pattern = r'(\d+)\s*억(?:\s*(\d+)\s*(천)?)?'
    match = re.match(pattern, price_str)
    if match:
        main = int(match.group(1))
        remainder = int(match.group(2)) if match.group(2) else 0
        if match.group(3):  # "천"이 포함된 경우
            return main * 10000 + remainder * 1000
        else:
            return main * 10000 + remainder
    return price_str

# --- API 호출 함수 (페이지 번호 포함) ---
def get_complex_info(complex_no, page=1):
    url = (
        'https://new.land.naver.com/api/articles/complex/{complex_no}'
        '?realEstateType=APT%3AABYG%3AJGC%3APRE'
        '&tradeType=A1%3AB1'
        '&tag=%3A%3A%3A%3A%3A%3A%3A%3A'
        '&rentPriceMin=0&rentPriceMax=900000000'
        '&priceMin=0&priceMax=900000000'
        '&areaMin=0&areaMax=900000000'
        '&oldBuildYears&recentlyBuildYears'
        '&minHouseHoldCount&maxHouseHoldCount'
        '&showArticle=false'
        '&sameAddressGroup=true'
        '&minMaintenanceCost&maxMaintenanceCost'
        '&priceType=RETAIL'
        '&directions='
        '&page={page}'
        '&complexNo={complex_no}'
        '&buildingNos='
        '&areaNos='
        '&type=list'
        '&order=rank'
    ).format(complex_no=complex_no, page=page)
    
    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.status_code}
    except Exception as e:
        return {"error": str(e)}

# --- 각 complex no 별로 전체 페이지의 article 정보를 수집 ---
all_articles = []
for complex_no in complex_numbers:
    if complex_no.strip().isdigit():
        page = 1
        while True:
            data = get_complex_info(complex_no.strip(), page=page)
            if "error" in data:
                print(f"Complex {complex_no} Page {page}: Error {data['error']}")
                break
            articles = data.get("articleList", [])
            for article in articles:
                # 각 article에 복합번호 추가 (숫자형)
                article["complexNo"] = int(complex_no.strip())
                all_articles.append(article)
            if not data.get("isMoreData", False):
                break
            page += 1
            time.sleep(0.5)
    else:
        continue

# --- 데이터 후처리: 가격 필드 및 floorInfo 분리 ---
for article in all_articles:
    # 가격 필드 변환: dealOrWarrantPrc, sameAddrMaxPrc, sameAddrMinPrc
    for key in ["dealOrWarrantPrc", "sameAddrMaxPrc", "sameAddrMinPrc"]:
        if key in article and article[key]:
            try:
                article[key] = convert_price(article[key])
            except Exception:
                article[key] = ""
    # floorInfo 분리: "currentFloor"와 "maxFloor" (정수형)
    if "floorInfo" in article and article["floorInfo"]:
        floor_val = article["floorInfo"].strip()
        if "/" in floor_val:
            parts = floor_val.split("/")
            try:
                article["currentFloor"] = int(parts[0].strip())
            except Exception:
                article["currentFloor"] = parts[0].strip()
            try:
                article["maxFloor"] = int(parts[1].strip())
            except Exception:
                article["maxFloor"] = parts[1].strip()
        else:
            try:
                article["currentFloor"] = int(floor_val)
            except Exception:
                article["currentFloor"] = floor_val
            article["maxFloor"] = ""
        del article["floorInfo"]
    else:
        article["currentFloor"] = ""
        article["maxFloor"] = ""

# --- 원하는 CSV 컬럼 순서 지정 ---
csv_columns = [
    "complexNo",
    "area1",
    "area2",
    "areaName",
    "articleConfirmYmd",
    "articleFeatureDesc",
    "articleName",
    "articleNo",
    "articleRealEstateTypeCode",
    "articleRealEstateTypeName",
    "articleStatus",
    "buildingName",
    "cpMobileArticleLinkUseAtArticleTitleYn",
    "cpMobileArticleLinkUseAtCpNameYn",
    "cpMobileArticleUrl",
    "cpName",
    "cpPcArticleBridgeUrl",
    "cpPcArticleLinkUseAtArticleTitleYn",
    "cpPcArticleLinkUseAtCpNameYn",
    "cpPcArticleUrl",
    "cpid",
    "dealOrWarrantPrc",
    "detailAddress",
    "detailAddressYn",
    "direction",
    "currentFloor",
    "maxFloor",
    "isComplex",
    "isDirectTrade",
    "isInterest",
    "isLocationShow",
    "isPriceModification",
    "isVrExposed",
    "latitude",
    "longitude",
    "priceChangeState",
    "realEstateTypeCode",
    "realEstateTypeName",
    "realtorId",
    "realtorName",
    "representativeImgThumb",
    "representativeImgTypeCode",
    "representativeImgUrl",
    "sameAddrCnt",
    "sameAddrDirectCnt",
    "sameAddrMaxPrc",
    "sameAddrMinPrc",
    "siteImageCount",
    "tagList",
    "tradeCheckedByOwner",
    "tradeTypeCode",
    "tradeTypeName",
    "verificationTypeCode"
]

# 업데이트 시 숫자형으로 기록할 열들
numeric_columns = {"complexNo", "area1", "area2", "dealOrWarrantPrc", "currentFloor", "maxFloor", "sameAddrMaxPrc", "sameAddrMinPrc"}

# --- 2차원 리스트(배열) 생성 ---
data_to_update = []
# 헤더
data_to_update.append(csv_columns)

for article in all_articles:
    row = []
    for col in csv_columns:
        val = article.get(col, "")
        # 만약 값이 리스트라면, 콤마로 join하여 문자열로 변환
        if isinstance(val, list):
            val = ", ".join(val)
        if col in numeric_columns:
            if val == "":
                row.append("")
            else:
                try:
                    row.append(int(val))
                except:
                    try:
                        row.append(float(val))
                    except:
                        row.append(val)
        else:
            row.append(val)
    data_to_update.append(row)

# --- Sheet2 업데이트 ---
sheet2.clear()
sheet2.update(range_name='A1', values=data_to_update)

print("Sheet2에 complex no별 전체 article 정보가 숫자형 가격 및 층 정보로 업데이트되었습니다.")

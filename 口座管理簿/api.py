# api.py
# ----------------------------------------------------------------------------------------------------

from decimal import Decimal # 全体を通して一貫した計算を行うために、10進数をインポートします
from dotenv import load_dotenv # LoaderをImportする
import os
import requests
# ----------------------------------------------------------------------------------------------------

# .env ファイルから環境変数を読み込みます。
load_dotenv()

# load_dotenv() によってロードされた環境変数から API キーを読み取ります。
API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

# if not API_KEY:
#     raise ValueError("API Key Not Found.")

# ベースURLには、このサービスに必要なAPIキーが含まれています。
BASE_URL =  f"https://v6.exchangerate-api.com/v6/{API_KEY}"
REQUEST_TIMEOUT_SECONDS = 10

RATE_CACHE = {} # 取得したレートを保存するためのキャッシュ: {'FROM_TO': Decimal_Rate}。
# ----------------------------------------------------------------------------------------------------

"""
API から最新の為替レート (1 FROM_CURRENCY = X TO_CURRENCY) を取得します。
キャッシュを使用して、繰り返し検索の API 呼び出しを削減します。
"""
def get_exchange_rate(from_currency, to_currency):
    if not API_KEY:
        print("Error: API Key Not Found.")
        return None

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    cache_key = f"{from_currency}_{to_currency}"
    
    if cache_key in RATE_CACHE:
        return RATE_CACHE[cache_key]
    
    # 'from_currency' を基準とした最新のレートをすべて取得するエンドポイント。
    endpoint = f"{BASE_URL}/latest/{from_currency}"
    
    try:
        response = requests.get(endpoint, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status() # 不正な応答（4xx または 5xx）に対して HTTPError を発生させます。
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error Fetching Exchange Rate From API:{e}")
        return None
    
    # 変換率dictionaryを抽出する。
    rates = data.get("conversion_rates")
    
    if not rates or to_currency not in rates:
        # これは、ターゲット通貨コードが無効な場合を処理します。
        print(f"Error:Rate For {to_currency} Not Found.")
        return None
        
    # レートを取得し、安全な計算のために str() でキャストして Decimal に変換します。
    rate = Decimal(str(rates[to_currency]))
    
    RATE_CACHE[cache_key] = rate # レートをキャッシュに保存する。
    return rate
# ----------------------------------------------------------------------------------------------------

"""
直接変換計算には API の「ペア」エンドポイントを使用します。
これは通常、レートを取得してローカルで乗算するよりも信頼性が高くなります。
"""
def convert(amount, from_currency, to_currency):
    if not API_KEY:
        print("Error: API Key Not Found.")
        return None

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    # エンドポイントの形式: /pair/{from_code}/{to_code}/{amount}。
    endpoint = f"{BASE_URL}/pair/{from_currency}/{to_currency}/{amount}"
    
    try:
        response = requests.get(endpoint, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status() # エラーを確認する。
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error Converting Currency:{e}")
        return None
    
    # API応答ステータスを確認する。
    if data.get("result") == "success":
        # 結果の金額をDecimalに変換する。
        return Decimal(str(data.get("conversion_result")))
    
    # API呼び出しは成功したが、変換結果フィールドが欠落していた場合はNoneを返します。
    return None
# ----------------------------------------------------------------------------------------------------
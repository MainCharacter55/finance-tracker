# currency.py
# ----------------------------------------------------------------------------------------------------

from decimal import Decimal # 一貫した計算のためにDecimalをインポート
import api #api.py
# ----------------------------------------------------------------------------------------------------

# 主にapiモジュール内のメソッドを呼び出して通貨換算を調整します。
class Converter:
    # 換算ルート (直接換算またはレート乗算) を決定します。
    def get_converted_amount(self, amount, from_currency, to_currency):
        amount = Decimal(amount) # 入力金額がDecimalであることを確認。

        if from_currency == to_currency:
            return amount # 換算不要。

        # 1. APIエンドポイント経由で直接換算を試みる (より正確/簡単)。
        converted_amount = api.convert(amount, from_currency, to_currency)

        if converted_amount is not None:
            return converted_amount
        else:
            print("⚠️ 手動レート計算にフォールバックしています...")

        # 2. フォールバック: レートを取得して手動で計算。
        rate = api.get_exchange_rate(from_currency, to_currency)

        if rate is not None:
            return amount * rate
        else:
            print(f"❌ {from_currency} から {to_currency} へのレートの取得に失敗しました。送金を完了できません。")
            return None # 重大な失敗。
# ----------------------------------------------------------------------------------------------------
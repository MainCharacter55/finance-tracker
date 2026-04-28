# data.py
# ----------------------------------------------------------------------------------------------------

from decimal import Decimal # 一貫した計算のためにDecimalをインポート
import copy
# ----------------------------------------------------------------------------------------------------

"""
単一の銀行口座を表し、残高、通貨、および履歴を管理します。
高精度の金融計算のためにDecimalを使用します。
"""
class Account:
    def __init__(self, name, balance, currency):
        self.name = name
        # 安全な算術演算のために初期残高をDecimalに変換。
        self.balance = Decimal(balance)
        self.currency = currency
        self.history = [] # トランザクションのリストを格納: [タイプ, 件名, 金額, 通貨]。
# ----------------------------------------------------------------------------------------------------

    # 資金の引き出しを試みます。残高不足の場合はFalseを返します。
    def set_withdraw(self, subject, amount):
        amount = Decimal(amount)
        # 残高不足をチェック。
        if self.balance - amount < 0:
            return False
        self.balance -= amount
        # トランザクションを記録。
        self.history.append(["withdraw", subject, amount, self.currency])
        return True # 出金完了。
# ----------------------------------------------------------------------------------------------------

    # 残高に資金を追加し、トランザクションを記録します。
    def set_deposit(self, subject, amount):
        amount = Decimal(amount) # 'amount'がDecimalであることを確認。
        self.balance += amount
        # トランザクションを記録。
        self.history.append(["deposit", subject, amount, self.currency])
# ----------------------------------------------------------------------------------------------------

    def get_historys(self):
        # 参照渡しを防ぐためにリストのコピーを返します。
        return copy.deepcopy(self.history)
# ----------------------------------------------------------------------------------------------------

    # 現在の残高 (Decimal) を返します。
    def get_balance(self):
        return self.balance
# ----------------------------------------------------------------------------------------------------

    def __repr__(self):
        return f"<Account name='{self.name}', balance={self.balance}, currency='{self.currency}'>"
# ----------------------------------------------------------------------------------------------------
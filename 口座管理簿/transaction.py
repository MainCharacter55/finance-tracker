# transactions.py
# ----------------------------------------------------------------------------------------------------

from abc import ABC, abstractmethod
from decimal import Decimal # 一貫した計算のためにDecimalをインポート
# ----------------------------------------------------------------------------------------------------

# --- 1. 抽象基底クラス (ABC) ---
class Transaction(ABC):
    """すべての金融取引のための抽象基底クラス。"""

    def __init__(self, account_name, amount, currency, subject):
        self.account_name = account_name
        self.amount = Decimal(amount)
        self.currency = currency
        self.subject = subject

    @abstractmethod
    def execute(self, account_manager):
        """実際のトランザクションを実行するために実装する必要があります。"""
        pass
# ----------------------------------------------------------------------------------------------------

# --- 2. 具体的なサブクラス (Transactionを継承) ---
class DepositTransaction(Transaction):
    """単純な入金操作を表します。"""

    def execute(self, account_manager):
        account = account_manager.get_account(self.account_name)
        if account is None:
            return False, f"アカウント '{self.account_name}' が見つかりません。"

        # 実際の操作はAccountオブジェクトの入金メソッドを使用
        account.set_deposit(self.subject, self.amount)
        return True, "入金に成功しました。"
# ----------------------------------------------------------------------------------------------------
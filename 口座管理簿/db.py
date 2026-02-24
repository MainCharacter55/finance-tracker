# db.py
# ----------------------------------------------------------------------------------------------------

from data import Account # data.py
from decimal import Decimal # 一貫した計算のためにDecimalをインポート
import sqlite3
import json
# ----------------------------------------------------------------------------------------------------

class DatabaseManager:
    def __init__(self, db_name='accounts.db'):
        # 1. データベースファイルに接続。
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        # 2. テーブルが存在することを確認。
        self._create_table()

# ----------------------------------------------------------------------------------------------------
    def _create_table(self):
        # 'IF NOT EXISTS' 句を使用。
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                name TEXT PRIMARY KEY,
                balance TEXT,       -- Decimalの精度を保つため文字列として保存
                currency TEXT,
                history TEXT        -- JSON文字列として保存
            )
        ''')

        # SETTINGS テーブルを作成 (基準通貨のようなグローバル値用)。
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        self.conn.commit()

# ----------------------------------------------------------------------------------------------------
    def save_all_accounts(self, accounts_dict, base_currency):
        # 1. 既存のデータをクリアして保存を簡素化 (上書きをシミュレート)。
        self.cursor.execute("DELETE FROM accounts")

        # 2. accounts_dictを反復処理して挿入用のデータを準備。
        for name, account_obj in accounts_dict.items():
            # 複雑なフィールドをシリアル化。
            balance_str = str(account_obj.balance)
            serializable_history = []
            for item in account_obj.history:
                # itemは [タイプ, 件名, 金額 (Decimal), 通貨]。
                transaction_type, subject, amount, currency_code = item

                # Decimal金額をJSONシリアル化のために文字列に変換。
                serializable_history.append([
                    transaction_type,
                    subject,
                    str(amount), # <-- ここが修正箇所。
                    currency_code
                ])
            history_json = json.dumps(serializable_history)

            # SQLインジェクションを防ぐために '?' プレースホルダーを使用。
            self.cursor.execute('''
                INSERT INTO accounts (name, balance, currency, history)
                VALUES (?, ?, ?, ?)
            ''', (name, balance_str, account_obj.currency, history_json))

        # 3. SETTINGS (基準通貨) を保存。
        self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                            ('base_currency', base_currency))

        self.conn.commit()

# ----------------------------------------------------------------------------------------------------
    def load_all_data(self):
        accounts = {}
        # 1. 全ての行をフェッチ。
        self.cursor.execute("SELECT name, balance, currency, history FROM accounts")
        rows = self.cursor.fetchall()

        # 2. データをデシリアル化し、Accountオブジェクトを再作成。
        for name, balance_str, currency_code, history_json in rows:
            history_list_str = json.loads(history_json)

            history_list_decimal = []
            for item in history_list_str:
                transaction_type, subject, amount_str, currency_code_hist = item
                history_list_decimal.append([
                    transaction_type,
                    subject,
                    Decimal(amount_str), # ここでDecimalに戻す。
                    currency_code_hist
                ])

            account = Account(name, balance_str, currency_code)
            account.history = history_list_decimal

            accounts[name] = account

          # SETTINGS (基準通貨) をロード。 ---
        base_currency = "JPY" # 設定が見つからない場合のデフォルト値。
        self.cursor.execute("SELECT value FROM settings WHERE key = 'base_currency'")
        setting_row = self.cursor.fetchone()

        if setting_row:
            base_currency = setting_row[0] # 行からの最初の (そして唯一の) カラム。

        # ロードされたすべてのデータを単一の辞書として返す。
        return {
            'accounts': accounts,
            'base_currency': base_currency
        }
# ----------------------------------------------------------------------------------------------------

    # データベースから特定のアカウント レコードを削除します。
    def delete_account_record(self, name):
        try:
            self.cursor.execute("DELETE FROM accounts WHERE name = ?", (name,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error during deletion: {e}")
            return False
# ----------------------------------------------------------------------------------------------------
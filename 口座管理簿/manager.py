# manager.py
# ----------------------------------------------------------------------------------------------------

from data import Account #data.py
from db import DatabaseManager #db.py
# ----------------------------------------------------------------------------------------------------

"""
Accountオブジェクトのコレクションを管理します。
メインアプリケーションロジックとアカウントデータの間のインターフェースとして機能します。
"""
class AccountManager:
    def __init__(self):
        self.accounts = {} # Accountオブジェクトを格納する辞書: {名前: Account_Object}。
        self.db_manager = DatabaseManager()

        # アカウントと基準通貨をロード。
        loaded_data = self.db_manager.load_all_data()
        # 'accounts'キーはAccountオブジェクトの辞書を保持。
        self.accounts = loaded_data.get('accounts', {})
        # 基準通貨をロードし、デフォルトを "JPY" に設定。
        self.base_currency = loaded_data.get('base_currency', "JPY")

# ----------------------------------------------------------------------------------------------------
    # このメソッドは、ユーザーが '0. 終了' を選択したときに main.py から呼び出されます。
    def save_data(self):
        # このメソッドは、ユーザーが '0. 終了' を選択したときに main.py から呼び出されます。
        self.db_manager.save_all_accounts(self.accounts, self.base_currency)
# ----------------------------------------------------------------------------------------------------

    # オブジェクトが破棄されるときに接続を閉じます。
    def __del__(self):
        if hasattr(self, 'db_manager') and self.db_manager.conn:
            # db_managerが既にクローズしているかチェックはしませんが、connが存在すれば閉じます。
            self.db_manager.conn.close()
# ----------------------------------------------------------------------------------------------------

    # 新しいAccountオブジェクトを作成し、マネージャーに追加します。
    def add_account(self, name, initial_balance, currency):
        if name in self.accounts:
            return False # アカウントはすでに存在します。
        # 修正された変数名 'initial_balance' を使用。
        self.accounts[name] = Account(name, initial_balance, currency)
        return True
# ----------------------------------------------------------------------------------------------------

    # 名前でAccountオブジェクトを取得します。見つからない場合はNoneを返します。
    def get_account(self, name):
        return self.accounts.get(name)
# ----------------------------------------------------------------------------------------------------

    # 名前で指定したアカウントオブジェクトを削除します。成功した場合はTrueを返します。
    def delete_account(self, name):
        if name in self.accounts:
            # 1. データベースから削除。
            if self.db_manager.delete_account_record(name):
                # 2. メモリ内辞書から削除。
                del self.accounts[name]
                # 3. 削除を永続化するために、状態全体をすぐに保存します。
                self.save_data()
                return True
            else:
                # データベースの削除に失敗しました。
                return False
        return False # アカウントが見つかりません。
# ----------------------------------------------------------------------------------------------------
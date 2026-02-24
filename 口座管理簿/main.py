# main.py
# ----------------------------------------------------------------------------------------------------

import os
import matplotlib
matplotlib.use('Agg') # Replit/Linux環境でグラフを表示するための設定 (GUIがない環境用)
import matplotlib.pyplot as plt # グラフ表示用
from matplotlib import font_manager
from data import Account #data.py
from db import DatabaseManager #db.py
from manager import AccountManager #manager.py
from transaction import DepositTransaction #transaction.py
from decimal import Decimal # 一貫した計算のためにDecimalをインポート
import api #api.py
import currency #currency.py
# ----------------------------------------------------------------------------------------------------

# 日本語表示のためのフォント設定 (Replit/Linux対応)
# 1. 'font.ttf' をプロジェクトのルートディレクトリにアップロードしてください。
FONT_PATH = './font.ttf'

if os.path.exists(FONT_PATH):
    # カスタムフォントを登録
    font_manager.fontManager.addfont(FONT_PATH)
    prop = font_manager.FontProperties(fname=FONT_PATH)
    plt.rcParams['font.family'] = prop.get_name()
    # マイナス記号の文字化け防止
    plt.rcParams['axes.unicode_minus'] = False 
    print(f"✅ フォント '{prop.get_name()}' を適用しました。")
else:
    # ローカル(Windows)実行用のフォールバック
    plt.rcParams['font.family'] = 'Meiryo'
    print("⚠️ 警告: font.ttf が見つかりません。デフォルト設定を使用します。")
    pass
# ----------------------------------------------------------------------------------------------------

def main():
    manager = AccountManager()
    current_account = None # 現在表示・使用中のアカウントを追跡。

    if manager.accounts:
        # DBからデータがロードされた: 最初に見つかったアカウントを現在のアカウントに設定。
        current_account = list(manager.accounts.keys())[0]
        print(f"✅ {len(manager.accounts)}件のアカウントをロードしました。基準通貨: {manager.base_currency}")
    else:
        # DBにデータが見つからなかった: 初期設定のプロンプトに進む。
        print("💡 初期セットアップを開始します (データが見つかりませんでした)。")
        # 基準通貨の初期設定。
        manager.base_currency = input("基準通貨を設定してください (例: JPY/USD/...):").upper()

        # --- 初期アカウント設定。 ---
        try:
            # 1つ目のアカウントの詳細を取得。
            account_name = (input("アカウント名 (例: SMBC/Mizuho/...):"))
            initial_balance = (input("初期残高:"))
            account_currency = input("アカウントの通貨:").upper()
            # アカウントを追加し、現在のアカウントとして設定。
            if manager.add_account(account_name, initial_balance, account_currency):
                current_account = account_name
                manager.save_data()
            else:
                print("❌ 初期アカウントの追加中にエラーが発生しました。")
                return
        except Exception as e:
            # 初期入力/設定中の例外をキャッチ。
            print(f"❌ セットアップ中の無効な初期残高です。終了します。")
            return

    # メインループ開始前にcurrent_accountが存在することを確認。
    if current_account is None:
        print("⚠️ 致命的なエラー: アカウントのロードまたは作成に失敗しました。終了します。")
        return
# ----------------------------------------------------------------------------------------------------

    # メインループ
    while True:
        # 表示情報のために常に現在のアカウントオブジェクトを取得。
        account_for_display = manager.get_account(current_account)
        print(f'''
              現在のアカウント:{current_account} ({account_for_display.currency}) - 残高: {account_for_display.get_balance()} {account_for_display.currency}
              1. ダッシュボード          2. 送金
              3. 入金                   4. 出金
              5. 口座詳細               6. アカウント切替
              7. アカウント追加          8. アカウントを削除
              0. 終了''')
        choice = (input("\n上記のアクションから 0-8 を選択してください:"))
        print("---------------------------------------------------")
# ----------------------------------------------------------------------------------------------------

        if choice == "1":
            print("💰 ダッシュボード")

            while True:
                # 基準通貨の変更プロンプト。
                print(f"現在の基準通貨: {manager.base_currency}")
                change_currency = input("基準通貨を変更するには新しい通貨を入力してください (または 'Enter' で続行):").upper()
                # 新しい通貨が入力されたかチェック。
                if change_currency == "":
                    break
                if len(change_currency) != 3 or not change_currency.isalpha():
                    print(f"❌ エラー: '{change_currency}' は有効な通貨ではありません。")
                    continue # whileループの最初に戻る。
                manager.base_currency = change_currency
                print(f"✅ 基準通貨を {manager.base_currency} に更新しました。")
                break

            # 合計を0に設定。
            total_value = Decimal(0)
            base = manager.base_currency
            converter = currency.Converter()
            print(f"集計基準通貨: {base}")
            # print("-" * 30)

            for name, account_obj in manager.accounts.items():
                balance = account_obj.get_balance()
                source_curr = account_obj.currency
                converted_balance = balance

                try:
                    if source_curr != base:
                        # Converterを使用して基準通貨での値を取得。
                        converted_balance = converter.get_converted_amount(balance, source_curr, base)
                        if converted_balance is None:
                            print(f"⚠️ {name} ({source_curr}) の換算に失敗しました。スキップします。")
                            continue # APIが失敗した場合はこのアカウントをスキップ。
                        # 小数点以下2桁に丸めて表示。
                        print(f"{name:<10}: {balance:<10} {source_curr} -> {converted_balance.quantize(Decimal('.01'))} {base}")
                    else:
                        print(f"{name:<10}: {balance:<10} {source_curr}")
                    total_value += converted_balance
                except Exception as e:
                    print(f"❌ アカウント {name} の処理中に重大なエラーが発生しました: {e}。スキップします。")
                    continue

            # print("-" * 30)
            # 合計値を表示 (小数点以下2桁に丸める)。
            print(f"✅ 合計資産価値: {total_value.quantize(Decimal('.01'))} {base}")
# ----------------------------------------------------------------------------------------------------

        elif choice == "2":
            print("💸 送金")

            try:
                # 0. 全てのアカウントリストを取得。
                available_accounts = list(manager.accounts.keys())
                # 現在のアカウントを除外。
                switch_options = [name for name in available_accounts if name != current_account]
                if not switch_options:
                    # 現在のアカウントのみ、またはアカウントがない場合。
                    print("⚠️ 送金先として利用可能なアカウントがありません。")
                    continue
                print("利用可能なアカウント:")
                # フィルタリングされたリストのみを反復処理。
                for i, name in enumerate(switch_options):
                    account_obj = manager.get_account(name)
                    print(f"{i+1}. {name} ({account_obj.currency}) - 残高: {account_obj.get_balance()} {account_obj.currency}")

                # 1. アカウントを設定し、有効性をチェック。
                source_account = manager.get_account(current_account)
                destination_name = input("送金先の口座名を入力してください (または 'C' でキャンセル):")
                if destination_name.upper() == 'C':
                    print("送金をキャンセルしました。")
                    continue
                destination_account = manager.get_account(destination_name)

                if destination_account is None:
                    print(f"❌ エラー: アカウント '{destination_name}' が見つかりません。")
                    continue

                # 2. 金額を取得。
                amount_str = input(f"送金する金額 ({source_account.currency}建て):")
                transfer_amount = Decimal(amount_str) # 計算のためにDecimalに変換。
                source_currency = source_account.currency
                destination_currency = destination_account.currency

                # 3. 通貨換算の処理。
                converted_amount = transfer_amount
                if source_currency != destination_currency:
                    converter = currency.Converter()
                    # コンバーターを呼び出して最終的な金額を取得。
                    converted_amount = converter.get_converted_amount(transfer_amount, source_currency, destination_currency)
                    if converted_amount is None:
                        print("❌ エラー: 通貨換算に失敗しました。送金をキャンセルしました。")
                        continue # 換算失敗、出金前に送金を中止。

                # 4. 送金元からの出金を試みる (換算確認後)。
                # 送金額は常に送金元の通貨建て。
                if not source_account.set_withdraw(f"'{destination_name}' ({destination_currency}) への送金", transfer_amount):
                    print("❌ エラー: 残高不足です。送金をキャンセルしました。")
                    continue

                # 5. 送金先への入金を実行。
                # 入金額は、送金先の通貨建ての換算済み金額。
                destination_account.set_deposit(f"'{current_account}' ({source_currency}) からの送金", converted_amount)

                # 6. 成功の出力。
                print(f"✅ 送金成功! {transfer_amount} {source_currency} を送金しました。")
                print(f"送金先は {converted_amount.quantize(Decimal('.01'))} {destination_currency} を受け取りました。")

            except Exception as e:
                # 無効な金額入力 (Decimalに変換できないなど) の例外をキャッチ。
                print(f"❌ 送金中にエラーが発生しました: 入力を確認してください。")
                # print(f"詳細エラー: {e}") # デバッグ用。
# ----------------------------------------------------------------------------------------------------

        elif choice == "3":
            print("📥 入金")
            try:
                subject = input("件名:")
                amount = input("金額:") # 文字列として読み込み、Decimalへの変換はdata.pyで処理。
                account_obj = manager.get_account(current_account)
                deposit = DepositTransaction(current_account, amount, account_obj.currency, subject)
                success, message = deposit.execute(manager) # managerはAccountManagerのインスタンス。
                print(message)
                print("✅ 入金完了。")
            except Exception:
                print("❌ 無効な金額です。数値を入力してください。")
# ----------------------------------------------------------------------------------------------------

        elif choice == "4":
            print("📤 出金")
            try:
                subject = input("件名:")
                amount = input("金額:") # 文字列として読み込み、Decimalへの変換はdata.pyで処理。
                account_obj = manager.get_account(current_account)
                # set_withdrawは利用可能な資金に基づいてTrue/Falseを返す。
                if account_obj.set_withdraw(subject, amount):
                    print("✅ 出金完了。")
                else:
                    print("❌ 残高不足です。出金に失敗しました。")
            except Exception:
                print("❌ 無効な金額です。数値を入力してください。")
# ----------------------------------------------------------------------------------------------------

        elif choice == "5":
            print("📄 口座詳細")
            account_obj = manager.get_account(current_account)
            print(f"現在の残高:{account_obj.get_balance()}{account_obj.currency}")
            history = account_obj.get_historys()
            if not history:
                print("履歴が見つかりません。")
            else:
                print("--- 履歴 ---")

                # 1. 履歴リスト内の全トランザクションより前の開始残高を計算。
                # これは、現在の残高から全トランザクションの純額を引くことで行われる。
                current_total_balance = account_obj.get_balance()
                net_transaction_sum = sum(
                    amount if type == "deposit" else -amount
                    for type, _, amount, _ in history
                )
                initial_balance = current_total_balance - net_transaction_sum
                # プロットデータ配列を初期化。計算された初期残高で開始。。
                running_balance = initial_balance
                balances = [running_balance] # 最初のポイントを実際の初期残高に設定。
                transaction_labels = ["初期残高"]
                running_balance = initial_balance

                # enumerateの結果を'i' (インデックス) と 'record' (履歴項目) にアンパック。
                for i, record in enumerate(history):
                    # 次に、'record' (4要素のリスト/タプル) をアンパック。
                    transaction_type, subject, amount, curr = record

                    # 新しい残高を計算。
                    if transaction_type == "deposit":
                        running_balance += amount
                    elif transaction_type == "withdraw":
                        running_balance -= amount

                    balances.append(running_balance)

                    # X軸用の説明的なラベルを作成。
                    label = f"{i+1}: {transaction_type.capitalize()} ({subject})"
                    transaction_labels.append(label)

                    # 文字列フォーマットを使用して位置合わせ (: <15は左揃え15文字幅)。
                    print(f"{transaction_type:<10} | 件名:{subject:<15} | 金額:{amount} {curr}")

                # Matplotlib用にDecimal残高をfloatに変換。
                plot_balances = [float(b) for b in balances]

                plt.figure(figsize=(10, 6)) # グラフサイズを設定。
                plt.plot(transaction_labels, plot_balances, marker='o', linestyle='-', color='skyblue')

                plt.title(f'{current_account} ({account_obj.currency}) の残高履歴')
                plt.xlabel('トランザクション番号と件名')
                plt.ylabel(f'残高 ({account_obj.currency})')

                # X軸ラベルを回転させて、トランザクションが多い場合に見やすくする。
                plt.xticks(rotation=45, ha='right')
                plt.grid(True)
                plt.tight_layout() # ラベルが切れないようにレイアウトを調整。

                # plt.show() # グラフを表示。
                plt.savefig('balance_graph.png')
                print("📊 グラフを 'balance_graph.png' として保存しました。")
                plt.close() # Important to clear memory
# ----------------------------------------------------------------------------------------------------

        elif choice == "6":
            print("🔄 アカウント切替")

            # 全てのアカウントリストを取得。
            available_accounts = list(manager.accounts.keys())
            # 現在のアカウントを除外。
            switch_options = [name for name in available_accounts if name != current_account]
            if not switch_options:
                # 現在のアカウントのみ、またはアカウントがない場合。
                print("⚠️ 切り替えるアカウントがありません。")
                continue
            print("利用可能なアカウント:")
            # フィルタリングされたリストのみを反復処理。
            for i, name in enumerate(switch_options):
                account_obj = manager.get_account(name)
                print(f"{i+1}. {name} ({account_obj.currency}) - 残高: {account_obj.get_balance()} {account_obj.currency}")

            new_account_name = input("切り替えるアカウント名を入力してください (または 'C' でキャンセル):")
            if new_account_name.upper() == 'C':
                print("アカウント切替をキャンセルしました。")
                continue

            # 名前が有効であれば current_account 変数を変更。
            if new_account_name in manager.accounts:
                # global current_account # 'current_account'がmainで初期化されていない場合にのみ必要。
                current_account = new_account_name
                print(f"✅ アカウントを {current_account} に切り替えました。")
            else:
                print(f"❌ エラー。アカウント '{new_account_name}' が見つかりません。")
# ----------------------------------------------------------------------------------------------------

        elif choice == "7":
            print("➕ アカウント追加")
            name = input("新しいアカウント名を入力してください (または 'C' でキャンセル):")
            if name.upper() == 'C':
                print("アカウント追加をキャンセルしました。")
                continue
            try:
                balance = input("初期残高:")
                currency_code = input("通貨:").upper()
                if manager.add_account(name, balance, currency_code):
                    print(f"✅ アカウント '{name}' を作成しました。")
                else:
                    print("❌ アカウントはすでに存在します。")
            except Exception:
                print("❌ 無効な金額です。数値を入力してください。")
# ----------------------------------------------------------------------------------------------------

        elif choice == "8":
            print("アカウントを削除")
            
            # 1. 確認を求める。
            conformation = input(f"現在のアカウント'{current_account}'を削除しますか? ('C'で確定):").upper()
            if conformation != "C":
                print("アカウント削除が中止されました。")
                continue
            
            # 2. これが残っている唯一のアカウントであるかどうかを確認します。
            if len(manager.accounts) <= 1:
                print("削除失敗しました: 最後のアカウントを削除することができません。")
                print("別のアカウント作ってからやりなおして下さい。")
                continue
            
            # 3. 削除するにはmanagerを呼び出す。
            if manager.delete_account(current_account):
                print(f"アカウント'{current_account}'が削除されました。")
                
                # 4. 重要: 新しい当座預金口座に切り替える。
                # 残りのアカウントキーを取得し、最初のものを現在のものに設定する。
                remaining_accounts = list(manager.accounts.keys())
                if remaining_accounts:
                    current_account = remaining_accounts[0]
                    print(f"現在のアカウント{current_account}に切替されました。")
                else:
                    print("アカウントがありません。プログラム終了します。")
                    break
            else:
                # このケースはステップ2で防ぐべきであるが、安全なフォールバックである。
                print(f"エラーr: このアカウント'{current_account}'の削除はできませんでした。")
# ----------------------------------------------------------------------------------------------------

        elif choice == "0":
            print("💾 データを保存しています。")
            manager.save_data() # <-- データベース保存呼び出しを追加。
            print("👋 終了します。")
            break
# ----------------------------------------------------------------------------------------------------

        else:
            print("❌ 無効な入力です。0-7 を選択してください。")
# ----------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------
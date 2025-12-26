import streamlit as st


def render_header() -> None:
    col_header1, col_header2, col_header3, col_header4 = st.columns([2, 1, 1, 1])
    with col_header1:
        st.title("データ前処理ツール")
    with col_header2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ホーム", use_container_width=True, help="メインページに戻る"):
            if 'show_help' in st.session_state:
                del st.session_state['show_help']
            if 'show_full_history' in st.session_state:
                del st.session_state['show_full_history']
            st.rerun()
    with col_header3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("リセット", use_container_width=True, help="すべての設定とデータをリセット"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col_header4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ヘルプ", use_container_width=True, help="使い方ガイドを表示"):
            st.session_state['show_help'] = True


def render_recent_history() -> None:
    if len(st.session_state.get('processing_history', [])) == 0:
        return

    st.markdown("---")
    col_hist1, col_hist2 = st.columns([3, 1])
    with col_hist1:
        st.markdown("### 最近の処理")
    with col_hist2:
        if st.button("全履歴", use_container_width=True):
            st.session_state['show_full_history'] = True
            st.rerun()

    recent_history = st.session_state['processing_history'][-3:][::-1]

    hist_cols = st.columns(min(len(recent_history), 3))
    for idx, entry in enumerate(recent_history):
        with hist_cols[idx]:
            changes_summary = []
            if 'rows_removed' in entry.get('changes', {}):
                changes_summary.append(f"行-{entry['changes']['rows_removed']}")
            if 'rows_changed' in entry.get('changes', {}):
                change = entry['changes']['rows_changed']
                if change != 0:
                    changes_summary.append(f"行{change:+d}")
            if 'columns_added' in entry.get('changes', {}):
                changes_summary.append(f"列+{entry['changes']['columns_added']}")
            if 'columns_changed' in entry.get('changes', {}):
                change = entry['changes']['columns_changed']
                if change != 0:
                    changes_summary.append(f"列{change:+d}")

            changes_str = " | ".join(changes_summary) if changes_summary else "変更なし"

            before_info = []
            after_info = []
            if 'rows' in entry.get('before', {}):
                before_info.append(f"{entry['before']['rows']}行")
            if 'columns' in entry.get('before', {}):
                before_info.append(f"{entry['before']['columns']}列")
            if 'rows' in entry.get('after', {}):
                after_info.append(f"{entry['after']['rows']}行")
            if 'columns' in entry.get('after', {}):
                after_info.append(f"{entry['after']['columns']}列")

            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4; margin-bottom: 0.5rem;">
                <strong>{entry['operation']}</strong><br>
                <small style="color: #6c757d;">{entry['timestamp']}</small><br>
                <span style="font-size: 0.9em;">{', '.join(before_info)} → {', '.join(after_info)}</span><br>
                <span style="font-size: 0.85em; color: #28a745;">{changes_str}</span>
            </div>
            """, unsafe_allow_html=True)


def render_help() -> None:
    if 'show_help' not in st.session_state:
        return

    st.markdown("---")
    with st.container():
        st.markdown("### ヘルプとガイド")

        help_tabs = st.tabs(["使い方ガイド", "前処理のフロー", "よくある質問", "機能一覧", "使用例とサンプルデータ"])

        with help_tabs[0]:
            st.info("👈 左側のサイドバーからデータファイルをアップロードしてください")

            st.markdown("""
            ### 基本的な使い方

            1. **ファイルをアップロード**（サイドバー）
            2. **「データ」タブ**で中身を確認・必要なら編集
            3. **「前処理」タブ**で設定を確認し、「前処理を実行」をクリック
            4. 必要に応じて **「可視化」・「統計検定」・「高度な機能」** タブを利用
            5. 「データ」タブや各機能内のダウンロードボタンから処理済みデータを保存
            """)

        with help_tabs[1]:
            st.markdown("""
            ### 標準的な前処理の流れ（概要）

            1. データの読み込み・確認
            2. データの理解（分布・欠損・外れ値の把握）
            3. 重複・明らかな誤り（異常値）の除去
            4. 外れ値の検出・処理
            5. 欠損値の処理
            6. カテゴリ変数のエンコーディング
            7. 特徴量スケーリング
            8. （必要に応じて）特徴量エンジニアリング・特徴量選択
            9. 処理済みデータのダウンロード
            """)

        with help_tabs[2]:
            st.markdown("""
            ### よくある質問

            **Q: どの前処理設定を選べばいいですか？**
            A: 初心者の方は「自動」設定を推奨します。詳細は各設定のヘルプテキストを参照してください。

            **Q: エラーが発生しました**
            A: エラーメッセージを確認し、データの形式や設定を見直してください。よくある原因：
            - データに文字列が含まれている数値列がある
            - 欠損値が多すぎる
            - メモリ不足（データが大きすぎる）

            **Q: 処理が完了しましたが、結果がおかしいです**
            A: 「履歴」タブで実行した処理を確認し、必要に応じて設定を変更して再実行してください。

            **Q: データを元に戻したい**
            A: 「リセット」ボタンをクリックするか、「データ」タブで「元のデータに戻す」をクリックしてください。

            **Q: 高度な分析の結果はどこで確認できますか？**
            A: 各機能の実行後、結果がその場に表示されます。処理済みデータは「データ」タブの「処理済みデータのダウンロード」セクションからダウンロードできます。

            **Q: 生成された図をダウンロードできますか？**
            A: はい。「可視化」タブで生成された図にはダウンロードボタンが表示されます。
            """)

        with help_tabs[3]:
            st.markdown("""
            ### 機能一覧

            #### データタブ
            - データの確認と編集
            - 列・行の削除、編集、並べ替え
            - データのリセット
            - 処理済みデータのダウンロード

            #### 分析タブ
            - 数値変数とカテゴリ変数の識別
            - 基本統計量の表示
            - 変数ごとの詳細分析

            #### 前処理タブ
            - 欠損値処理
            - 外れ値処理
            - カテゴリ変数エンコーディング
            - 特徴量スケーリング
            - 特徴量選択
            - 処理済みデータのダウンロード

            #### 可視化タブ
            - データ分布の可視化（ヒストグラム、箱ひげ図、密度プロット）
            - 相関行列の可視化
            - 欠損値の可視化
            - 散布図マトリックス
            - グラフのカスタマイズ
            - 図のダウンロード

            #### 統計検定タブ
            - 正規性検定
            - 等分散性検定
            - 独立性検定
            - VIF分析
            - 条件数計算

            #### 高度な機能タブ
            - 重複削除
            - 特徴量エンジニアリング
            - VIF分析
            - クラス不均衡処理
            - データ分割
            - 高度な診断
            - 特徴量選択（高度）
            - 次元削減

            #### 履歴タブ
            - 実行した処理の履歴を確認
            - 処理の詳細を表示
            """)

        with help_tabs[4]:
            st.markdown("""
            ### 使用例とサンプルデータ

            #### サンプルデータの作成方法

            以下のような形式のCSVファイルを準備してください：

            ```csv
            年齢,収入,都市,教育,性別,経験年数,ターゲット
            25,50000,東京,学士,1,3,1
            30,60000,大阪,修士,0,5,0
            35,70000,名古屋,博士,1,8,1
            ...
            ```

            #### 基本的な使用例

            1. **データのアップロード**
               - サイドバーからCSV、Excel、JSONファイルをアップロード
               - 日本語ファイルの場合は、エンコーディングを選択（通常は「自動検出」でOK）

            2. **データの確認**
               - 「データ」タブでデータの内容を確認
               - 欠損値や外れ値がないか確認

            3. **前処理の実行**
               - サイドバーで前処理設定を確認（初心者の方はデフォルト設定のまま）
               - 「前処理」タブで「前処理を実行」をクリック
               - 処理結果を確認

            4. **データのダウンロード**
               - 「データ」タブの「処理済みデータのダウンロード」セクションからダウンロード
               - または、各機能内のダウンロードボタンからダウンロード

            #### 推奨される前処理の流れ

            1. **欠損値処理**: まずは "auto" を試してみてください
            2. **外れ値除去**: データに外れ値が多そうな場合は有効化
            3. **カテゴリ変数エンコーディング**: "auto" で自動選択
            4. **特徴量スケーリング**: 機械学習を使用する場合は "standard" を推奨
            5. **特徴量選択**: 変数が多い場合に有効化

            #### よくある使用パターン

            **パターン1: 初心者向け（デフォルト設定）**
            - 欠損値処理: auto
            - 外れ値処理: 無効
            - カテゴリ変数エンコーディング: auto
            - 特徴量スケーリング: なし
            - 「前処理を実行」をクリック

            **パターン2: 機械学習用データの準備**
            - 欠損値処理: auto または fill (mean)
            - 外れ値処理: 有効（IQR法）
            - カテゴリ変数エンコーディング: auto
            - 特徴量スケーリング: standard
            - 「前処理を実行」をクリック

            **パターン3: 統計分析用データの準備**
            - 欠損値処理: auto または drop
            - 外れ値処理: 有効（Z-score法）
            - カテゴリ変数エンコーディング: label または onehot
            - 特徴量スケーリング: なし（統計分析では通常不要）
            - 「前処理を実行」をクリック
            """)

        if st.button("ヘルプを閉じる", key="close_help"):
            del st.session_state['show_help']
            st.rerun()

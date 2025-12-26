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
        st.markdown("
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
            <div style="background:
                <strong>{entry['operation']}</strong><br>
                <small style="color:
                <span style="font-size: 0.9em;">{', '.join(before_info)} → {', '.join(after_info)}</span><br>
                <span style="font-size: 0.85em; color:
            </div>

        with help_tabs[1]:
            st.markdown("""

            1. データの読み込み・確認
            2. データの理解（分布・欠損・外れ値の把握）
            3. 重複・明らかな誤り（異常値）の除去
            4. 外れ値の検出・処理
            5. 欠損値の処理
            6. カテゴリ変数のエンコーディング
            7. 特徴量スケーリング
            8. （必要に応じて）特徴量エンジニアリング・特徴量選択
            9. 処理済みデータのダウンロード

        with help_tabs[3]:
            st.markdown("""

            - データの確認と編集
            - 列・行の削除、編集、並べ替え
            - データのリセット
            - 処理済みデータのダウンロード

            - 数値変数とカテゴリ変数の識別
            - 基本統計量の表示
            - 変数ごとの詳細分析

            - 欠損値処理
            - 外れ値処理
            - カテゴリ変数エンコーディング
            - 特徴量スケーリング
            - 特徴量選択
            - 処理済みデータのダウンロード

            - データ分布の可視化（ヒストグラム、箱ひげ図、密度プロット）
            - 相関行列の可視化
            - 欠損値の可視化
            - 散布図マトリックス
            - グラフのカスタマイズ
            - 図のダウンロード

            - 正規性検定
            - 等分散性検定
            - 独立性検定
            - VIF分析
            - 条件数計算

            - 重複削除
            - 特徴量エンジニアリング
            - VIF分析
            - クラス不均衡処理
            - データ分割
            - 高度な診断
            - 特徴量選択（高度）
            - 次元削減

            - 実行した処理の履歴を確認
            - 処理の詳細を表示

        if st.button("ヘルプを閉じる", key="close_help"):
            del st.session_state['show_help']
            st.rerun()

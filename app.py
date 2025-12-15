"""
データ前処理プログラム - Streamlit Web UI
文系学生にも簡単に使えるWebインターフェース

License: MIT License
Copyright (c) 2024
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
from data_preprocessor import DataPreprocessor
import base64

# ページ設定
st.set_page_config(
    page_title="データ前処理ツール",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,  # ヘルプメニューを非表示
        'Report a bug': None,  # バグ報告を非表示
        'About': None  # Aboutを非表示（GitHubリンクが含まれる可能性があるため）
    }
)

# カスタムCSS（日本語フォント対応・エレガントなデザイン・GitHubリンク非表示）
st.markdown("""
<style>
    .main {
        font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    h1 {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    h2 {
        color: #2c3e50;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 0.3rem;
        margin-top: 1.5rem;
    }
    h3 {
        color: #34495e;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem 0.5rem 0 0;
        padding: 0.75rem 1.5rem;
    }
    /* GitHubリンクを非表示 */
    a[href*="github.com"] {
        display: none !important;
    }
    /* Streamlit Cloudのフッターリンクを非表示 */
    footer[data-testid="stFooter"] a[href*="github"] {
        display: none !important;
    }
    /* メニュー内のGitHubリンクを非表示 */
    [data-testid="stHeader"] a[href*="github"],
    [data-testid="stHeader"] button[aria-label*="github"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # uploaded_fileを初期化（サイドバーで定義される前に使用される可能性があるため）
    uploaded_file = None
    
    # ヘッダー
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header1:
        st.title("データ前処理ツール")
    with col_header2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("リセット", use_container_width=True, help="すべての設定とデータをリセット"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col_header3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ヘルプ", use_container_width=True, help="使い方ガイドを表示"):
            st.session_state['show_help'] = True
    
    # 処理履歴を初期化（セッション状態に保存）
    if 'processing_history' not in st.session_state:
        st.session_state['processing_history'] = []
    
    # 処理履歴をコンパクトに表示（常に表示・より目立つデザイン）
    if len(st.session_state.get('processing_history', [])) > 0:
        st.markdown("---")
        col_hist1, col_hist2 = st.columns([3, 1])
        with col_hist1:
            st.markdown("### 最近の処理")
        with col_hist2:
            if st.button("全履歴", use_container_width=True):
                st.session_state['show_full_history'] = True
                st.rerun()
        
        # 最新3件をカード形式で表示
        recent_history = st.session_state['processing_history'][-3:][::-1]  # 最新3件、新しい順
        
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
    
    st.markdown("---")
    
    # ワークフローガイド（ファイル未アップロード時のみ表示）
    if uploaded_file is None:
        st.info("""
        👋 **はじめに**: サイドバーからデータファイルをアップロードしてください。
        
        **基本的な使い方**:
        1. ファイルをアップロード → 2. データを確認・編集 → 3. 前処理設定 → 4. 実行 → 5. ダウンロード
        """)
        
        with st.expander("詳細な使い方ガイド", expanded=False):
            st.markdown("""
            ### このツールについて
            機械学習や統計分析のためのデータ前処理を簡単に行うためのWebアプリケーションです。
            プログラミングの知識がなくても、直感的な操作でデータの前処理ができます。
            
            ### ステップバイステップガイド
            
            #### ステップ1: データのアップロード
            - サイドバーからCSV、Excel、JSONファイルをアップロード
            - 日本語ファイルの場合は、エンコーディングを選択（通常は「自動検出」でOK）
            
            #### ステップ2: データの確認と編集（データタブ）
            - データの内容を確認
            - 必要に応じてセル、列、行を編集・削除
            
            #### ステップ3: データの理解（分析タブ）
            - 数値変数とカテゴリ変数の識別
            - 各変数の統計量を確認
            - 欠損値の有無を確認
            
            #### ステップ4: 前処理設定（サイドバー）
            - **欠損値処理**: 自動処理（推奨）または手動設定
            - **外れ値処理**: 必要に応じて有効化
            - **カテゴリ変数エンコーディング**: 自動選択（推奨）
            - **特徴量スケーリング**: 必要に応じて選択
            
            #### ステップ5: 前処理の実行（前処理タブ）
            - 「前処理を実行」ボタンをクリック
            - 処理結果を確認
            - 処理済みデータをダウンロード
            
            ### 初心者向けの推奨設定
            - **欠損値処理**: 自動（auto）
            - **外れ値処理**: 無効（必要に応じて有効化）
            - **カテゴリ変数エンコーディング**: 自動（auto）
            - **特徴量スケーリング**: なし（必要に応じて選択）
            """)
    
    # ヘルプ表示（ヘルプボタンが押された場合）
    if 'show_help' in st.session_state:
        with st.expander("ヘルプ", expanded=True):
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
            """)
            
            if st.button("ヘルプを閉じる"):
                del st.session_state['show_help']
                st.rerun()
    
    # 前処理フローの説明
    with st.expander("データ前処理のフロー", expanded=False):
        st.markdown("""
        ### 標準的な前処理の流れ
        
        #### ステップ1: データの読み込みと確認
        1. **ファイルをアップロード**: サイドバーからCSV、Excel、JSONファイルをアップロード
        2. **エンコーディング設定**: 日本語ファイルの場合は適切なエンコーディングを選択
        3. **データの確認**: 「データプレビュー・編集」タブでデータを確認
        
        #### ステップ2: データの理解と診断（EDA）
        1. **データ情報の確認**: 「データ情報」タブで以下を確認
           - 数値変数とカテゴリ変数の識別
           - 各変数の値の範囲（最小値、最大値、ユニーク値など）
           - 欠損値の有無とパターン
        2. **データの可視化**: 統計量やグラフでデータの分布を確認
        
        #### ステップ3: データクリーニング
        1. **重複データの削除**: 「高度な分析」→「重複削除」で重複を検出・削除
        2. **異常値の処理**: 業務ルールに基づく異常値の除外（手動編集で対応）
        
        #### ステップ4: 外れ値の処理
        1. **外れ値検出方法の選択**: サイドバーで適切な方法を選択
           - **IQR法**: 四分位範囲を使用（一般的）
           - **Z-score法**: 標準偏差を使用
           - **Isolation Forest**: 機械学習ベース（多変量データに有効）
           - **MAD法**: 中央値絶対偏差（外れ値に強い）
           - **Winsorize法**: 上下をクリップ
           - **Mahalanobis距離**: 多変量外れ値検出
        2. **処理方法の選択**: 削除またはクリップ
        
        #### ステップ5: 欠損値の処理
        1. **処理方法の選択**: サイドバーで適切な方法を選択
           - **auto**: 自動処理（推奨）
           - **fill**: 補完（平均値、中央値、最頻値、前後の値）
           - **drop**: 削除
           - **listwise**: リストワイズ削除（完全ケースのみ）
           - **knn**: KNN補完（近傍データから推定）
           - **mice**: MICE補完（多重代入法、高精度）
        2. **欠損フラグの作成**: 欠損自体が情報となる場合に有効
        
        #### ステップ6: カテゴリ変数のエンコーディング
        1. **エンコーディング方法の選択**:
           - **auto**: 自動選択（推奨）
           - **label**: Label Encoding（順序がある場合）
           - **onehot**: One-Hot Encoding（名義尺度、少数カテゴリ）
           - **ordinal**: 順序エンコーディング（順序尺度）
           - **target**: Target Encoding（高カーディナリティに有効、注意: リーク対策必要）
           - **frequency**: Frequency Encoding（カテゴリの出現頻度）
           - **count**: Count Encoding（カテゴリの出現回数）
        
        #### ステップ7: 特徴量のスケーリング・正規化
        1. **スケーリング方法の選択**:
           - **standard**: 標準化（平均0、分散1、線形モデル、SVM、kNNに有効）
           - **minmax**: 0-1正規化（ニューラルネット、画像データに有効）
           - **robust**: Robust scaling（外れ値に強い）
           - **max_abs**: 最大絶対値スケーリング
           - **quantile**: 分位数変換（一様分布へ）
           - **quantile_normal**: 正規分布への変換
           - **power**: Yeo-Johnson変換（負の値もOK）
           - **box_cox**: Box-Cox変換（正の値のみ）
           - **log**: 対数変換（右裾が長い分布に有効）
           - **sqrt**: 平方根変換
        
        #### ステップ8: 特徴量エンジニアリング（オプション）
        1. **交互作用項の作成**: 「高度な分析」→「特徴量エンジニアリング」
        2. **多項式特徴の作成**: 非線形関係の捕捉
        3. **ビニング**: 連続変数をカテゴリに変換
        
        #### ステップ9: 特徴量選択（オプション）
        1. **特徴量選択の有効化**: サイドバーでチェック
        2. **選択する特徴量数の指定**: 上位N個を選択
        
        #### ステップ10: 共線性の確認（オプション）
        1. **VIF分析**: 「高度な分析」→「VIF分析」で共線性を検出
        2. **閾値以上の変数を削除**: VIF > 10の変数は削除を検討
        
        #### ステップ11: クラス不均衡の処理（分類タスクの場合）
        1. **不均衡処理方法の選択**: 「高度な分析」→「クラス不均衡」
           - **SMOTE**: Synthetic Minority Oversampling
           - **ADASYN**: Adaptive Synthetic Sampling
           - **Random Over/Under Sampling**: ランダムサンプリング
        
        #### ステップ12: データ分割（オプション）
        1. **分割方法の選択**: 「高度な分析」→「データ分割」
           - **random**: ランダム分割（独立同分布想定）
           - **stratified**: 層化分割（分類タスク、比率維持）
           - **timeseries**: 時系列分割（未来情報を混ぜない）
           - **group**: GroupKFold（同一グループが跨らない）
        
        #### ステップ13: 前処理の実行と結果の確認
        1. **前処理の実行**: 「前処理実行」タブで実行
        2. **結果の確認**: 処理前後の比較、統計量、可視化、統計検定
        3. **データのダウンロード**: 処理済みデータをCSV形式でダウンロード
        
        ### ⚠️ 重要な注意事項
        - **データリークの防止**: 学習データだけで前処理（fit）し、テスト/本番には同じ変換を適用（transform）
        - **CV（交差検証）**: 各foldの学習側で前処理を作る（Pipeline化が安全）
        - **統計モデル**: 係数の解釈が重要なので、変換の意味を説明できる形にする
        """)
    
    # 各機能の使い方
    with st.expander("📚 各機能の詳細な使い方", expanded=False):
        st.markdown("""
        ### データプレビュー・編集タブ
        
        #### 閲覧モード
        - データを参照番号付きで表示（列番号: [0], [1]...、行番号: 0, 1, 2...）
        - データの基本情報（行数、列数、欠損値、重複行）を表示
        
        #### 編集モード（セル編集）
        - セルを直接クリックして編集可能
        - 行の追加・削除が可能（data_editorの機能）
        
        #### 編集モード（列・行操作）
        - **列操作**:
          - 列を削除: 選択した列を削除
          - 列をコピー: クリップボードに保存
          - 列を移動: 列番号を指定して移動
          - 列名を変更: 新しい列名を入力
          - 列の型を変更: int64, float64, object, bool, datetime64に変換
        
        - **行操作**:
          - 行を選択: 行番号を指定して内容を確認（選択した行は他の操作で自動使用）
          - 行を削除: 選択した行を削除
          - 行をコピー: クリップボードに保存
          - 行を移動: 行番号と新しい位置を指定して移動
          - 行を複製: 選択した行を複製
        
        #### 追加の編集機能
        - **削除**: 列、行、セルの削除（複数選択可能、範囲指定可能）
        - **置換**: 列全体、条件付き、正規表現による置換
        - **並べ替え**: 列で並べ替え（昇順/降順）
        - **挿入・追加**: 列や行の追加
        - **入れ替え**: 列や行の入れ替え
        
        ### データ情報タブ
        
        - **数値変数とカテゴリ変数の識別**: 自動的に識別
        - **変数の詳細情報**: 各変数について以下を表示
          - 型、欠損値数、欠損率、ユニーク値数
          - 数値変数: 最小値、最大値、平均値、中央値、値の範囲
          - カテゴリ変数: 値の例（10個まで）
        - **欠損値の詳細**: 欠損値がある列の詳細情報
        
        ### 前処理実行タブ
        
        1. **ターゲット列の選択**: 特徴量選択やTarget Encodingを使用する場合
        2. **前処理の実行**: サイドバーで設定したオプションに基づいて実行
        3. **結果の確認**:
           - 処理後のデータ（最初の10行）
           - 処理結果の比較（処理前後の統計量、可視化、統計検定）
        4. **データのダウンロード**: 処理済みデータをCSV形式でダウンロード
        
        ### 高度な分析タブ
        
        - **重複削除**: 完全一致、キー重複、類似度ベースの重複削除
        - **特徴量エンジニアリング**: 交互作用項、多項式特徴、ビニング
        - **VIF分析**: 共線性の検出（VIF > 10の変数は削除を検討）
        - **クラス不均衡処理**: SMOTE、ADASYN、Random Over/Under Sampling
        - **データ分割**: ランダム、層化、時系列、グループ分割
        """)
    
    st.markdown("---")
    
    # サイドバー（先に定義してメイン部分で参照可能にする）
    with st.sidebar:
        st.markdown("## 📁 データの読み込み")
        
        uploaded_file = st.file_uploader(
            "ファイルをアップロード",
            type=['csv', 'xlsx', 'xls', 'json'],
            help="CSV、Excel、JSONファイルに対応",
            label_visibility="collapsed"
        )
        
        # エンコーディング選択（CSVファイルの場合）
        selected_encoding = None
        if uploaded_file is not None:
            # ファイル情報をコンパクトに表示
            file_size = uploaded_file.size / 1024  # KB
            st.success(f"**{uploaded_file.name}** ({file_size:.1f} KB)")
            
            # エンコーディング選択（CSV、Excel、JSONファイルすべてに対応）
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            if file_ext in ['.csv', '.txt']:
                st.markdown("**🔤 エンコーディング（CSVファイル）**")
                encoding_option = st.selectbox(
                    "エンコーディング",
                    ["自動検出", "UTF-8", "Shift-JIS (CP932)", "EUC-JP", "ISO-2022-JP", "CP932"],
                    help="日本語ファイルの文字化けを防ぐために選択。文字化けする場合は別のエンコーディングを試してください。",
                    key="encoding_select",
                    index=0
                )
                
                encoding_map = {
                    "自動検出": None,
                    "UTF-8": "utf-8",
                    "Shift-JIS (CP932)": "shift_jis",
                    "EUC-JP": "euc-jp",
                    "ISO-2022-JP": "iso-2022-jp",
                    "CP932": "cp932"
                }
                selected_encoding = encoding_map[encoding_option]
            elif file_ext in ['.xlsx', '.xls']:
                st.info("💡 Excelファイルは自動的にエンコーディングを検出します。")
                selected_encoding = None
            elif file_ext == '.json':
                st.info("💡 JSONファイルはUTF-8で読み込みます。")
                selected_encoding = "utf-8"
            else:
                selected_encoding = None
        
        st.markdown("---")
        st.markdown("## 前処理設定")
        
        # 初心者向けのクイック設定
        st.info("**初心者の方**: デフォルト設定のまま「前処理」タブで実行できます。")
        
        # 前処理オプション（コンパクトに）
        with st.expander("欠損値処理", expanded=True):
            st.caption("データに欠損値（空白やNaN）がある場合の処理方法を選択します")
            missing_strategy = st.selectbox(
                "処理方法",
                ["auto", "fill", "drop", "listwise", "knn", "mice", "em"],
                help="auto: 自動処理（推奨）",
                label_visibility="collapsed"
            )
            
            create_missing_flags = st.checkbox("欠損フラグを作成", value=False, 
                                              help="欠損値自体が情報となる場合に有効")
            
            if missing_strategy == "fill":
                missing_method = st.selectbox(
                    "補完方法",
                    ["mean", "median", "mode", "forward_fill", "backward_fill"],
                    help="mean: 平均値, median: 中央値, mode: 最頻値",
                    label_visibility="collapsed"
                )
            elif missing_strategy == "mice":
                n_iterations = st.number_input("MICE反復回数", min_value=1, max_value=20, value=5, 
                                              label_visibility="visible")
                missing_method = "mean"
            elif missing_strategy == "em":
                n_iterations = st.number_input("EM最大反復回数", min_value=10, max_value=200, value=100,
                                              label_visibility="visible")
                missing_method = "mean"
            else:
                missing_method = "mean"
                n_iterations = 5
        
        with st.expander("外れ値処理", expanded=False):
            st.caption("データから異常に大きい/小さい値を検出・処理します")
            remove_outliers = st.checkbox("外れ値を処理する", value=False)
            
            if remove_outliers:
                outlier_method_option = st.selectbox(
                    "外れ値検出方法",
                    [
                        "iqr (IQR法)",
                        "zscore (Z-score法)",
                        "isolation_forest (Isolation Forest)",
                        "mad (MAD法)",
                        "winsorize (Winsorize法)",
                        "mahalanobis (Mahalanobis距離)"
                    ],
                    help="外れ値の検出方法を選択",
                    label_visibility="collapsed"
                )
            
                # 括弧内の説明を削除
                outlier_method = outlier_method_option.split(" (")[0]
                
                outlier_action = st.radio(
                    "処理方法",
                    ["削除", "クリップ"],
                    help="削除: 外れ値を除去, クリップ: 外れ値をクリップ（Winsorize）",
                    horizontal=True
                )
                action = 'remove' if outlier_action == "削除" else 'clip'
                
                if outlier_method == "isolation_forest":
                    contamination = st.slider(
                        "外れ値の割合",
                        min_value=0.01,
                        max_value=0.5,
                        value=0.1,
                        step=0.01,
                        help="データ全体に対する外れ値の割合"
                    )
                    z_threshold = 3.0
                    iqr_multiplier = 1.5
                    winsorize_limits = (0.01, 0.99)
                elif outlier_method == "zscore":
                    z_threshold = st.slider(
                        "Z-scoreの閾値",
                        min_value=1.0,
                        max_value=5.0,
                        value=3.0,
                        step=0.5,
                        help="この値より大きいZ-scoreを持つデータを外れ値とみなします"
                    )
                    contamination = 0.1
                    iqr_multiplier = 1.5
                    winsorize_limits = (0.01, 0.99)
                elif outlier_method == "iqr":
                    iqr_multiplier = st.slider(
                        "IQRの倍数",
                        min_value=1.0,
                        max_value=3.0,
                        value=1.5,
                        step=0.1,
                        help="Q1 - k*IQR より小さい、または Q3 + k*IQR より大きい値を外れ値とみなします"
                    )
                    contamination = 0.1
                    z_threshold = 3.0
                    winsorize_limits = (0.01, 0.99)
                elif outlier_method == "winsorize":
                    lower_pct = st.slider("下限パーセンタイル", min_value=0.0, max_value=0.1, value=0.01, step=0.01)
                    upper_pct = st.slider("上限パーセンタイル", min_value=0.9, max_value=1.0, value=0.99, step=0.01)
                    winsorize_limits = (lower_pct, upper_pct)
                    contamination = 0.1
                    z_threshold = 3.0
                    iqr_multiplier = 1.5
                else:
                    contamination = 0.1
                    z_threshold = 3.0
                    iqr_multiplier = 1.5
                    winsorize_limits = (0.01, 0.99)
            else:
                outlier_method = "iqr"
                contamination = 0.1
                z_threshold = 3.0
                iqr_multiplier = 1.5
                winsorize_limits = (0.01, 0.99)
                action = 'remove'
        
        with st.expander("カテゴリ変数エンコーディング", expanded=False):
            st.caption("文字列やカテゴリデータを数値に変換します")
            encoding_method_option = st.selectbox(
                "エンコーディング方法",
                [
                    "auto (自動選択)",
                    "label (Label Encoding)",
                    "onehot (One-Hot Encoding)",
                    "ordinal (順序エンコーディング)",
                    "target (Target Encoding)",
                    "frequency (Frequency Encoding)",
                    "count (Count Encoding)"
                ],
                help="カテゴリ変数のエンコーディング方法を選択",
                label_visibility="collapsed"
            )
            encoding_method = encoding_method_option.split(" (")[0]
            
            if encoding_method == "target":
                st.info("💡 Target encoding使用時は、前処理実行時にターゲット列を選択してください。")
        
        with st.expander("特徴量スケーリング", expanded=False):
            st.caption("数値データの範囲を調整します（機械学習で重要）")
            scaling_method_option = st.selectbox(
                "スケーリング方法",
                [
                    "なし",
                    "standard (標準化)",
                    "minmax (0-1正規化)",
                    "robust (Robust scaling)",
                    "max_abs (最大絶対値)",
                    "quantile (分位数変換)",
                    "quantile_normal (正規分布への変換)",
                    "power (Yeo-Johnson変換)",
                    "box_cox (Box-Cox変換)",
                    "log (対数変換)",
                    "sqrt (平方根変換)"
                ],
                help="データの分布を変換・正規化します",
                label_visibility="collapsed"
            )
            
            if scaling_method_option == "なし":
                scaling_method = None
            else:
                scaling_method = scaling_method_option.split(" (")[0]
        
        with st.expander("特徴量選択", expanded=False):
            feature_selection = st.checkbox("特徴量選択を実行", value=False)
            if feature_selection:
                k_features = st.number_input(
                    "選択する特徴量数",
                    min_value=1,
                    max_value=100,
                    value=10,
                    help="上位N個の特徴量を選択",
                    label_visibility="visible"
                )
            else:
                k_features = "auto"
        
        with st.expander("詳細設定", expanded=False):
            categorical_threshold = st.number_input(
                "カテゴリ変数の閾値",
                min_value=2,
                max_value=50,
                value=10,
                help="ユニーク値がこの数以下の整数列をカテゴリ変数として扱う"
            )
        
        st.markdown("---")
        st.markdown("## 分析オプション")
        
        show_statistics = st.checkbox("記述統計量を表示", value=True)
        show_visualization = st.checkbox("グラフを表示", value=False, 
                                         help="変数が多い場合は非推奨")
        
        st.markdown("---")
        show_tests = st.checkbox("統計検定を実行", value=False, 
                                help="データの分布や特性を統計的に検定します")
        
        if show_tests:
            alpha_level = st.selectbox(
                "有意水準",
                [0.01, 0.05, 0.10],
                index=1,
                help="検定の有意水準を選択（デフォルト: 0.05）",
                key="alpha_level_sidebar"
            )
            
            with st.expander("統計検定の詳細", expanded=False):
                st.markdown("""
                ### 実装されている統計検定
                
                #### 1. 正規性検定
                データが正規分布に従うかを検定します。
                - **Shapiro-Wilk検定**: サンプルサイズが小さい場合（n ≤ 5000）に使用
                - **D'Agostino-Pearson検定**: 歪度と尖度に基づく検定
                - **Anderson-Darling検定**: より厳密な正規性検定
                
                #### 2. 分布の形状
                データの分布の特徴を数値で表現します。
                - **歪度（Skewness）**: 分布の非対称性を測定
                  - 正の値: 右に歪む（右裾が長い）
                  - 負の値: 左に歪む（左裾が長い）
                  - 0に近い: 対称的
                - **尖度（Kurtosis）**: 分布の尖り具合を測定
                  - 正の値: 正規分布より尖っている
                  - 負の値: 正規分布より平ら
                  - 0に近い: 正規分布に近い
                
                #### 3. 等分散性検定
                複数の変数間で分散が等しいかを検定します。
                - **Levene検定**: 正規分布でなくても使用可能（推奨）
                - **Bartlett検定**: 正規分布を仮定した検定
                
                #### 4. 独立性検定（カテゴリ変数）
                カテゴリ変数間の独立性を検定します。
                - **カイ二乗検定**: 2つのカテゴリ変数が独立かどうかを検定
                
                ### 使い方
                1. 「統計検定を実行」にチェックを入れる
                2. 「前処理実行」タブで前処理を実行
                3. 検定結果が自動的に表示されます
                
                ### 解釈の目安
                - **p値 < 0.05**: 有意差あり（帰無仮説を棄却）
                - **p値 ≥ 0.05**: 有意差なし（帰無仮説を採択）
                """)
        else:
            alpha_level = 0.05
    
    # メインコンテンツ
    if uploaded_file is not None:
        # ファイルを一時保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # データを読み込む
            preprocessor = DataPreprocessor()
            
            with st.spinner("データを読み込んでいます..."):
                # エンコーディングを指定
                if selected_encoding is not None:
                    df = preprocessor.load_data(tmp_path, encoding=selected_encoding, auto_detect_encoding=False, auto_detect_structure=True)
                else:
                    df = preprocessor.load_data(tmp_path, auto_detect_encoding=True, auto_detect_structure=True)
            
            st.success(f"✅ データの読み込みが完了しました: {df.shape[0]}行 × {df.shape[1]}列")
            
            # セッション状態にデータを保存
            if 'original_df' not in st.session_state or st.session_state.get('file_name') != uploaded_file.name:
                st.session_state['original_df'] = df.copy()
                st.session_state['current_df'] = df.copy()
                st.session_state['file_name'] = uploaded_file.name
            
            # 処理履歴を初期化（セッション状態に保存）
            if 'processing_history' not in st.session_state:
                st.session_state['processing_history'] = []
            
            # カスタムタブナビゲーション（タブの状態を保持）
            if 'active_tab' not in st.session_state:
                st.session_state['active_tab'] = "データ"
            
            # タブ選択UI
            tab_options = ["データ", "分析", "前処理", "高度な機能", "履歴"]
            # 現在のタブのインデックスを取得
            current_index = tab_options.index(st.session_state['active_tab']) if st.session_state['active_tab'] in tab_options else 0
            
            # タブ選択（keyを削除して、indexのみで制御）
            selected_tab = st.radio(
                "タブを選択",
                tab_options,
                index=current_index,
                horizontal=True,
                label_visibility="collapsed"
            )
            # タブが変更された場合のみ更新
            if selected_tab != st.session_state.get('active_tab'):
                st.session_state['active_tab'] = selected_tab
            
            # タブのコンテンツを表示
            if st.session_state['active_tab'] == "データ":
                st.markdown("### データの確認と編集")
                st.caption("データの内容を確認し、必要に応じて編集できます")
                
                # 処理済みデータのダウンロード（現在のデータフレーム）
                if 'current_df' in st.session_state and st.session_state['current_df'] is not None:
                    st.markdown("#### 処理済みデータのダウンロード")
                    df_dl = st.session_state['current_df']
                    
                    # CSV
                    csv_bytes = df_dl.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="CSVでダウンロード",
                        data=csv_bytes,
                        file_name="processed_data.csv",
                        mime="text/csv",
                        key="download_csv_current"
                    )
                    
                    # Excel
                    import io
                    excel_buffer = io.BytesIO()
                    df_dl.to_excel(excel_buffer, index=False, engine='openpyxl')
                    st.download_button(
                        label="Excelでダウンロード",
                        data=excel_buffer.getvalue(),
                        file_name="processed_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_xlsx_current"
                    )
                
                # 編集モードの選択
                edit_mode = st.radio(
                    "表示モード",
                    ["閲覧", "セル編集", "列・行操作"],
                    horizontal=True,
                    help="編集モードでは、セルを直接クリックして編集できます"
                )
                
                if edit_mode == "セル編集":
                    # 参照番号付きでデータを表示（列番号と行番号を表示）
                    df_display = st.session_state['current_df'].copy()
                    df_display.index.name = '行番号'
                    # 列名に番号を追加（表示用）
                    original_cols = df_display.columns.tolist()
                    df_display.columns = [f"[{i}] {col}" for i, col in enumerate(original_cols)]
                    
                    # Streamlitのdata_editorを使用（直接編集可能）
                    edited_df = st.data_editor(
                        df_display,
                        use_container_width=True,
                        height=400,
                        num_rows="dynamic",  # 行の追加・削除が可能
                        key="data_editor"
                    )
                    
                    # 列名から番号を除去して元に戻す
                    if not edited_df.equals(df_display):
                        edited_df.columns = [col.split('] ')[1] if '] ' in col else col for col in edited_df.columns]
                        st.session_state['current_df'] = edited_df
                        st.success("✅ データが更新されました")
                        st.rerun()
                
                elif edit_mode == "列・行操作":
                    # データを参照番号付きで表示
                    st.info("💡 ヒント: 列番号と行番号を確認してから操作してください")
                    
                    # 参照番号付きでデータを表示
                    df_display = st.session_state['current_df'].copy()
                    df_display.index.name = '行番号'
                    df_display.columns = [f"[{i}] {col}" for i, col in enumerate(df_display.columns)]
                    st.dataframe(df_display.head(20), use_container_width=True, height=300)
                    
                    # 列操作パネル
                    with st.expander("列操作", expanded=True):
                        col_op1, col_op2 = st.columns([1, 2])
                        with col_op1:
                            selected_col = st.selectbox("列を選択", st.session_state['current_df'].columns, key="col_select")
                            col_action = st.selectbox(
                                "操作",
                                ["列を削除", "列をコピー", "列を貼り付け", "列を移動", "列名を変更", "列の型を変更"],
                                key="col_action"
                            )
                        
                        # 操作に応じたUI要素を表示
                        with col_op2:
                            if col_action == "列を移動":
                                current_pos = st.session_state['current_df'].columns.get_loc(selected_col)
                                st.info(f"現在の位置: 列番号 {current_pos} ({selected_col})")
                                new_pos = st.number_input(
                                    "新しい位置（列番号）", 
                                    min_value=0, 
                                    max_value=len(st.session_state['current_df'].columns)-1, 
                                    value=current_pos,
                                    key="col_new_pos",
                                    help=f"0から{len(st.session_state['current_df'].columns)-1}の範囲で指定"
                                )
                            elif col_action == "列名を変更":
                                new_name = st.text_input("新しい列名", value=selected_col, key="col_new_name")
                            elif col_action == "列の型を変更":
                                current_dtype = str(st.session_state['current_df'][selected_col].dtype)
                                dtype_options = ["int64", "float64", "object", "bool", "datetime64"]
                                try:
                                    default_idx = dtype_options.index(current_dtype.split('[')[0] if '[' in current_dtype else current_dtype.split('.')[0])
                                except:
                                    default_idx = 0
                                new_dtype = st.selectbox(
                                    "新しい型",
                                    dtype_options,
                                    index=default_idx,
                                    key="col_new_dtype",
                                    help=f"現在の型: {current_dtype}"
                                )
                        
                        # 実行ボタン
                        if st.button("✅ 実行", key="col_exec", use_container_width=True, type="primary"):
                            try:
                                if col_action == "列を削除":
                                    st.session_state['current_df'] = st.session_state['current_df'].drop(columns=[selected_col])
                                    st.success(f"✅ 列 '{selected_col}' を削除しました")
                                    st.rerun()
                                
                                elif col_action == "列をコピー":
                                    st.session_state['clipboard_col'] = st.session_state['current_df'][selected_col].copy()
                                    st.session_state['clipboard_col_name'] = selected_col
                                    st.success(f"✅ 列 '{selected_col}' をコピーしました（クリップボードに保存）")
                                
                                elif col_action == "列を貼り付け":
                                    if 'clipboard_col' in st.session_state:
                                        paste_col_name = st.text_input(
                                            "新しい列名",
                                            value=st.session_state.get('clipboard_col_name', 'pasted_column'),
                                            key="paste_col_name"
                                        )
                                        paste_position = st.number_input(
                                            "貼り付け位置（列番号）",
                                            min_value=0,
                                            max_value=len(st.session_state['current_df'].columns),
                                            value=len(st.session_state['current_df'].columns),
                                            key="paste_col_pos"
                                        )
                                        
                                        if paste_col_name:
                                            if paste_col_name in st.session_state['current_df'].columns:
                                                st.error(f"❌ 列名 '{paste_col_name}' は既に存在します")
                                            else:
                                                # 列を追加
                                                st.session_state['current_df'].insert(
                                                    paste_position,
                                                    paste_col_name,
                                                    st.session_state['clipboard_col']
                                                )
                                                st.success(f"✅ 列 '{paste_col_name}' を貼り付けました")
                                                st.rerun()
                                    else:
                                        st.warning("⚠️ クリップボードに列がありません。先に列をコピーしてください。")
                                
                                elif col_action == "列を移動":
                                    # 列の移動を実装
                                    # new_posを取得（st.number_inputのkeyから）
                                    new_pos = st.session_state.get('col_new_pos', 0)
                                    
                                    cols = st.session_state['current_df'].columns.tolist()
                                    current_idx = cols.index(selected_col)
                                    
                                    # 現在の位置と同じ場合は何もしない
                                    if current_idx == new_pos:
                                        st.info(f"列 '{selected_col}' は既に位置 {new_pos} にあります")
                                    else:
                                        # 列を削除
                                        cols.remove(selected_col)
                                        # 新しい位置に挿入
                                        cols.insert(new_pos, selected_col)
                                        # 列の順序を変更
                                        st.session_state['current_df'] = st.session_state['current_df'][cols]
                                        st.success(f"✅ 列 '{selected_col}' を位置 {current_idx} から {new_pos} に移動しました")
                                        st.rerun()
                                
                                elif col_action == "列名を変更":
                                    # new_name変数を取得
                                    if 'new_name' not in locals():
                                        new_name = st.session_state.get('col_new_name', selected_col)
                                    
                                    if new_name and new_name != selected_col:
                                        if new_name in st.session_state['current_df'].columns:
                                            st.error(f"❌ 列名 '{new_name}' は既に存在します")
                                        else:
                                            st.session_state['current_df'] = st.session_state['current_df'].rename(columns={selected_col: new_name})
                                            st.success(f"✅ 列名を '{selected_col}' → '{new_name}' に変更しました")
                                            st.rerun()
                                    else:
                                        st.warning("⚠️ 新しい列名を入力してください（現在の列名と異なる必要があります）")
                                
                                elif col_action == "列の型を変更":
                                    # new_dtype変数を取得
                                    if 'new_dtype' not in locals():
                                        new_dtype = st.session_state.get('col_new_dtype', 'int64')
                                    
                                    try:
                                        if new_dtype == "int64":
                                            st.session_state['current_df'][selected_col] = pd.to_numeric(st.session_state['current_df'][selected_col], errors='coerce').astype('Int64')
                                        elif new_dtype == "float64":
                                            st.session_state['current_df'][selected_col] = pd.to_numeric(st.session_state['current_df'][selected_col], errors='coerce').astype('float64')
                                        elif new_dtype == "object":
                                            st.session_state['current_df'][selected_col] = st.session_state['current_df'][selected_col].astype('object')
                                        elif new_dtype == "bool":
                                            st.session_state['current_df'][selected_col] = st.session_state['current_df'][selected_col].astype('bool')
                                        elif new_dtype == "datetime64":
                                            st.session_state['current_df'][selected_col] = pd.to_datetime(st.session_state['current_df'][selected_col], errors='coerce')
                                        
                                        st.success(f"✅ 列 '{selected_col}' の型を '{new_dtype}' に変更しました")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ 型変換エラー: {e}")
                                        st.exception(e)
                            
                            except Exception as e:
                                st.error(f"❌ エラー: {e}")
                                st.exception(e)
                    
                    # 行操作パネル
                    with st.expander("行操作", expanded=True):
                        row_op1, row_op2 = st.columns([1, 2])
                        with row_op1:
                            row_action = st.selectbox(
                                "操作",
                                ["行を選択", "行を削除", "行をコピー", "行を貼り付け", "行を移動", "行を複製"],
                                key="row_action"
                            )
                        
                        # 操作に応じたUI要素を表示
                        with row_op2:
                            if row_action == "行を選択":
                                # 行を選択して表示
                                row_idx = st.number_input(
                                    "行番号を選択", 
                                    min_value=0, 
                                    max_value=max(0, len(st.session_state['current_df'])-1), 
                                    value=0, 
                                    key="row_select_idx",
                                    help=f"0から{max(0, len(st.session_state['current_df'])-1)}の範囲で指定"
                                )
                                if len(st.session_state['current_df']) > 0 and row_idx < len(st.session_state['current_df']):
                                    st.dataframe(st.session_state['current_df'].iloc[row_idx:row_idx+1], use_container_width=True)
                                    st.session_state['selected_row_idx'] = row_idx
                            
                            elif row_action in ["行を削除", "行を移動", "行を複製", "行を貼り付け"]:
                                # 選択された行を使用、または新しく選択
                                if 'selected_row_idx' in st.session_state:
                                    default_row = st.session_state['selected_row_idx']
                                else:
                                    default_row = 0
                                
                                row_idx = st.number_input(
                                    "行番号", 
                                    min_value=0, 
                                    max_value=max(0, len(st.session_state['current_df'])-1), 
                                    value=min(default_row, max(0, len(st.session_state['current_df'])-1)), 
                                    key="row_idx_delete_move",
                                    help=f"0から{max(0, len(st.session_state['current_df'])-1)}の範囲で指定"
                                )
                                
                                if row_action == "行を移動":
                                    new_pos = st.number_input(
                                        "新しい位置（行番号）", 
                                        min_value=0, 
                                        max_value=max(0, len(st.session_state['current_df'])-1), 
                                        value=min(row_idx, max(0, len(st.session_state['current_df'])-1)),
                                        key="row_new_pos",
                                        help=f"現在の位置: {row_idx}"
                                    )
                            
                            elif row_action == "行をコピー":
                                if 'selected_row_idx' in st.session_state:
                                    default_row = st.session_state['selected_row_idx']
                                else:
                                    default_row = 0
                                
                                row_idx = st.number_input(
                                    "行番号", 
                                    min_value=0, 
                                    max_value=max(0, len(st.session_state['current_df'])-1), 
                                    value=min(default_row, max(0, len(st.session_state['current_df'])-1)), 
                                    key="row_idx_copy",
                                    help=f"0から{max(0, len(st.session_state['current_df'])-1)}の範囲で指定"
                                )
                            
                            elif row_action == "行を貼り付け":
                                if 'clipboard_row' in st.session_state:
                                    paste_row_position = st.number_input(
                                        "貼り付け位置（行番号）",
                                        min_value=0,
                                        max_value=len(st.session_state['current_df']),
                                        value=len(st.session_state['current_df']),
                                        key="paste_row_pos"
                                    )
                                    
                                    # 貼り付け実行ボタン
                                    if st.button("✅ 貼り付け", key="row_paste_exec", use_container_width=True, type="primary"):
                                        try:
                                            # 行データを取得
                                            row_data = st.session_state['clipboard_row'].to_frame().T
                                            row_data.index = [paste_row_position]
                                            
                                            # 新しい位置に挿入
                                            st.session_state['current_df'] = pd.concat([
                                                st.session_state['current_df'].iloc[:paste_row_position],
                                                row_data,
                                                st.session_state['current_df'].iloc[paste_row_position:]
                                            ]).reset_index(drop=True)
                                            
                                            st.success(f"✅ 行を位置 {paste_row_position} に貼り付けました")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ エラー: {e}")
                                            st.exception(e)
                                else:
                                    st.warning("⚠️ クリップボードに行がありません。先に行をコピーしてください。")
                        
                        # 実行ボタン（行を選択と行を貼り付け以外）
                        if row_action not in ["行を選択", "行を貼り付け"]:
                            if st.button("✅ 実行", key="row_exec", use_container_width=True, type="primary"):
                                try:
                                    if row_action == "行を削除":
                                        if len(st.session_state['current_df']) > 0 and row_idx < len(st.session_state['current_df']):
                                            st.session_state['current_df'] = st.session_state['current_df'].drop(index=st.session_state['current_df'].index[row_idx]).reset_index(drop=True)
                                            st.success(f"✅ 行 {row_idx} を削除しました")
                                            if 'selected_row_idx' in st.session_state:
                                                del st.session_state['selected_row_idx']
                                            st.rerun()
                                        else:
                                            st.error(f"❌ 行番号 {row_idx} は範囲外です（行数: {len(st.session_state['current_df'])}）")
                                    
                                    elif row_action == "行をコピー":
                                        if len(st.session_state['current_df']) > 0 and row_idx < len(st.session_state['current_df']):
                                            st.session_state['clipboard_row'] = st.session_state['current_df'].iloc[row_idx].copy()
                                            st.success(f"✅ 行 {row_idx} をコピーしました（クリップボードに保存）")
                                        else:
                                            st.error(f"❌ 行番号 {row_idx} は範囲外です（行数: {len(st.session_state['current_df'])}）")
                                    
                                    elif row_action == "行を移動":
                                        # 行の移動を実装
                                        # new_posを取得（st.number_inputのkeyから）
                                        new_pos = st.session_state.get('row_new_pos', 0)
                                        
                                        if len(st.session_state['current_df']) > 0:
                                            if row_idx < len(st.session_state['current_df']) and new_pos < len(st.session_state['current_df']):
                                                # 現在の位置と同じ場合は何もしない
                                                if row_idx == new_pos:
                                                    st.info(f"行 {row_idx} は既に位置 {new_pos} にあります")
                                                else:
                                                    # 行データを取得
                                                    row_data = st.session_state['current_df'].iloc[row_idx:row_idx+1].copy()
                                                    
                                                    # 元の行を削除
                                                    df_without_row = pd.concat([
                                                        st.session_state['current_df'].iloc[:row_idx],
                                                        st.session_state['current_df'].iloc[row_idx+1:]
                                                    ]).reset_index(drop=True)
                                                    
                                                    # 新しい位置に挿入（位置が変わった場合は調整）
                                                    if new_pos > row_idx:
                                                        # 後ろに移動する場合、位置が1つずれる
                                                        insert_pos = new_pos - 1
                                                    else:
                                                        # 前に移動する場合、位置はそのまま
                                                        insert_pos = new_pos
                                                    
                                                    # 境界チェック
                                                    if insert_pos < 0:
                                                        insert_pos = 0
                                                    elif insert_pos > len(df_without_row):
                                                        insert_pos = len(df_without_row)
                                                    
                                                    # 新しい位置に挿入
                                                    st.session_state['current_df'] = pd.concat([
                                                        df_without_row.iloc[:insert_pos],
                                                        row_data,
                                                        df_without_row.iloc[insert_pos:]
                                                    ]).reset_index(drop=True)
                                                    
                                                    st.success(f"✅ 行 {row_idx} を位置 {new_pos} に移動しました")
                                                    if 'selected_row_idx' in st.session_state:
                                                        del st.session_state['selected_row_idx']
                                                    st.rerun()
                                            else:
                                                st.error(f"❌ 行番号が範囲外です（行数: {len(st.session_state['current_df'])}）")
                                        else:
                                            st.error("❌ データが空です")
                                    
                                    elif row_action == "行を複製":
                                        if len(st.session_state['current_df']) > 0 and row_idx < len(st.session_state['current_df']):
                                            row_data = st.session_state['current_df'].iloc[row_idx:row_idx+1].copy()
                                            st.session_state['current_df'] = pd.concat([
                                                st.session_state['current_df'].iloc[:row_idx+1],
                                                row_data,
                                                st.session_state['current_df'].iloc[row_idx+1:]
                                            ]).reset_index(drop=True)
                                            st.success(f"✅ 行 {row_idx} を複製しました（新しい行番号: {row_idx+1}）")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ 行番号 {row_idx} は範囲外です（行数: {len(st.session_state['current_df'])}）")
                                
                                except Exception as e:
                                    st.error(f"❌ エラー: {e}")
                                    st.exception(e)
                    
                    # データ表示
                    st.dataframe(st.session_state['current_df'], use_container_width=True, height=400)
                else:
                    # 閲覧モード（通常の表示）
                    st.dataframe(st.session_state['current_df'], use_container_width=True, height=500)
                
                # 追加の編集機能（削除、置換、並べ替え、挿入・追加、入れ替え）
                st.markdown("---")
                st.subheader("編集ツール")
                
                edit_tabs = st.tabs([
                    "削除", "置換", "並べ替え", "挿入・追加", "入れ替え"
                ])
                
                with edit_tabs[0]:
                    st.subheader("列・行・セルの削除")
                    
                    delete_option = st.radio(
                        "削除する項目を選択",
                        ["列を削除", "行を削除", "セルを削除（欠損値にする）"]
                    )
                    
                    if delete_option == "列を削除":
                        columns_to_delete = st.multiselect(
                            "削除する列を選択",
                            st.session_state['current_df'].columns.tolist(),
                            help="複数選択可能"
                        )
                        if st.button("選択した列を削除", type="primary"):
                            if columns_to_delete:
                                st.session_state['current_df'] = st.session_state['current_df'].drop(columns=columns_to_delete)
                                st.success(f"✅ {len(columns_to_delete)}個の列を削除しました")
                                # st.rerun()を削除（ページがリロードされないように）
                    
                    elif delete_option == "行を削除":
                        row_delete_method = st.radio(
                            "削除方法",
                            ["行番号を指定", "条件で指定"]
                        )
                        
                        if row_delete_method == "行番号を指定":
                            row_indices = st.text_input(
                                "削除する行番号（カンマ区切り、例: 0,1,2 または 0-5）",
                                help="例: 0,1,2 または 0-5"
                            )
                            if st.button("選択した行を削除", type="primary") and row_indices:
                                try:
                                    indices_to_delete = []
                                    for part in row_indices.split(','):
                                        part = part.strip()
                                        if '-' in part:
                                            start, end = map(int, part.split('-'))
                                            indices_to_delete.extend(range(start, end + 1))
                                        else:
                                            indices_to_delete.append(int(part))
                                    
                                    st.session_state['current_df'] = st.session_state['current_df'].drop(index=indices_to_delete)
                                    st.success(f"✅ {len(indices_to_delete)}個の行を削除しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                        
                        else:  # 条件で指定
                            st.subheader("条件による行削除")
                            condition_col = st.selectbox("条件の基準となる列を選択", st.session_state['current_df'].columns, key="cond_delete_col")
                            condition_type = st.selectbox("条件", ["以上", "以下", "等しい", "含む", "より大きい", "より小さい"], key="cond_delete_type")
                            condition_value = st.text_input("条件の値", key="cond_delete_value")
                            
                            if st.button("条件に一致する行を削除", type="primary", key="cond_delete_btn") and condition_value:
                                try:
                                    # 数値列かどうかを判定
                                    is_numeric = pd.api.types.is_numeric_dtype(st.session_state['current_df'][condition_col])
                                    
                                    if is_numeric:
                                        cond_value_num = float(condition_value) if '.' in condition_value else int(condition_value)
                                        
                                        if condition_type == "以上":
                                            mask = st.session_state['current_df'][condition_col] >= cond_value_num
                                        elif condition_type == "以下":
                                            mask = st.session_state['current_df'][condition_col] <= cond_value_num
                                        elif condition_type == "等しい":
                                            mask = st.session_state['current_df'][condition_col] == cond_value_num
                                        elif condition_type == "より大きい":
                                            mask = st.session_state['current_df'][condition_col] > cond_value_num
                                        elif condition_type == "より小さい":
                                            mask = st.session_state['current_df'][condition_col] < cond_value_num
                                        else:  # 含む（数値列では使用不可）
                                            st.warning("数値列では「含む」条件は使用できません")
                                            mask = pd.Series([False] * len(st.session_state['current_df']))
                                    else:
                                        if condition_type == "含む":
                                            mask = st.session_state['current_df'][condition_col].astype(str).str.contains(condition_value, na=False)
                                        elif condition_type == "等しい":
                                            mask = st.session_state['current_df'][condition_col].astype(str) == condition_value
                                        else:
                                            st.warning("文字列列では「以上」「以下」「より大きい」「より小さい」条件は使用できません")
                                            mask = pd.Series([False] * len(st.session_state['current_df']))
                                    
                                    if mask.sum() > 0:
                                        st.session_state['current_df'] = st.session_state['current_df'][~mask].reset_index(drop=True)
                                        st.success(f"✅ {mask.sum()}個の行を削除しました")
                                        st.rerun()
                                    else:
                                        st.info("条件に一致する行が見つかりませんでした")
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                    
                    else:  # セルを削除
                        col_for_cell = st.selectbox("列を選択", st.session_state['current_df'].columns)
                        row_indices = st.text_input(
                            "削除する行番号（カンマ区切り）",
                            help="例: 0,1,2"
                        )
                        if st.button("選択したセルを削除", type="primary") and row_indices:
                            try:
                                indices = [int(x.strip()) for x in row_indices.split(',')]
                                st.session_state['current_df'].loc[indices, col_for_cell] = np.nan
                                st.success(f"✅ {len(indices)}個のセルを削除しました")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")
                
                with edit_tabs[1]:
                    st.subheader("値の一括置換")
                    
                    replace_option = st.radio(
                        "置換方法",
                        ["列全体を置換", "条件付き置換", "正規表現による置換"]
                    )
                    
                    if replace_option == "列全体を置換":
                        replace_col = st.selectbox("置換する列を選択", st.session_state['current_df'].columns, key="replace_col")
                        old_value = st.text_input("置換前の値", help="この値を持つすべてのセルを置換します", key="old_value")
                        new_value = st.text_input("置換後の値", key="new_value")
                        
                        if st.button("一括置換を実行", type="primary", key="replace_btn") and old_value:
                            try:
                                # 数値の場合は数値として扱う
                                try:
                                    old_value_num = float(old_value) if '.' in old_value else int(old_value)
                                    new_value_num = float(new_value) if new_value and '.' in new_value else (int(new_value) if new_value and new_value.isdigit() else new_value)
                                    count_before = (st.session_state['current_df'][replace_col] == old_value_num).sum()
                                    st.session_state['current_df'][replace_col] = st.session_state['current_df'][replace_col].replace(old_value_num, new_value_num)
                                    st.success(f"✅ 置換が完了しました（{count_before}個のセルが更新されました）")
                                except:
                                    count_before = (st.session_state['current_df'][replace_col].astype(str) == old_value).sum()
                                    st.session_state['current_df'][replace_col] = st.session_state['current_df'][replace_col].astype(str).replace(old_value, new_value)
                                    st.success(f"✅ 置換が完了しました（{count_before}個のセルが更新されました）")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")
                    
                    elif replace_option == "条件付き置換":
                        replace_col = st.selectbox("置換する列を選択", st.session_state['current_df'].columns, key="cond_replace_col")
                        condition_type = st.selectbox("条件", ["以上", "以下", "等しい", "含む"], key="cond_type")
                        condition_value = st.text_input("条件の値", key="cond_value")
                        new_value = st.text_input("置換後の値", key="cond_new_value")
                        
                        if st.button("条件付き置換を実行", type="primary", key="cond_replace_btn") and condition_value:
                            try:
                                # 数値列かどうかを判定
                                is_numeric = pd.api.types.is_numeric_dtype(st.session_state['current_df'][replace_col])
                                
                                if is_numeric:
                                    cond_value_num = float(condition_value) if '.' in condition_value else int(condition_value)
                                    
                                    if condition_type == "以上":
                                        mask = st.session_state['current_df'][replace_col] >= cond_value_num
                                    elif condition_type == "以下":
                                        mask = st.session_state['current_df'][replace_col] <= cond_value_num
                                    elif condition_type == "等しい":
                                        mask = st.session_state['current_df'][replace_col] == cond_value_num
                                    else:  # 含む（数値列では使用不可）
                                        st.warning("数値列では「含む」条件は使用できません")
                                        mask = pd.Series([False] * len(st.session_state['current_df']))
                                else:
                                    if condition_type == "含む":
                                        mask = st.session_state['current_df'][replace_col].astype(str).str.contains(condition_value, na=False)
                                    elif condition_type == "等しい":
                                        mask = st.session_state['current_df'][replace_col].astype(str) == condition_value
                                    else:
                                        st.warning("文字列列では「以上」「以下」条件は使用できません")
                                        mask = pd.Series([False] * len(st.session_state['current_df']))
                                
                                if mask.sum() > 0:
                                    new_val = float(new_value) if new_value and '.' in new_value else (int(new_value) if new_value and new_value.isdigit() else new_value)
                                    st.session_state['current_df'].loc[mask, replace_col] = new_val
                                    st.success(f"✅ 置換が完了しました（{mask.sum()}個のセルが更新されました）")
                                else:
                                    st.info("条件に一致するセルが見つかりませんでした")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")
                    
                    else:  # 正規表現による置換
                        replace_col = st.selectbox("置換する列を選択", st.session_state['current_df'].columns, key="regex_replace_col")
                        pattern = st.text_input("正規表現パターン", help="例: ^[0-9]+$ で数字のみにマッチ", key="regex_pattern")
                        replacement = st.text_input("置換後の値", key="regex_replacement")
                        
                        if st.button("正規表現置換を実行", type="primary", key="regex_replace_btn") and pattern:
                            try:
                                import re
                                def replace_func(x):
                                    if pd.isna(x):
                                        return x
                                    x_str = str(x)
                                    if re.search(pattern, x_str):
                                        return replacement if replacement else x
                                    return x
                                
                                count_before = st.session_state['current_df'][replace_col].apply(lambda x: bool(re.search(pattern, str(x)) if pd.notna(x) else False)).sum()
                                st.session_state['current_df'][replace_col] = st.session_state['current_df'][replace_col].apply(replace_func)
                                st.success(f"✅ 正規表現による置換が完了しました（{count_before}個のセルが更新されました）")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")
                    
                    st.markdown("---")
                    st.subheader("セルの個別編集")
                    
                    edit_col = st.selectbox("編集する列を選択", st.session_state['current_df'].columns, key="single_edit_col")
                    edit_row = st.number_input("編集する行番号", min_value=0, max_value=len(st.session_state['current_df'])-1, value=0, key="single_edit_row")
                    
                    current_value = st.session_state['current_df'].iloc[edit_row][edit_col]
                    st.info(f"現在の値: {current_value}")
                    
                    new_value = st.text_input("新しい値", value=str(current_value) if pd.notna(current_value) else "", key="single_edit_value")
                    
                    if st.button("セルを更新", type="primary", key="single_edit_btn"):
                        try:
                            # 数値に変換できる場合は数値として保存
                            try:
                                if '.' in new_value:
                                    new_value = float(new_value)
                                else:
                                    new_value = int(new_value)
                            except:
                                pass  # 文字列のまま
                            
                            st.session_state['current_df'].iloc[edit_row, st.session_state['current_df'].columns.get_loc(edit_col)] = new_value
                            st.success("✅ セルを更新しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"エラー: {e}")
                
                with edit_tabs[2]:
                    st.subheader("並べ替え")
                    
                    sort_option = st.radio("並べ替え方法", ["列で並べ替え", "行で並べ替え"])
                    
                    if sort_option == "列で並べ替え":
                        sort_column = st.selectbox("並べ替え基準の列", st.session_state['current_df'].columns)
                        ascending = st.checkbox("昇順", value=True)
                        
                        if st.button("並べ替えを実行", type="primary"):
                            st.session_state['current_df'] = st.session_state['current_df'].sort_values(by=sort_column, ascending=ascending).reset_index(drop=True)
                            st.success("✅ 並べ替えが完了しました")
                            st.rerun()
                    else:
                        st.info("行の並べ替え機能は開発中です")
                
                with edit_tabs[3]:
                    st.subheader("挿入・追加")
                    
                    insert_option = st.radio("操作", ["列を追加", "行を追加"])
                    
                    if insert_option == "列を追加":
                        new_col_name = st.text_input("新しい列名")
                        insert_position = st.number_input("挿入位置（列番号）", min_value=0, max_value=len(st.session_state['current_df'].columns), value=len(st.session_state['current_df'].columns))
                        default_value = st.text_input("デフォルト値（空欄の場合はNaN）", value="")
                        
                        if st.button("列を追加", type="primary") and new_col_name:
                            try:
                                if default_value == "":
                                    default_value = np.nan
                                else:
                                    try:
                                        default_value = float(default_value)
                                    except:
                                        pass
                                
                                # 列を追加
                                st.session_state['current_df'].insert(insert_position, new_col_name, default_value)
                                st.success("✅ 列を追加しました")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")
                    
                    else:  # 行を追加
                        insert_row_position = st.number_input("挿入位置（行番号）", min_value=0, max_value=len(st.session_state['current_df']), value=len(st.session_state['current_df']))
                        num_rows = st.number_input("追加する行数", min_value=1, max_value=10, value=1)
                        
                        if st.button("行を追加", type="primary"):
                            try:
                                new_rows = pd.DataFrame(
                                    [[np.nan] * len(st.session_state['current_df'].columns)] * num_rows,
                                    columns=st.session_state['current_df'].columns
                                )
                                st.session_state['current_df'] = pd.concat([
                                    st.session_state['current_df'].iloc[:insert_row_position],
                                    new_rows,
                                    st.session_state['current_df'].iloc[insert_row_position:]
                                ]).reset_index(drop=True)
                                st.success(f"✅ {num_rows}個の行を追加しました")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")
                
                with edit_tabs[4]:
                    st.subheader("入れ替え")
                    
                    swap_option = st.radio("入れ替え方法", ["列を入れ替え", "行を入れ替え"])
                    
                    if swap_option == "列を入れ替え":
                        col1, col2 = st.columns(2)
                        with col1:
                            col1_name = st.selectbox("列1", st.session_state['current_df'].columns, key="swap_col1")
                        with col2:
                            col2_name = st.selectbox("列2", st.session_state['current_df'].columns, key="swap_col2")
                        
                        if st.button("列を入れ替え", type="primary"):
                            try:
                                cols = st.session_state['current_df'].columns.tolist()
                                idx1, idx2 = cols.index(col1_name), cols.index(col2_name)
                                cols[idx1], cols[idx2] = cols[idx2], cols[idx1]
                                st.session_state['current_df'] = st.session_state['current_df'][cols]
                                st.success("✅ 列を入れ替えました")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")
                    
                    else:  # 行を入れ替え
                        row1_idx = st.number_input("行1の番号", min_value=0, max_value=len(st.session_state['current_df'])-1, value=0, key="swap_row1")
                        row2_idx = st.number_input("行2の番号", min_value=0, max_value=len(st.session_state['current_df'])-1, value=1, key="swap_row2")
                        
                        if st.button("行を入れ替え", type="primary"):
                            try:
                                row1 = st.session_state['current_df'].iloc[row1_idx].copy()
                                row2 = st.session_state['current_df'].iloc[row2_idx].copy()
                                st.session_state['current_df'].iloc[row1_idx] = row2
                                st.session_state['current_df'].iloc[row2_idx] = row1
                                st.success("✅ 行を入れ替えました")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")
                
                # リセットボタン
                st.markdown("---")
                if st.button("編集をリセット（元のデータに戻す）", type="secondary"):
                    st.session_state['current_df'] = st.session_state['original_df'].copy()
                    st.success("✅ データをリセットしました")
                    st.rerun()
            
            elif st.session_state['active_tab'] == "分析":
                # 列のタイプを識別
                preprocessor.identify_columns(st.session_state['current_df'], categorical_threshold=categorical_threshold)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("数値変数")
                    if len(preprocessor.numerical_columns) > 0:
                        st.write(preprocessor.numerical_columns)
                    else:
                        st.info("数値変数が見つかりませんでした")
                
                with col2:
                    st.subheader("カテゴリ変数")
                    if len(preprocessor.categorical_columns) > 0:
                        st.write(preprocessor.categorical_columns)
                    else:
                        st.info("カテゴリ変数が見つかりませんでした")
                
                # 各変数の詳細情報（値の範囲を含む）
                st.subheader("変数の詳細情報")
                info_data = []
                
                for col in st.session_state['current_df'].columns:
                    col_info = {
                        '列名': col,
                        '型': str(st.session_state['current_df'][col].dtype),
                        '欠損値数': st.session_state['current_df'][col].isnull().sum(),
                        '欠損率(%)': round(st.session_state['current_df'][col].isnull().sum() / len(st.session_state['current_df']) * 100, 2),
                        'ユニーク値数': st.session_state['current_df'][col].nunique()
                    }
                    
                    # 値の範囲を追加
                    if col in preprocessor.numerical_columns:
                        col_info['最小値'] = st.session_state['current_df'][col].min()
                        col_info['最大値'] = st.session_state['current_df'][col].max()
                        col_info['平均値'] = round(st.session_state['current_df'][col].mean(), 2)
                        col_info['中央値'] = st.session_state['current_df'][col].median()
                        col_info['値の範囲'] = f"[{col_info['最小値']:.2f}, {col_info['最大値']:.2f}]"
                    else:
                        # カテゴリ変数の場合、値の例を表示
                        unique_vals = st.session_state['current_df'][col].dropna().unique()
                        if len(unique_vals) <= 10:
                            col_info['値の範囲'] = ', '.join([str(v) for v in unique_vals[:10]])
                        else:
                            col_info['値の範囲'] = ', '.join([str(v) for v in unique_vals[:10]]) + f" ... (他{len(unique_vals)-10}個)"
                    
                    info_data.append(col_info)
                
                info_df = pd.DataFrame(info_data)
                st.dataframe(info_df, use_container_width=True)
                
                # 欠損値の詳細
                if st.session_state['current_df'].isnull().sum().sum() > 0:
                    st.subheader("欠損値の詳細")
                    missing_df = pd.DataFrame({
                        '列名': st.session_state['current_df'].columns,
                        '欠損値数': st.session_state['current_df'].isnull().sum().values,
                        '欠損率(%)': (st.session_state['current_df'].isnull().sum() / len(st.session_state['current_df']) * 100).values
                    })
                    missing_df = missing_df[missing_df['欠損値数'] > 0].sort_values('欠損値数', ascending=False)
                    st.dataframe(missing_df, use_container_width=True)
                
                # 変数選択と可視化・統計処理
                st.markdown("---")
                st.subheader("変数の可視化・統計処理")
                
                selected_var = st.selectbox(
                    "分析する変数を選択",
                    ["なし"] + list(st.session_state['current_df'].columns),
                    key="selected_var_analysis"
                )
                
                if selected_var != "なし":
                    var_data = st.session_state['current_df'][selected_var]
                    is_numeric_var = pd.api.types.is_numeric_dtype(var_data)
                    
                    # 基本統計量
                    st.subheader(f"{selected_var} の基本統計量")
                    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                    
                    with stat_col1:
                        st.metric("データ数", len(var_data))
                    with stat_col2:
                        st.metric("欠損値", var_data.isnull().sum())
                    with stat_col3:
                        st.metric("ユニーク値", var_data.nunique())
                    with stat_col4:
                        if is_numeric_var:
                            st.metric("平均値", f"{var_data.mean():.2f}")
                        else:
                            st.metric("最頻値", var_data.mode()[0] if len(var_data.mode()) > 0 else "N/A")
                    
                    # 詳細統計量（数値変数の場合）
                    if is_numeric_var:
                        st.subheader("詳細統計量")
                        detail_stats = {
                            '最小値': var_data.min(),
                            '25%分位点': var_data.quantile(0.25),
                            '中央値': var_data.median(),
                            '75%分位点': var_data.quantile(0.75),
                            '最大値': var_data.max(),
                            '平均値': var_data.mean(),
                            '標準偏差': var_data.std(),
                            '歪度': var_data.skew(),
                            '尖度': var_data.kurtosis()
                        }
                        stats_df = pd.DataFrame([detail_stats]).T
                        stats_df.columns = ['値']
                        st.dataframe(stats_df, use_container_width=True)
                    
                    # 可視化
                    st.subheader(f"{selected_var} の可視化")
                    
                    if is_numeric_var:
                        # 数値変数の可視化
                        viz_tabs = st.tabs(["ヒストグラム", "箱ひげ図", "散布図（他の変数との関係）"])
                        
                        with viz_tabs[0]:
                            bins = st.slider("ビン数", min_value=10, max_value=100, value=30, key="hist_bins")
                            if st.button("ヒストグラムを表示", key="show_hist"):
                                try:
                                    import matplotlib.pyplot as plt
                                    # japanize-matplotlibが利用可能な場合は使用
                                    try:
                                        import japanize_matplotlib
                                    except ImportError:
                                        from data_preprocessor import setup_japanese_font
                                        setup_japanese_font()
                                    
                                    data_to_plot = var_data.dropna()
                                    if len(data_to_plot) == 0:
                                        st.warning("表示するデータがありません。")
                                    else:
                                        fig, ax = plt.subplots(figsize=(10, 6))
                                        ax.hist(data_to_plot, bins=bins, edgecolor='black', alpha=0.7)
                                        ax.set_xlabel(selected_var, fontsize=12)
                                        ax.set_ylabel('頻度', fontsize=12)
                                        ax.set_title(f'{selected_var}の分布', fontsize=14)
                                        ax.grid(True, alpha=0.3)
                                        st.pyplot(fig, clear_figure=True)
                                        plt.close(fig)
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                        
                        with viz_tabs[1]:
                            if st.button("箱ひげ図を表示", key="show_box"):
                                try:
                                    import matplotlib.pyplot as plt
                                    # japanize-matplotlibが利用可能な場合は使用
                                    try:
                                        import japanize_matplotlib
                                    except ImportError:
                                        from data_preprocessor import setup_japanese_font
                                        setup_japanese_font()
                                    
                                    data_to_plot = var_data.dropna()
                                    if len(data_to_plot) == 0:
                                        st.warning("表示するデータがありません。")
                                    else:
                                        fig, ax = plt.subplots(figsize=(8, 6))
                                        ax.boxplot(data_to_plot, vert=True)
                                        ax.set_ylabel(selected_var, fontsize=12)
                                        ax.set_title(f'{selected_var}の箱ひげ図', fontsize=14)
                                        ax.grid(True, alpha=0.3)
                                        st.pyplot(fig, clear_figure=True)
                                        plt.close(fig)
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                        
                        with viz_tabs[2]:
                            other_var = st.selectbox(
                                "比較する変数を選択",
                                ["なし"] + [col for col in st.session_state['current_df'].columns if col != selected_var and pd.api.types.is_numeric_dtype(st.session_state['current_df'][col])],
                                key="scatter_var"
                            )
                            
                            if other_var != "なし" and st.button("散布図を表示", key="show_scatter"):
                                try:
                                    import matplotlib.pyplot as plt
                                    # japanize-matplotlibが利用可能な場合は使用
                                    try:
                                        import japanize_matplotlib
                                    except ImportError:
                                        from data_preprocessor import setup_japanese_font
                                        setup_japanese_font()
                                    
                                    scatter_data = st.session_state['current_df'][[selected_var, other_var]].dropna()
                                    if len(scatter_data) == 0:
                                        st.warning("表示するデータがありません。")
                                    else:
                                        fig, ax = plt.subplots(figsize=(10, 6))
                                        ax.scatter(scatter_data[selected_var], scatter_data[other_var], alpha=0.5)
                                        ax.set_xlabel(selected_var, fontsize=12)
                                        ax.set_ylabel(other_var, fontsize=12)
                                        ax.set_title(f'{selected_var} vs {other_var}', fontsize=14)
                                        ax.grid(True, alpha=0.3)
                                        
                                        # 相関係数を表示
                                        corr = scatter_data[selected_var].corr(scatter_data[other_var])
                                        ax.text(0.05, 0.95, f'相関係数: {corr:.3f}', 
                                               transform=ax.transAxes, fontsize=12,
                                               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                                        st.pyplot(fig, clear_figure=True)
                                        plt.close(fig)
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                    
                    else:
                        # カテゴリ変数の可視化
                        viz_tabs = st.tabs(["棒グラフ", "円グラフ", "クロス集計"])
                        
                        with viz_tabs[0]:
                            top_n = st.slider("表示するカテゴリ数", min_value=5, max_value=50, value=10, key="bar_top_n")
                            if st.button("棒グラフを表示", key="show_bar"):
                                try:
                                    import matplotlib.pyplot as plt
                                    # japanize-matplotlibが利用可能な場合は使用
                                    try:
                                        import japanize_matplotlib
                                    except ImportError:
                                        from data_preprocessor import setup_japanese_font
                                        setup_japanese_font()
                                    
                                    value_counts = var_data.value_counts().head(top_n)
                                    if len(value_counts) == 0:
                                        st.warning("表示するデータがありません。")
                                    else:
                                        fig, ax = plt.subplots(figsize=(12, 6))
                                        value_counts.plot(kind='bar', ax=ax, color='steelblue', edgecolor='black')
                                        ax.set_xlabel(selected_var, fontsize=12)
                                        ax.set_ylabel('頻度', fontsize=12)
                                        ax.set_title(f'{selected_var}の分布', fontsize=14)
                                        ax.tick_params(axis='x', rotation=45)
                                        ax.grid(True, alpha=0.3, axis='y')
                                        st.pyplot(fig, clear_figure=True)
                                        plt.close(fig)
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                        
                        with viz_tabs[1]:
                            top_n_pie = st.slider("表示するカテゴリ数", min_value=5, max_value=20, value=10, key="pie_top_n")
                            if st.button("円グラフを表示", key="show_pie"):
                                try:
                                    import matplotlib.pyplot as plt
                                    # japanize-matplotlibが利用可能な場合は使用
                                    try:
                                        import japanize_matplotlib
                                    except ImportError:
                                        from data_preprocessor import setup_japanese_font
                                        setup_japanese_font()
                                    
                                    value_counts = var_data.value_counts().head(top_n_pie)
                                    if len(value_counts) == 0:
                                        st.warning("表示するデータがありません。")
                                    else:
                                        fig, ax = plt.subplots(figsize=(10, 8))
                                        ax.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%', startangle=90)
                                        ax.set_title(f'{selected_var}の分布', fontsize=14)
                                        st.pyplot(fig, clear_figure=True)
                                        plt.close(fig)
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                        
                        with viz_tabs[2]:
                            other_cat_var = st.selectbox(
                                "クロス集計する変数を選択",
                                ["なし"] + [col for col in st.session_state['current_df'].columns if col != selected_var],
                                key="crosstab_var"
                            )
                            
                            if other_cat_var != "なし" and st.button("クロス集計を表示", key="show_crosstab"):
                                try:
                                    crosstab = pd.crosstab(st.session_state['current_df'][selected_var], 
                                                          st.session_state['current_df'][other_cat_var])
                                    st.dataframe(crosstab, use_container_width=True)
                                    
                                    # 可視化
                                    import matplotlib.pyplot as plt
                                    import seaborn as sns
                                    # japanize-matplotlibが利用可能な場合は使用
                                    try:
                                        import japanize_matplotlib
                                    except ImportError:
                                        from data_preprocessor import setup_japanese_font
                                        setup_japanese_font()
                                    
                                    if crosstab.empty:
                                        st.warning("クロス集計データがありません。")
                                    else:
                                        fig, ax = plt.subplots(figsize=(12, 8))
                                        sns.heatmap(crosstab, annot=True, fmt='d', cmap='YlOrRd', ax=ax)
                                        ax.set_title(f'{selected_var} × {other_cat_var} のクロス集計', fontsize=14)
                                        st.pyplot(fig, clear_figure=True)
                                        plt.close(fig)
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                    
                    # 値の分布（テーブル）
                    st.subheader("値の分布")
                    if is_numeric_var:
                        # 数値変数の場合、範囲別の集計
                        n_bins_dist = st.slider("ビン数", min_value=5, max_value=50, value=10, key="dist_bins")
                        if st.button("分布を表示", key="show_dist"):
                            try:
                                bins = pd.cut(var_data.dropna(), bins=n_bins_dist)
                                dist_df = pd.DataFrame({
                                    '範囲': bins.value_counts().index.astype(str),
                                    '頻度': bins.value_counts().values,
                                    '割合(%)': (bins.value_counts().values / len(var_data.dropna()) * 100).round(2)
                                }).sort_index()
                                st.dataframe(dist_df, use_container_width=True)
                            except Exception as e:
                                st.error(f"エラー: {e}")
                    else:
                        # カテゴリ変数の場合、値の頻度表
                        value_counts_df = pd.DataFrame({
                            '値': var_data.value_counts().index,
                            '頻度': var_data.value_counts().values,
                            '割合(%)': (var_data.value_counts().values / len(var_data) * 100).round(2)
                        })
                        st.dataframe(value_counts_df, use_container_width=True)
            
            elif st.session_state['active_tab'] == "前処理":
                st.markdown("### 前処理の実行")
                st.caption("サイドバーで設定した前処理を実行します")
                
                # 前処理設定のサマリーを表示
                col_sum1, col_sum2 = st.columns(2)
                with col_sum1:
                    st.markdown("**現在の設定**")
                    st.markdown(f"- 欠損値: `{missing_strategy}`")
                    st.markdown(f"- 外れ値: {'有効' if remove_outliers else '無効'}")
                with col_sum2:
                    st.markdown("**現在の設定（続き）**")
                    st.markdown(f"- エンコーディング: `{encoding_method}`")
                    st.markdown(f"- スケーリング: `{scaling_method if scaling_method else 'なし'}`")
                
                # ターゲット列の選択（特徴量選択を使用する場合）
                target_col = None
                if feature_selection:
                    target_col = st.selectbox(
                        "ターゲット列（特徴量選択用）",
                        ["なし"] + list(st.session_state['current_df'].columns),
                        help="特徴量選択を実行する場合は、ターゲット列を選択してください"
                    )
                    if target_col == "なし":
                        target_col = None
                
                st.markdown("---")
                
                # 前処理実行ボタン（より目立つデザイン）
                col_exec1, col_exec2, col_exec3 = st.columns([1, 2, 1])
                with col_exec2:
                    if st.button("前処理を実行", type="primary", use_container_width=True):
                        with st.spinner("前処理を実行中..."):
                            try:
                                # 前処理を実行（編集済みデータを使用）
                                processed_df = st.session_state['current_df'].copy()
                                
                                # 列の識別
                                preprocessor.identify_columns(processed_df, categorical_threshold=categorical_threshold)
                                
                                # 欠損値処理
                                if missing_strategy == "mice":
                                    processed_df = preprocessor.handle_missing_values(
                                        processed_df, 
                                        strategy=missing_strategy, 
                                        method=missing_method,
                                        create_missing_flags=create_missing_flags,
                                        n_iterations=n_iterations
                                    )
                                elif missing_strategy == "em":
                                    processed_df = preprocessor.impute_missing_em(
                                        processed_df,
                                        max_iter=n_iterations
                                    )
                                    if create_missing_flags:
                                        for col in processed_df.columns:
                                            if processed_df[col].isnull().sum() > 0:
                                                flag_col_name = f'{col}_is_missing'
                                                processed_df[flag_col_name] = processed_df[col].isnull().astype(int)
                                else:
                                    processed_df = preprocessor.handle_missing_values(
                                        processed_df, 
                                        strategy=missing_strategy, 
                                        method=missing_method,
                                        create_missing_flags=create_missing_flags
                                    )
                                
                                # 外れ値処理
                                if remove_outliers:
                                    processed_df = preprocessor.remove_outliers(
                                        processed_df, 
                                        method=outlier_method,
                                        contamination=contamination,
                                        z_threshold=z_threshold,
                                        iqr_multiplier=iqr_multiplier,
                                        winsorize_limits=winsorize_limits,
                                        action=action
                                    )
                                
                                # カテゴリ変数エンコーディング
                                if len(preprocessor.categorical_columns) > 0:
                                    if encoding_method == "target" and target_col:
                                        processed_df = preprocessor.encode_categorical(
                                            processed_df, 
                                            method=encoding_method,
                                            target_col=target_col
                                        )
                                    else:
                                        processed_df = preprocessor.encode_categorical(
                                            processed_df, 
                                            method=encoding_method
                                        )
                                
                                # 特徴量スケーリング
                                if scaling_method and len(preprocessor.numerical_columns) > 0:
                                    processed_df = preprocessor.scale_features(
                                        processed_df, 
                                        method=scaling_method
                                    )
                                
                                # 特徴量選択
                                if feature_selection and target_col:
                                    processed_df = preprocessor.select_features(
                                        processed_df, 
                                        target_col=target_col, 
                                        k=k_features
                                    )
                                
                                # 処理履歴に記録
                                import datetime
                                df_before_rows = len(st.session_state['current_df'])
                                df_before_cols = len(st.session_state['current_df'].columns)
                                df_after_rows = len(processed_df)
                                df_after_cols = len(processed_df.columns)
                                
                                # 実行した処理を記録
                                operations_performed = []
                                if missing_strategy != "auto" and missing_strategy != "drop":
                                    operations_performed.append(f"欠損値処理({missing_strategy})")
                                if remove_outliers:
                                    operations_performed.append(f"外れ値処理({outlier_method})")
                                if len(preprocessor.categorical_columns) > 0:
                                    operations_performed.append(f"カテゴリエンコーディング({encoding_method})")
                                if scaling_method:
                                    operations_performed.append(f"スケーリング({scaling_method})")
                                if feature_selection and target_col:
                                    operations_performed.append(f"特徴量選択({k_features}個)")
                                
                                history_entry = {
                                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'operation': '前処理実行',
                                    'method': ', '.join(operations_performed) if operations_performed else '基本処理',
                                    'parameters': {
                                        'missing_strategy': missing_strategy,
                                        'remove_outliers': remove_outliers,
                                        'encoding_method': encoding_method,
                                        'scaling_method': scaling_method if scaling_method else 'なし',
                                        'feature_selection': feature_selection
                                    },
                                    'before': {'rows': df_before_rows, 'columns': df_before_cols},
                                    'after': {'rows': df_after_rows, 'columns': df_after_cols},
                                    'changes': {
                                        'rows_changed': df_after_rows - df_before_rows,
                                        'columns_changed': df_after_cols - df_before_cols
                                    }
                                }
                                st.session_state['processing_history'].append(history_entry)
                                
                                # 処理済みデータをセッション状態に保存
                                st.session_state['current_df'] = processed_df.copy()
                                
                                st.success("✅ 前処理が完了しました！")
                                
                                # 結果を表示（コンパクトに）
                                st.markdown("---")
                                st.subheader("処理結果の概要")
                                
                                # 処理前後の比較をコンパクトに表示
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("処理前の行数", df.shape[0])
                                with col2:
                                    st.metric("処理後の行数", processed_df.shape[0], 
                                             delta=processed_df.shape[0] - df.shape[0])
                                with col3:
                                    st.metric("処理前の列数", df.shape[1])
                                with col4:
                                    st.metric("処理後の列数", processed_df.shape[1],
                                             delta=processed_df.shape[1] - df.shape[1])
                                
                                # データプレビュー（オプション）
                                if st.checkbox("処理後のデータをプレビュー", value=False, key="show_processed_preview"):
                                    st.subheader("処理後のデータ（最初の10行）")
                                    st.dataframe(processed_df.head(10), use_container_width=True)
                                
                                # 記述統計量（コンパクトに表示）
                                if show_statistics:
                                    st.markdown("---")
                                    st.subheader("記述統計量")
                                    
                                    # 基本統計量をコンパクトに表示
                                    num_cols = [col for col in preprocessor.numerical_columns if col in processed_df.columns]
                                    if len(num_cols) > 0:
                                        # 基本統計量のサマリー
                                        summary_stats = processed_df[num_cols].describe().T
                                        summary_stats['欠損値'] = processed_df[num_cols].isnull().sum()
                                        summary_stats['欠損率(%)'] = (processed_df[num_cols].isnull().sum() / len(processed_df) * 100).round(2)
                                        
                                        # 変数が多い場合は最初の20個のみ表示
                                        if len(num_cols) > 20:
                                            st.info(f"⚠️ 変数が{len(num_cols)}個あります。最初の20個のみ表示します。")
                                            st.dataframe(summary_stats.head(20), use_container_width=True)
                                            
                                            if st.checkbox("全変数の統計量を表示", value=False, key="show_all_stats"):
                                                st.dataframe(summary_stats, use_container_width=True)
                                        else:
                                            st.dataframe(summary_stats, use_container_width=True)
                                        
                                        # 詳細統計量（オプション）
                                        if st.checkbox("詳細統計量を表示（コンソール出力）", value=False, key="show_detailed_stats"):
                                            with st.expander("詳細統計量", expanded=False):
                                                preprocessor.describe_statistics(processed_df, include_all=True)
                                    else:
                                        st.info("数値変数が見つかりませんでした。")
                                    
                                    # カテゴリ変数の統計
                                    cat_cols = [col for col in preprocessor.categorical_columns if col in processed_df.columns]
                                    if len(cat_cols) > 0:
                                        st.markdown("**カテゴリ変数の統計**")
                                        cat_stats = []
                                        for col in cat_cols[:10]:  # 最初の10個のみ
                                            cat_stats.append({
                                                '変数名': col,
                                                'ユニーク値数': processed_df[col].nunique(),
                                                '欠損値': processed_df[col].isnull().sum(),
                                                '最頻値': processed_df[col].mode()[0] if len(processed_df[col].mode()) > 0 else 'N/A'
                                            })
                                        if cat_stats:
                                            st.dataframe(pd.DataFrame(cat_stats), use_container_width=True)
                                            if len(cat_cols) > 10:
                                                st.info(f"他{len(cat_cols) - 10}個のカテゴリ変数があります。")
                                
                                # 可視化（オプション）
                                st.markdown("---")
                                st.subheader("データの可視化")
                                
                                if show_visualization:
                                    # 列の識別を確実に実行（可視化前に）
                                    preprocessor.identify_columns(processed_df, categorical_threshold=categorical_threshold)
                                    num_numeric_cols = len([col for col in preprocessor.numerical_columns if col in processed_df.columns])
                                    num_categorical_cols = len([col for col in preprocessor.categorical_columns if col in processed_df.columns])
                                    
                                    # 基本統計量の可視化
                                    
                                    if num_numeric_cols > 0 or num_categorical_cols > 0:
                                        # ボタンを使用してグラフを生成（タブが変わらないように）
                                        col_viz1, col_viz2 = st.columns([3, 1])
                                        with col_viz1:
                                            st.markdown("**データ分布の可視化**")
                                        with col_viz2:
                                            if st.button("グラフを生成", key="btn_data_viz", use_container_width=True):
                                                st.session_state['generate_data_viz'] = True
                                        
                                        # グラフ生成ボタンが押された場合、または既に生成されている場合
                                        if st.session_state.get('generate_data_viz', False):
                                            viz_key = 'data_viz_image_bytes'
                                            if viz_key not in st.session_state:
                                                tmp_plot = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                                                plot_path = tmp_plot.name
                                                tmp_plot.close()
                                                try:
                                                    with st.spinner("データ分布を可視化中..."):
                                                        preprocessor.visualize_data(processed_df, save_path=plot_path)
                                                    if os.path.exists(plot_path) and os.path.getsize(plot_path) > 0:
                                                        with open(plot_path, 'rb') as f:
                                                            st.session_state[viz_key] = f.read()
                                                    else:
                                                        st.warning("⚠️ グラフファイルが生成されませんでした。")
                                                except ValueError as ve:
                                                    st.warning(f"⚠️ {str(ve)}")
                                                except Exception as e:
                                                    st.error(f"❌ グラフの生成中にエラーが発生しました: {str(e)}")
                                                    import traceback
                                                    with st.expander("詳細なエラー情報", expanded=False):
                                                        st.code(traceback.format_exc())
                                                finally:
                                                    try:
                                                        if os.path.exists(plot_path):
                                                            os.remove(plot_path)
                                                    except Exception:
                                                        pass
                                            if viz_key in st.session_state:
                                                st.image(st.session_state[viz_key], caption="データの分布", use_container_width=True)
                                                # グラフを非表示にするボタン
                                                if st.button("グラフを非表示", key="hide_data_viz"):
                                                    st.session_state['generate_data_viz'] = False
                                                    if viz_key in st.session_state:
                                                        del st.session_state[viz_key]
                                    else:
                                        st.info("ℹ️ 可視化する数値変数またはカテゴリ変数が見つかりませんでした。")
                                    
                                    # 相関行列（変数が多い場合は警告）
                                    if num_numeric_cols >= 2:
                                        if num_numeric_cols > 20:
                                            st.warning(f"⚠️ 変数が{num_numeric_cols}個あります。相関行列の表示には時間がかかる場合があります。")
                                        
                                        # ボタンを使用して相関行列を生成（タブが変わらないように）
                                        col_corr1, col_corr2 = st.columns([3, 1])
                                        with col_corr1:
                                            st.markdown("**相関行列の可視化**")
                                        with col_corr2:
                                            if st.button("相関行列を生成", key="btn_corr_matrix", use_container_width=True):
                                                st.session_state['generate_corr_matrix'] = True
                                                # タブ状態を明示的に保持
                                                st.session_state['active_tab'] = "前処理"
                                        
                                        # 相関行列生成ボタンが押された場合、または既に生成されている場合
                                        if st.session_state.get('generate_corr_matrix', False):
                                            corr_key = 'corr_matrix_image_bytes'
                                            if corr_key not in st.session_state:
                                                tmp_corr = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                                                corr_path = tmp_corr.name
                                                tmp_corr.close()
                                                try:
                                                    with st.spinner("相関行列を計算中..."):
                                                        preprocessor.identify_columns(processed_df, categorical_threshold=categorical_threshold)
                                                        preprocessor.visualize_correlation(processed_df, save_path=corr_path)
                                                    if os.path.exists(corr_path) and os.path.getsize(corr_path) > 0:
                                                        with open(corr_path, 'rb') as f:
                                                            st.session_state[corr_key] = f.read()
                                                    else:
                                                        st.warning("⚠️ 相関行列のグラフファイルが生成されませんでした。数値変数が不足している可能性があります。")
                                                except ValueError as ve:
                                                    st.warning(f"⚠️ {str(ve)}")
                                                except Exception as e:
                                                    st.error(f"❌ 相関行列の生成中にエラーが発生しました: {str(e)}")
                                                    import traceback
                                                    with st.expander("詳細なエラー情報", expanded=False):
                                                        st.code(traceback.format_exc())
                                                finally:
                                                    try:
                                                        if os.path.exists(corr_path):
                                                            os.remove(corr_path)
                                                    except Exception:
                                                        pass
                                            
                                            if corr_key in st.session_state:
                                                st.image(st.session_state[corr_key], caption="相関行列", use_container_width=True)
                                                # グラフを非表示にするボタン
                                                if st.button("相関行列を非表示", key="hide_corr_matrix"):
                                                    st.session_state['generate_corr_matrix'] = False
                                                    if corr_key in st.session_state:
                                                        del st.session_state[corr_key]
                                                
                                                # 相関係数の高いペアを表示（オプション）
                                                if st.checkbox("相関係数の高い変数ペアを表示", value=False, key="show_high_corr"):
                                                    num_cols = [col for col in preprocessor.numerical_columns if col in processed_df.columns]
                                                    if len(num_cols) > 1:
                                                        corr_matrix = processed_df[num_cols].corr()
                                                        # 上三角行列のみを取得（重複を避ける）
                                                        corr_pairs = []
                                                        for i in range(len(corr_matrix.columns)):
                                                            for j in range(i+1, len(corr_matrix.columns)):
                                                                corr_val = corr_matrix.iloc[i, j]
                                                                if not np.isnan(corr_val):
                                                                    corr_pairs.append({
                                                                        '変数1': corr_matrix.columns[i],
                                                                        '変数2': corr_matrix.columns[j],
                                                                        '相関係数': corr_val
                                                                    })
                                                        
                                                        if corr_pairs:
                                                            corr_df = pd.DataFrame(corr_pairs)
                                                            corr_df = corr_df.sort_values('相関係数', key=abs, ascending=False)
                                                            st.dataframe(corr_df.head(20), use_container_width=True)
                                else:
                                    st.info("💡 可視化を表示するには、サイドバーの「グラフを表示」にチェックを入れてください。")
                                
                                # 統計検定（オプション）
                                if show_tests:
                                    st.markdown("---")
                                    st.subheader("統計検定")
                                    
                                    # 変数が多い場合の警告
                                    num_numeric_cols = len([col for col in preprocessor.numerical_columns if col in processed_df.columns])
                                    
                                    if num_numeric_cols > 20:
                                        st.warning(f"⚠️ 変数が{num_numeric_cols}個あります。統計検定の実行には時間がかかる場合があります。")
                                    
                                    if st.checkbox("統計検定を実行", value=(num_numeric_cols <= 15), key="execute_statistical_tests"):
                                        with st.spinner("統計検定を実行中..."):
                                            try:
                                                # 検定結果を取得
                                                test_results = preprocessor.statistical_tests(processed_df, alpha=alpha_level)
                                                
                                                if test_results:
                                                    # 各変数の検定結果を表示
                                                    for col, col_results in test_results.items():
                                                        if col in ['levene_test', 'bartlett_test', 'chi_square_test']:
                                                            continue  # これらは後で表示
                                                        
                                                        with st.expander(f"{col} の検定結果", expanded=False):
                                                            # 正規性検定
                                                            if 'shapiro_wilk' in col_results:
                                                                sw = col_results['shapiro_wilk']
                                                                st.markdown("**1. Shapiro-Wilk検定（正規性検定）**")
                                                                col1, col2, col3 = st.columns(3)
                                                                with col1:
                                                                    st.metric("統計量", f"{sw['statistic']:.4f}")
                                                                with col2:
                                                                    st.metric("p値", f"{sw['p_value']:.4f}")
                                                                with col3:
                                                                    result_text = "✅ 正規分布" if sw['is_normal'] else "❌ 非正規分布"
                                                                    st.metric("結果", result_text)
                                                            
                                                            if 'dagostino_pearson' in col_results:
                                                                dp = col_results['dagostino_pearson']
                                                                st.markdown("**2. D'Agostino-Pearson検定（正規性検定）**")
                                                                col1, col2, col3 = st.columns(3)
                                                                with col1:
                                                                    st.metric("統計量", f"{dp['statistic']:.4f}")
                                                                with col2:
                                                                    st.metric("p値", f"{dp['p_value']:.4f}")
                                                                with col3:
                                                                    result_text = "✅ 正規分布" if dp['is_normal'] else "❌ 非正規分布"
                                                                    st.metric("結果", result_text)
                                                            
                                                            if 'anderson_darling' in col_results:
                                                                ad = col_results['anderson_darling']
                                                                st.markdown("**3. Anderson-Darling検定（正規性検定）**")
                                                                st.metric("統計量", f"{ad['statistic']:.4f}")
                                                                st.info("臨界値と比較して判断してください")
                                                            
                                                            # 分布の形状
                                                            if 'skewness' in col_results and 'kurtosis' in col_results:
                                                                st.markdown("**4. 分布の形状**")
                                                                skew = col_results['skewness']
                                                                kurt = col_results['kurtosis']
                                                                
                                                                col1, col2 = st.columns(2)
                                                                with col1:
                                                                    skew_desc = "右に歪む" if skew > 0 else "左に歪む" if skew < 0 else "対称"
                                                                    st.metric("歪度", f"{skew:.4f}", help=f"{skew_desc}")
                                                                with col2:
                                                                    kurt_desc = "尖っている" if kurt > 0 else "平ら" if kurt < 0 else "正規分布に近い"
                                                                    st.metric("尖度", f"{kurt:.4f}", help=f"{kurt_desc}")
                                                    
                                                    # 等分散性検定
                                                    if 'levene_test' in test_results:
                                                        st.markdown("---")
                                                        st.subheader("等分散性検定")
                                                        levene = test_results['levene_test']
                                                        col1, col2, col3 = st.columns(3)
                                                        with col1:
                                                            st.metric("統計量", f"{levene['statistic']:.4f}")
                                                        with col2:
                                                            st.metric("p値", f"{levene['p_value']:.4f}")
                                                        with col3:
                                                            result_text = "✅ 等分散" if levene['equal_variance'] else "❌ 不等分散"
                                                            st.metric("結果", result_text)
                                                        st.info("**Levene検定**: 正規分布でなくても使用可能な等分散性検定")
                                                    
                                                    if 'bartlett_test' in test_results:
                                                        bartlett = test_results['bartlett_test']
                                                        col1, col2, col3 = st.columns(3)
                                                        with col1:
                                                            st.metric("統計量", f"{bartlett['statistic']:.4f}")
                                                        with col2:
                                                            st.metric("p値", f"{bartlett['p_value']:.4f}")
                                                        with col3:
                                                            result_text = "✅ 等分散" if bartlett['equal_variance'] else "❌ 不等分散"
                                                            st.metric("結果", result_text)
                                                        st.info("**Bartlett検定**: 正規分布を仮定した等分散性検定")
                                                    
                                                    # 独立性検定
                                                    if 'chi_square_test' in test_results:
                                                        st.markdown("---")
                                                        st.subheader("🔗 独立性検定（カテゴリ変数）")
                                                        chi2 = test_results['chi_square_test']
                                                        col1, col2, col3, col4 = st.columns(4)
                                                        with col1:
                                                            st.metric("統計量（χ²）", f"{chi2['statistic']:.4f}")
                                                        with col2:
                                                            st.metric("p値", f"{chi2['p_value']:.4f}")
                                                        with col3:
                                                            st.metric("自由度", chi2['degrees_of_freedom'])
                                                        with col4:
                                                            result_text = "✅ 独立" if chi2['independent'] else "❌ 従属"
                                                            st.metric("結果", result_text)
                                                        st.info("**カイ二乗検定**: 2つのカテゴリ変数が独立かどうかを検定")
                                                    
                                                    # 検定結果のサマリー
                                                    st.markdown("---")
                                                    st.subheader("検定結果サマリー")
                                                    
                                                    summary_data = []
                                                    for col_sum, col_results_sum in test_results.items():
                                                        if col_sum in ['levene_test', 'bartlett_test', 'chi_square_test']:
                                                            continue
                                                        
                                                        summary_row = {'変数名': col_sum}
                                                        
                                                        if 'shapiro_wilk' in col_results_sum:
                                                            summary_row['正規性（Shapiro-Wilk）'] = "✅ 正規" if col_results_sum['shapiro_wilk']['is_normal'] else "❌ 非正規"
                                                        if 'dagostino_pearson' in col_results_sum:
                                                            summary_row['正規性（D\'Agostino-Pearson）'] = "✅ 正規" if col_results_sum['dagostino_pearson']['is_normal'] else "❌ 非正規"
                                                        if 'skewness' in col_results_sum:
                                                            summary_row['歪度'] = f"{col_results_sum['skewness']:.3f}"
                                                        if 'kurtosis' in col_results_sum:
                                                            summary_row['尖度'] = f"{col_results_sum['kurtosis']:.3f}"
                                                        
                                                        summary_data.append(summary_row)
                                                    
                                                    if summary_data:
                                                        summary_df = pd.DataFrame(summary_data)
                                                        st.dataframe(summary_df, use_container_width=True)
                                                else:
                                                    st.info("検定結果がありません。数値変数が存在することを確認してください。")
                                            except Exception as e:
                                                st.error(f"統計検定の実行中にエラーが発生しました: {e}")
                                                import traceback
                                                st.code(traceback.format_exc())
                                    else:
                                        st.info("💡 統計検定を実行するには、上記のチェックボックスにチェックを入れてください。")
                                
                                # ダウンロードボタン
                                st.markdown("---")
                                st.subheader("📥 処理済みデータのダウンロード")
                                
                                # CSV形式でダウンロード
                                csv = processed_df.to_csv(index=False, encoding='utf-8-sig')
                                b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
                                href = f'<a href="data:file/csv;base64,{b64}" download="processed_data.csv">📥 CSV形式でダウンロード</a>'
                                st.markdown(href, unsafe_allow_html=True)
                                
                                # Excel形式でダウンロード
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_excel:
                                    excel_path = tmp_excel.name
                                    processed_df.to_excel(excel_path, index=False)
                                    
                                    with open(excel_path, 'rb') as f:
                                        excel_data = f.read()
                                        b64_excel = base64.b64encode(excel_data).decode()
                                    href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="processed_data.xlsx">📥 Excel形式でダウンロード</a>'
                                    st.markdown(href_excel, unsafe_allow_html=True)
                                
                                # セッション状態に保存
                                st.session_state['processed_df'] = processed_df
                                
                            except Exception as e:
                                st.error(f"❌ エラーが発生しました: {str(e)}")
                                st.exception(e)
            
            elif st.session_state['active_tab'] == "高度な機能":
                st.subheader("高度な分析")
                
                analysis_tabs = st.tabs([
                    "重複削除", "特徴量エンジニアリング", 
                    "VIF分析", "クラス不均衡", "データ分割",
                    "高度な診断", "特徴量選択（高度）", "次元削減"
                ])
                
                with analysis_tabs[0]:
                    st.subheader("重複削除")
                    duplicate_method = st.selectbox(
                        "重複検出方法",
                        ["exact (完全一致)", "key (キー列)", "similarity (類似度)"],
                        help="重複の検出方法を選択"
                    )
                    method = duplicate_method.split(" (")[0]
                    
                    if method == "key":
                        key_columns = st.multiselect(
                            "キー列を選択",
                            st.session_state['current_df'].columns.tolist(),
                            help="重複チェックする列を選択"
                        )
                        subset = key_columns if key_columns else None
                    else:
                        subset = None
                    
                    keep_option = st.selectbox(
                        "保持する行",
                        ["first (最初)", "last (最後)", "False (すべて削除)"],
                        help="重複が見つかった場合の処理"
                    )
                    keep = "first" if keep_option.startswith("first") else ("last" if keep_option.startswith("last") else False)
                    
                    if st.button("重複を削除", type="primary"):
                        try:
                            df_before = len(st.session_state['current_df'])
                            df_before_cols = len(st.session_state['current_df'].columns)
                            
                            st.session_state['current_df'] = preprocessor.remove_duplicates(
                                st.session_state['current_df'],
                                subset=subset,
                                keep=keep,
                                method=method
                            )
                            
                            df_after = len(st.session_state['current_df'])
                            df_after_cols = len(st.session_state['current_df'].columns)
                            
                            # 処理履歴に記録
                            import datetime
                            history_entry = {
                                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'operation': '重複削除',
                                'method': method,
                                'parameters': {
                                    'subset': subset if subset else '全列',
                                    'keep': keep
                                },
                                'before': {'rows': df_before, 'columns': df_before_cols},
                                'after': {'rows': df_after, 'columns': df_after_cols},
                                'changes': {
                                    'rows_removed': df_before - df_after,
                                    'columns_changed': df_after_cols - df_before_cols
                                }
                            }
                            st.session_state['processing_history'].append(history_entry)
                            
                            st.success(f"✅ 重複削除完了: {df_before}行 → {df_after}行（{df_before - df_after}行削除）")
                            
                            # 詳細結果を表示
                            with st.expander("処理結果の詳細", expanded=True):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("処理前行数", df_before)
                                with col2:
                                    st.metric("処理後行数", df_after)
                                with col3:
                                    st.metric("削除された行数", df_before - df_after)
                                
                                st.info(f"**処理方法**: {method} | **保持方法**: {keep} | **対象列**: {subset if subset else '全列'}")
                        except Exception as e:
                            st.error(f"エラー: {e}")
                
                with analysis_tabs[1]:
                    st.subheader("特徴量エンジニアリング")
                    
                    create_interactions = st.checkbox("交互作用項を作成", value=False)
                    create_polynomial = st.checkbox("多項式特徴を作成", value=False)
                    create_binning = st.checkbox("ビニング（分割）を実行", value=False)
                    create_spline = st.checkbox("スプライン変換を実行", value=False)
                    
                    if create_spline:
                        n_knots = st.number_input("ノット数", min_value=2, max_value=10, value=3, key="n_knots")
                        spline_degree = st.number_input("スプライン次数", min_value=1, max_value=5, value=3, key="spline_degree")
                    
                    if create_binning:
                        n_bins = st.number_input("ビン数", min_value=2, max_value=20, value=5)
                        binning_method = st.selectbox(
                            "ビニング方法",
                            ["equal_freq (等頻度)", "equal_width (等幅)"]
                        )
                        binning_method = binning_method.split(" (")[0]
                    else:
                        n_bins = 5
                        binning_method = 'equal_freq'
                    
                    if st.button("特徴量エンジニアリングを実行", type="primary"):
                        try:
                            df_before_cols = len(st.session_state['current_df'].columns)
                            
                            st.session_state['current_df'] = preprocessor.feature_engineering(
                                st.session_state['current_df'],
                                interactions=create_interactions,
                                polynomial=create_polynomial,
                                binning=create_binning,
                                n_bins=n_bins,
                                binning_method=binning_method
                            )
                            
                            if create_spline:
                                st.session_state['current_df'] = preprocessor.create_spline_features(
                                    st.session_state['current_df'],
                                    n_knots=n_knots,
                                    degree=spline_degree
                                )
                            
                            df_after_cols = len(st.session_state['current_df'].columns)
                            
                            # 処理履歴に記録
                            import datetime
                            features_created = []
                            if create_interactions:
                                features_created.append("交互作用項")
                            if create_polynomial:
                                features_created.append("多項式特徴")
                            if create_binning:
                                features_created.append(f"ビニング({binning_method}, {n_bins}ビン)")
                            if create_spline:
                                features_created.append(f"スプライン変換({n_knots}ノット, 次数{spline_degree})")
                            
                            history_entry = {
                                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'operation': '特徴量エンジニアリング',
                                'method': ', '.join(features_created) if features_created else 'なし',
                                'parameters': {
                                    'interactions': create_interactions,
                                    'polynomial': create_polynomial,
                                    'binning': create_binning,
                                    'spline': create_spline
                                },
                                'before': {'columns': df_before_cols},
                                'after': {'columns': df_after_cols},
                                'changes': {
                                    'columns_added': df_after_cols - df_before_cols
                                }
                            }
                            st.session_state['processing_history'].append(history_entry)
                            
                            st.success(f"✅ 特徴量エンジニアリングが完了しました（{df_after_cols - df_before_cols}個の特徴量を追加）")
                            
                            # 詳細結果を表示
                            with st.expander("処理結果の詳細", expanded=True):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("処理前列数", df_before_cols)
                                with col2:
                                    st.metric("処理後列数", df_after_cols)
                                with col3:
                                    st.metric("追加された列数", df_after_cols - df_before_cols)
                                
                                st.info(f"**作成された特徴量**: {', '.join(features_created) if features_created else 'なし'}")
                        except Exception as e:
                            st.error(f"エラー: {e}")
                    
                    # WOE計算
                    st.markdown("---")
                    st.subheader("WOE (Weight of Evidence) 計算")
                    st.info("WOEは信用スコアリングなどで使用される指標です。")
                    
                    if len(st.session_state['current_df'].columns) > 0:
                        woe_feature_col = st.selectbox(
                            "特徴量列を選択",
                            ["なし"] + list(st.session_state['current_df'].columns),
                            key="woe_feature"
                        )
                        woe_target_col = st.selectbox(
                            "ターゲット列を選択",
                            ["なし"] + list(st.session_state['current_df'].columns),
                            key="woe_target"
                        )
                        
                        if woe_feature_col != "なし" and woe_target_col != "なし":
                            woe_n_bins = st.number_input("ビン数", min_value=2, max_value=20, value=5, key="woe_bins")
                            
                            if st.button("WOEを計算", type="primary", key="woe_calc"):
                                try:
                                    woe_results = preprocessor.calculate_woe(
                                        st.session_state['current_df'],
                                        feature_col=woe_feature_col,
                                        target_col=woe_target_col,
                                        n_bins=woe_n_bins
                                    )
                                    if len(woe_results) > 0:
                                        st.dataframe(woe_results, use_container_width=True)
                                    else:
                                        st.info("WOE計算に必要なデータが不足しています")
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                
                with analysis_tabs[2]:
                    st.subheader("VIF分析（共線性の検出）")
                    st.info("VIF (Variance Inflation Factor) は共線性を検出する指標です。VIF > 10 の場合は共線性が疑われます。")
                    
                    vif_threshold = st.slider("VIF閾値", min_value=5.0, max_value=20.0, value=10.0, step=0.5)
                    
                    if st.button("VIFを計算", type="primary"):
                        try:
                            with st.spinner("VIFを計算中..."):
                                # 列の識別を先に実行
                                preprocessor.identify_columns(st.session_state['current_df'], categorical_threshold=categorical_threshold)
                                
                                vif_results = preprocessor.calculate_vif(
                                    st.session_state['current_df'],
                                    threshold=vif_threshold
                                )
                                
                                if len(vif_results) > 0:
                                    st.dataframe(vif_results, use_container_width=True)
                                    
                                    high_vif = vif_results[vif_results["共線性あり"]]
                                    if len(high_vif) > 0:
                                        st.warning(f"⚠️ {len(high_vif)}個の変数で共線性が検出されました: {', '.join(high_vif['変数'].tolist())}")
                                        
                                        # 処理履歴に記録
                                        import datetime
                                        history_entry = {
                                            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                            'operation': 'VIF分析',
                                            'method': 'VIF計算',
                                            'parameters': {
                                                'threshold': vif_threshold
                                            },
                                            'before': {'columns': len(st.session_state['current_df'].columns)},
                                            'after': {'columns': len(st.session_state['current_df'].columns)},
                                            'changes': {
                                                'high_vif_count': len(high_vif),
                                                'high_vif_vars': high_vif['変数'].tolist() if len(high_vif) > 0 else []
                                            }
                                        }
                                        st.session_state['processing_history'].append(history_entry)
                                    else:
                                        st.success("✅ 共線性の問題は検出されませんでした")
                                        
                                        # 処理履歴に記録
                                        import datetime
                                        history_entry = {
                                            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                            'operation': 'VIF分析',
                                            'method': 'VIF計算',
                                            'parameters': {
                                                'threshold': vif_threshold
                                            },
                                            'before': {'columns': len(st.session_state['current_df'].columns)},
                                            'after': {'columns': len(st.session_state['current_df'].columns)},
                                            'changes': {
                                                'high_vif_count': 0
                                            }
                                        }
                                        st.session_state['processing_history'].append(history_entry)
                                else:
                                    st.info("VIF計算に必要な数値変数が不足しています")
                        except Exception as e:
                            st.error(f"❌ エラー: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                
                with analysis_tabs[3]:
                    st.subheader("クラス不均衡処理")
                    st.info("分類問題でクラス不均衡を処理します。")
                    
                    if len(st.session_state['current_df'].columns) > 0:
                        target_col_imbalance = st.selectbox(
                            "ターゲット列を選択",
                            ["なし"] + list(st.session_state['current_df'].columns),
                            key="target_imbalance"
                        )
                        
                        if target_col_imbalance != "なし":
                            imbalance_method = st.selectbox(
                                "サンプリング方法",
                                ["smote", "adasyn", "random_oversample", "random_undersample"],
                                help="SMOTE: 合成サンプル生成, ADASYN: 適応的SMOTE, random_oversample: ランダムオーバーサンプリング, random_undersample: ランダムアンダーサンプリング"
                            )
                            
                            if st.button("クラス不均衡を処理", type="primary"):
                                try:
                                    df_before = len(st.session_state['current_df'])
                                    df_before_cols = len(st.session_state['current_df'].columns)
                                    
                                    st.session_state['current_df'] = preprocessor.handle_imbalance(
                                        st.session_state['current_df'],
                                        target_col=target_col_imbalance,
                                        method=imbalance_method
                                    )
                                    
                                    df_after = len(st.session_state['current_df'])
                                    df_after_cols = len(st.session_state['current_df'].columns)
                                    
                                    # 処理履歴に記録
                                    import datetime
                                    history_entry = {
                                        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'operation': 'クラス不均衡処理',
                                        'method': imbalance_method,
                                        'parameters': {
                                            'target_col': target_col_imbalance,
                                            'method': imbalance_method
                                        },
                                        'before': {'rows': df_before, 'columns': df_before_cols},
                                        'after': {'rows': df_after, 'columns': df_after_cols},
                                        'changes': {
                                            'rows_changed': df_after - df_before
                                        }
                                    }
                                    st.session_state['processing_history'].append(history_entry)
                                    
                                    st.success(f"✅ クラス不均衡処理完了: {df_before}行 → {df_after}行")
                                    
                                    # 詳細結果を表示
                                    with st.expander("処理結果の詳細", expanded=True):
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("処理前行数", df_before)
                                        with col2:
                                            st.metric("処理後行数", df_after)
                                        with col3:
                                            st.metric("行数の変化", df_after - df_before)
                                        
                                        st.info(f"**処理方法**: {imbalance_method} | **ターゲット列**: {target_col_imbalance}")
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                
                with analysis_tabs[4]:
                    st.subheader("データ分割")
                    st.info("学習データとテストデータに分割、またはCV用に分割します。")
                    
                    if len(st.session_state['current_df'].columns) > 0:
                        target_col_split = st.selectbox(
                            "ターゲット列を選択",
                            ["なし"] + list(st.session_state['current_df'].columns),
                            key="target_split"
                        )
                        
                        if target_col_split != "なし":
                            split_method = st.selectbox(
                                "分割方法",
                                ["random (ランダム)", "stratified (層化)", "timeseries (時系列)", "group (グループ)"],
                                help="データの分割方法を選択"
                            )
                            method = split_method.split(" (")[0]
                            
                            if method == "random":
                                test_size = st.slider("テストデータの割合", min_value=0.1, max_value=0.5, value=0.2, step=0.05)
                                stratify = st.checkbox("層化分割を使用", value=True)
                            elif method in ["timeseries", "group", "stratified"]:
                                n_splits = st.number_input("CV分割数", min_value=2, max_value=10, value=5)
                                test_size = 0.2
                                stratify = True
                            else:
                                test_size = 0.2
                                n_splits = 5
                                stratify = True
                            
                            if method == "group":
                                group_col = st.selectbox(
                                    "グループ列を選択",
                                    ["なし"] + list(st.session_state['current_df'].columns),
                                    key="group_col"
                                )
                                groups = group_col if group_col != "なし" else None
                            else:
                                groups = None
                            
                            if st.button("データを分割", type="primary"):
                                try:
                                    df_before = len(st.session_state['current_df'])
                                    
                                    split_result = preprocessor.split_data(
                                        st.session_state['current_df'],
                                        target_col=target_col_split,
                                        test_size=test_size,
                                        method=method,
                                        n_splits=n_splits if 'n_splits' in locals() else 5,
                                        groups=groups,
                                        stratify=stratify if 'stratify' in locals() else True
                                    )
                                    
                                    # 処理履歴に記録
                                    import datetime
                                    if split_result:
                                        if method == "random":
                                            train_size = len(split_result['X_train'])
                                            test_size_actual = len(split_result['X_test'])
                                            
                                            history_entry = {
                                                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                'operation': 'データ分割',
                                                'method': method,
                                                'parameters': {
                                                    'target_col': target_col_split,
                                                    'method': method,
                                                    'test_size': test_size,
                                                    'stratify': stratify if 'stratify' in locals() else True
                                                },
                                                'before': {'rows': df_before},
                                                'after': {
                                                    'train_rows': train_size,
                                                    'test_rows': test_size_actual
                                                },
                                                'changes': {
                                                    'train_size': train_size,
                                                    'test_size': test_size_actual
                                                }
                                            }
                                            st.session_state['processing_history'].append(history_entry)
                                            
                                            st.success(f"✅ データ分割完了: 学習データ {train_size}行, テストデータ {test_size_actual}行")
                                            
                                            # 詳細結果を表示
                                            with st.expander("処理結果の詳細", expanded=True):
                                                col1, col2, col3 = st.columns(3)
                                                with col1:
                                                    st.metric("元のデータ行数", df_before)
                                                with col2:
                                                    st.metric("学習データ行数", train_size)
                                                with col3:
                                                    st.metric("テストデータ行数", test_size_actual)
                                            
                                            st.session_state['split_result'] = split_result
                                        else:
                                            n_folds = len(split_result['splits'])
                                            
                                            history_entry = {
                                                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                'operation': 'データ分割（CV）',
                                                'method': method,
                                                'parameters': {
                                                    'target_col': target_col_split,
                                                    'method': method,
                                                    'n_splits': n_splits if 'n_splits' in locals() else 5
                                                },
                                                'before': {'rows': df_before},
                                                'after': {'n_folds': n_folds},
                                                'changes': {
                                                    'n_folds': n_folds
                                                }
                                            }
                                            st.session_state['processing_history'].append(history_entry)
                                            
                                            st.success(f"✅ CV分割完了: {n_folds}個のfold")
                                            
                                            # 詳細結果を表示
                                            with st.expander("処理結果の詳細", expanded=True):
                                                st.metric("CV分割数", n_folds)
                                                st.info(f"**分割方法**: {method} | **ターゲット列**: {target_col_split}")
                                            
                                            st.session_state['split_result'] = split_result
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                
                with analysis_tabs[5]:
                    st.subheader("高度な診断")
                    
                    diag_tabs = st.tabs([
                        "条件数・相関クラスタリング", "欠損パターン診断", "異常値ルールチェック", "高度な外れ値検出"
                    ])
                    
                    with diag_tabs[0]:
                        st.subheader("条件数と相関クラスタリング")
                        
                        if st.button("条件数を計算", type="primary", key="calc_cond"):
                            try:
                                cond_num = preprocessor.calculate_condition_number(st.session_state['current_df'])
                                if cond_num is not None:
                                    st.metric("条件数", f"{cond_num:.2f}")
                                    if cond_num > 30:
                                        st.warning("⚠️ 条件数が高いです（>30）。共線性の問題が疑われます。")
                                    elif cond_num > 10:
                                        st.info("条件数が中程度です（10-30）。注意が必要です。")
                                    else:
                                        st.success("✅ 条件数は正常範囲です（<10）。")
                            except Exception as e:
                                st.error(f"エラー: {e}")
                        
                        if st.button("相関クラスタリングを実行", type="primary", key="cluster_corr"):
                            try:
                                clusters = preprocessor.cluster_correlations(st.session_state['current_df'])
                                if clusters:
                                    st.success(f"✅ {len(clusters)}個のクラスタを検出しました")
                                    for cluster_id, cols in clusters.items():
                                        with st.expander(f"クラスタ {cluster_id} ({len(cols)}個の変数)"):
                                            st.write(cols)
                                else:
                                    st.info("クラスタが見つかりませんでした")
                            except Exception as e:
                                st.error(f"エラー: {e}")
                    
                    with diag_tabs[1]:
                        st.subheader("欠損パターン診断（MCAR/MAR/MNAR）")
                        
                        if st.button("欠損パターンを診断", type="primary", key="diag_missing"):
                            try:
                                results = preprocessor.diagnose_missing_patterns(st.session_state['current_df'])
                                
                                if results['suspected_type']:
                                    st.subheader("診断結果")
                                    for col, pattern_type in results['suspected_type'].items():
                                        st.write(f"**{col}**: {pattern_type}")
                                    
                                    st.info("""
                                    **MCAR (Missing Completely At Random)**: 欠損が完全にランダム
                                    **MAR (Missing At Random)**: 他の観測変数で説明可能
                                    **MNAR (Missing Not At Random)**: 欠損自体が情報を持つ
                                    """)
                                else:
                                    st.info("欠損値が見つかりませんでした")
                            except Exception as e:
                                st.error(f"エラー: {e}")
                    
                    with diag_tabs[2]:
                        st.subheader("異常値のルールベースチェック")
                        st.info("業務ルールに基づく異常値を検出します（例: 年齢が負、売上が極端など）")
                        
                        rule_col = st.selectbox("チェックする列を選択", st.session_state['current_df'].columns, key="rule_col")
                        
                        rule_type = st.selectbox("ルールタイプ", ["範囲チェック", "許可値チェック"], key="rule_type")
                        
                        if rule_type == "範囲チェック":
                            # 数値列かどうかをチェック
                            is_numeric = pd.api.types.is_numeric_dtype(st.session_state['current_df'][rule_col])
                            
                            if is_numeric:
                                min_val = st.number_input("最小値", value=float(st.session_state['current_df'][rule_col].min()), key="rule_min")
                                max_val = st.number_input("最大値", value=float(st.session_state['current_df'][rule_col].max()), key="rule_max")
                            else:
                                st.warning("⚠️ 範囲チェックは数値列のみ使用できます。許可値チェックを使用してください。")
                                min_val = None
                                max_val = None
                            
                            if st.button("異常値を検出", type="primary", key="detect_anomalies"):
                                try:
                                    if min_val is not None and max_val is not None:
                                        rules = {rule_col: {'min': min_val, 'max': max_val}}
                                        anomalies = preprocessor.rule_based_anomaly_detection(st.session_state['current_df'], rules)
                                        if len(anomalies) > 0:
                                            st.warning(f"⚠️ {len(anomalies)}個の異常値を検出しました")
                                            st.dataframe(anomalies, use_container_width=True)
                                        else:
                                            st.success("✅ 異常値は検出されませんでした")
                                    else:
                                        st.warning("⚠️ 数値列を選択してください")
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                        else:
                            allowed_values_str = st.text_input("許可値（カンマ区切り）", key="allowed_values")
                            
                            if st.button("異常値を検出", type="primary", key="detect_anomalies_allowed") and allowed_values_str:
                                try:
                                    allowed_values = [v.strip() for v in allowed_values_str.split(',')]
                                    # 数値に変換できる場合は数値として扱う
                                    try:
                                        allowed_values = [float(v) if '.' in v else int(v) for v in allowed_values]
                                    except:
                                        pass
                                    
                                    rules = {rule_col: {'allowed_values': allowed_values}}
                                    anomalies = preprocessor.rule_based_anomaly_detection(st.session_state['current_df'], rules)
                                    if len(anomalies) > 0:
                                        st.warning(f"⚠️ {len(anomalies)}個の異常値を検出しました")
                                        st.dataframe(anomalies, use_container_width=True)
                                    else:
                                        st.success("✅ 異常値は検出されませんでした")
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                    
                    with diag_tabs[3]:
                        st.subheader("高度な外れ値検出（One-Class SVM、LOF）")
                        
                        advanced_outlier_method = st.selectbox(
                            "検出方法",
                            ["one_class_svm", "lof"],
                            help="One-Class SVM: サポートベクターマシン、LOF: Local Outlier Factor",
                            key="advanced_outlier_method"
                        )
                        
                        contamination = st.slider("外れ値の割合", min_value=0.01, max_value=0.5, value=0.1, step=0.01, key="advanced_contamination")
                        action = st.radio("処理方法", ["削除", "クリップ"], horizontal=True, key="advanced_action")
                        action = 'remove' if action == "削除" else 'clip'
                        
                        if st.button("高度な外れ値検出を実行", type="primary", key="advanced_outlier_exec"):
                            try:
                                df_before = len(st.session_state['current_df'])
                                st.session_state['current_df'] = preprocessor.remove_outliers_advanced(
                                    st.session_state['current_df'],
                                    method=advanced_outlier_method,
                                    contamination=contamination,
                                    action=action
                                )
                                df_after = len(st.session_state['current_df'])
                                
                                # 処理履歴に記録
                                import datetime
                                history_entry = {
                                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'operation': '高度な外れ値検出',
                                    'method': advanced_outlier_method,
                                    'parameters': {
                                        'contamination': contamination,
                                        'action': action
                                    },
                                    'before': {'rows': df_before},
                                    'after': {'rows': df_after},
                                    'changes': {
                                        'rows_removed': df_before - df_after
                                    }
                                }
                                st.session_state['processing_history'].append(history_entry)
                                
                                st.success(f"✅ 外れ値検出完了: {df_before}行 → {df_after}行")
                                
                                # 詳細結果を表示
                                with st.expander("処理結果の詳細", expanded=True):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("処理前行数", df_before)
                                    with col2:
                                        st.metric("処理後行数", df_after)
                                    with col3:
                                        st.metric("削除された行数", df_before - df_after)
                                    
                                    st.info(f"**検出方法**: {advanced_outlier_method} | **処理方法**: {action} | **外れ値割合**: {contamination}")
                                # st.rerun()を削除（ページがリロードされないように）
                            except Exception as e:
                                st.error(f"エラー: {e}")
                
                with analysis_tabs[6]:
                    st.subheader("特徴量選択（高度）")
                    
                    if len(st.session_state['current_df'].columns) > 0:
                        target_col_feature = st.selectbox(
                            "ターゲット列を選択",
                            ["なし"] + list(st.session_state['current_df'].columns),
                            key="target_feature"
                        )
                        
                        if target_col_feature != "なし":
                            feature_selection_method = st.selectbox(
                                "特徴量選択方法",
                                ["mutual_info (相互情報量)", "rfe (RFE)"],
                                help="相互情報量: フィルタ法、RFE: ラッパー法",
                                key="feature_selection_method"
                            )
                            
                            k_features_advanced = st.number_input(
                                "選択する特徴量数",
                                min_value=1,
                                max_value=50,
                                value=10,
                                key="k_features_advanced"
                            )
                            
                            if st.button("特徴量選択を実行", type="primary", key="feature_selection_exec"):
                                try:
                                    with st.spinner("特徴量選択を実行中..."):
                                        method = feature_selection_method.split(" (")[0]
                                        
                                        df_before_cols = len(st.session_state['current_df'].columns)
                                        df_before_rows = len(st.session_state['current_df'])
                                        
                                        if method == "mutual_info":
                                            processed_df = preprocessor.select_features_mutual_info(
                                                st.session_state['current_df'],
                                                target_col=target_col_feature,
                                                k=k_features_advanced
                                            )
                                        elif method == "rfe":
                                            processed_df = preprocessor.select_features_rfe(
                                                st.session_state['current_df'],
                                                target_col=target_col_feature,
                                                n_features_to_select=k_features_advanced
                                            )
                                        else:
                                            processed_df = st.session_state['current_df'].copy()
                                        
                                        df_after_cols = len(processed_df.columns)
                                        df_after_rows = len(processed_df)
                                        
                                        # データを更新
                                        st.session_state['current_df'] = processed_df.copy()
                                        
                                        # 処理履歴に記録
                                        import datetime
                                        selected_features = getattr(preprocessor, 'selected_features', [])
                                        
                                        history_entry = {
                                            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                            'operation': '特徴量選択（高度）',
                                            'method': method,
                                            'parameters': {
                                                'target_col': target_col_feature,
                                                'method': method,
                                                'k_features': k_features_advanced
                                            },
                                            'before': {'rows': df_before_rows, 'columns': df_before_cols},
                                            'after': {'rows': df_after_rows, 'columns': df_after_cols},
                                            'changes': {
                                                'columns_removed': df_before_cols - df_after_cols,
                                                'columns_changed': df_after_cols - df_before_cols
                                            }
                                        }
                                        st.session_state['processing_history'].append(history_entry)
                                        
                                        st.success(f"✅ 特徴量選択完了: {df_before_cols}列 → {df_after_cols}列（{df_before_cols - df_after_cols}列削除）")
                                        
                                        # 詳細結果を表示
                                        with st.expander("処理結果の詳細", expanded=True):
                                            col1, col2, col3, col4 = st.columns(4)
                                            with col1:
                                                st.metric("処理前列数", df_before_cols)
                                            with col2:
                                                st.metric("処理後列数", df_after_cols)
                                            with col3:
                                                st.metric("削除された列数", df_before_cols - df_after_cols)
                                            with col4:
                                                st.metric("選択された特徴量数", len(selected_features) if selected_features else df_after_cols)
                                            
                                            st.info(f"**選択方法**: {method} | **ターゲット列**: {target_col_feature} | **選択数**: {k_features_advanced}")
                                            
                                            # 選択された特徴量を表示
                                            if selected_features:
                                                st.markdown("**選択された特徴量:**")
                                                st.write(", ".join(selected_features[:20]))
                                                if len(selected_features) > 20:
                                                    st.write(f"... 他{len(selected_features) - 20}個")
                                            else:
                                                st.markdown("**残った列:**")
                                                st.write(", ".join(processed_df.columns.tolist()[:20]))
                                                if len(processed_df.columns) > 20:
                                                    st.write(f"... 他{len(processed_df.columns) - 20}個")
                                        
                                        # st.rerun()を削除（ページがリロードされないように）
                                except Exception as e:
                                    st.error(f"❌ エラー: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                
                with analysis_tabs[7]:
                    st.subheader("次元削減")
                    st.info("データの次元数を削減します。PCA、MCA、UMAP、t-SNEに対応しています。")
                    
                    # 列の識別を先に実行
                    preprocessor.identify_columns(st.session_state['current_df'], categorical_threshold=categorical_threshold)
                    
                    num_cols = [col for col in preprocessor.numerical_columns if col in st.session_state['current_df'].columns]
                    
                    if len(num_cols) < 2:
                        st.warning("⚠️ 次元削減には少なくとも2つの数値変数が必要です。")
                    else:
                        st.info(f"処理対象: {len(num_cols)}個の数値変数")
                        
                        dim_reduction_method = st.selectbox(
                            "次元削減方法",
                            ["pca", "mca", "umap", "tsne"],
                            help="PCA: 主成分分析、MCA: 多重対応分析、UMAP: 非線形次元削減、t-SNE: 可視化用",
                            key="dim_reduction_method"
                        )
                        
                        n_components = st.number_input(
                            "削減後の次元数",
                            min_value=2,
                            max_value=min(10, len(num_cols)),
                            value=min(2, len(num_cols)),
                            help=f"元の次元数: {len(num_cols)}",
                            key="n_components"
                        )
                        
                        if st.button("次元削減を実行", type="primary", key="dim_reduction_exec"):
                            try:
                                with st.spinner("次元削減を実行中..."):
                                    df_before_cols = len(st.session_state['current_df'].columns)
                                    df_before_rows = len(st.session_state['current_df'])
                                    
                                    # 次元削減を実行
                                    processed_df = preprocessor.reduce_dimensions(
                                        st.session_state['current_df'],
                                        method=dim_reduction_method,
                                        n_components=n_components
                                    )
                                    
                                    df_after_cols = len(processed_df.columns)
                                    df_after_rows = len(processed_df)
                                    
                                    # データを更新
                                    st.session_state['current_df'] = processed_df.copy()
                                    
                                    # 処理履歴に記録
                                    import datetime
                                    history_entry = {
                                        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'operation': '次元削減',
                                        'method': dim_reduction_method.upper(),
                                        'parameters': {
                                            'method': dim_reduction_method,
                                            'n_components': n_components,
                                            'original_dimensions': len(num_cols)
                                        },
                                        'before': {'rows': df_before_rows, 'columns': df_before_cols},
                                        'after': {'rows': df_after_rows, 'columns': df_after_cols},
                                        'changes': {
                                            'columns_added': df_after_cols - df_before_cols,
                                            'columns_changed': df_after_cols - df_before_cols
                                        }
                                    }
                                    st.session_state['processing_history'].append(history_entry)
                                    
                                    st.success(f"✅ 次元削減完了: {dim_reduction_method.upper()}で{len(num_cols)}次元 → {n_components}次元に削減")
                                    
                                    # 詳細結果を表示
                                    with st.expander("処理結果の詳細", expanded=True):
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("元の次元数", len(num_cols))
                                        with col2:
                                            st.metric("削減後の次元数", n_components)
                                        with col3:
                                            st.metric("処理前列数", df_before_cols)
                                        with col4:
                                            st.metric("処理後列数", df_after_cols)
                                        
                                        st.info(f"**次元削減方法**: {dim_reduction_method.upper()} | **削減後の次元数**: {n_components}")
                                        
                                        # 新しい列を表示
                                        new_cols = [col for col in processed_df.columns if col not in st.session_state.get('original_df', processed_df).columns]
                                        if new_cols:
                                            st.markdown("**新しく作成された列:**")
                                            st.write(", ".join(new_cols[:10]))
                                            if len(new_cols) > 10:
                                                st.write(f"... 他{len(new_cols) - 10}個")
                                        
                                        # データプレビュー
                                        if st.checkbox("処理後のデータをプレビュー", value=False, key="preview_dim_reduced"):
                                            st.dataframe(processed_df.head(10), use_container_width=True)
                                    
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ エラー: {e}")
                                import traceback
                                st.code(traceback.format_exc())
                                if dim_reduction_method in ['umap', 'tsne']:
                                    st.info("💡 注意: UMAP/t-SNEを使用する場合は `pip install umap-learn` が必要です。")
            
            elif st.session_state['active_tab'] == "履歴":
                st.subheader("処理履歴（詳細）")
                st.info("実行されたすべての処理の詳細な履歴を表示します。")
                
                if len(st.session_state.get('processing_history', [])) == 0:
                    st.info("まだ処理履歴がありません。処理を実行すると、ここに履歴が表示されます。")
                else:
                    # 統計情報を先に表示
                    st.markdown("---")
                    st.subheader("処理統計")
                    total_operations = len(st.session_state['processing_history'])
                    operation_counts = {}
                    for entry in st.session_state['processing_history']:
                        op = entry['operation']
                        operation_counts[op] = operation_counts.get(op, 0) + 1
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("総処理回数", total_operations)
                    with col2:
                        st.metric("処理種類数", len(operation_counts))
                    with col3:
                        most_common = max(operation_counts.items(), key=lambda x: x[1]) if operation_counts else ('なし', 0)
                        st.metric("最も多い処理", f"{most_common[0]}")
                    with col4:
                        if st.button("履歴をクリア", use_container_width=True):
                            st.session_state['processing_history'] = []
                            st.success("✅ 処理履歴をクリアしました")
                            st.rerun()
                    
                    # 処理種類別の集計
                    if operation_counts:
                        st.write("**処理種類別の集計**:")
                        cols = st.columns(min(len(operation_counts), 4))
                        for idx, (op, count) in enumerate(sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)):
                            with cols[idx % 4]:
                                st.metric(op, f"{count}回")
                    
                    st.markdown("---")
                    st.subheader("処理履歴一覧")
                    
                    # フィルタリング
                    filter_option = st.selectbox(
                        "フィルタ",
                        ["すべて", "前処理実行", "重複削除", "特徴量エンジニアリング", "クラス不均衡処理", "データ分割"],
                        key="history_filter"
                    )
                    
                    # 処理履歴を時系列で表示（新しい順）
                    history = st.session_state['processing_history'][::-1]  # 新しい順
                    
                    filtered_history = history
                    if filter_option != "すべて":
                        filtered_history = [h for h in history if h['operation'] == filter_option]
                    
                    if len(filtered_history) == 0:
                        st.info("該当する処理履歴がありません。")
                    else:
                        for idx, entry in enumerate(filtered_history):
                            # コンパクトな表示形式
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
                            
                            # 処理前後の情報
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
                            
                            with st.expander(f"🔹 {entry['operation']} - {entry['timestamp']}", expanded=(idx < 3)):
                                # コンパクトな表示
                                st.markdown(f"""
                                **処理方法**: {entry.get('method', 'N/A')}  
                                **変更**: {changes_str}  
                                **データ**: {', '.join(before_info)} → {', '.join(after_info)}
                                """)
                                
                                # 詳細情報
                                if 'parameters' in entry and entry['parameters']:
                                    st.markdown("**詳細パラメータ**:")
                                    param_text = "\n".join([f"- **{key}**: {value}" for key, value in entry['parameters'].items()])
                                    st.markdown(param_text)
        
        finally:
            # 一時ファイルを削除
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    else:
        st.info("👈 左側のサイドバーからデータファイルをアップロードしてください")
        
        # 使用例を表示
        with st.expander("使用例とサンプルデータ"):
            st.markdown("""
            ### サンプルデータの作成方法
            
            以下のような形式のCSVファイルを準備してください：
            
            ```csv
            年齢,収入,都市,教育,性別,経験年数,ターゲット
            25,50000,東京,学士,1,3,1
            30,60000,大阪,修士,0,5,0
            ...
            ```
            
            ### 推奨される前処理の流れ
            
            1. **欠損値処理**: まずは "auto" を試してみてください
            2. **外れ値除去**: データに外れ値が多そうな場合は有効化
            3. **カテゴリ変数エンコーディング**: "auto" で自動選択
            4. **特徴量スケーリング**: 機械学習を使用する場合は "standard" を推奨
            5. **特徴量選択**: 変数が多い場合に有効化
            
            ### よくある質問
            
            **Q: どの前処理を選べばいいですか？**  
            A: まずはデフォルト設定（auto）で試してみてください。結果を見ながら調整します。
            
            **Q: エラーが発生しました**  
            A: ファイル形式が正しいか確認してください。CSVファイルはカンマ区切りである必要があります。
            
            **Q: 処理に時間がかかります**  
            A: データサイズが大きい場合、処理に時間がかかることがあります。しばらくお待ちください。
            """)


if __name__ == "__main__":
    main()


import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
from data_preprocessor import DataPreprocessor
import base64
from ui_components import render_header, render_help, render_recent_history

LARGE_FILE_MB = 50
LARGE_ROW_THRESHOLD = 200_000
LARGE_MEMORY_MB = 200

def format_mb(value_mb):
    if value_mb is None:
        return "N/A"
    return f"{value_mb:.1f} MB"

def estimate_df_memory_mb(df):
    try:
        return df.memory_usage(deep=True).sum() / (1024 ** 2)
    except Exception:
        return None

def is_large_dataset(df, memory_mb=None):
    if df is None:
        return False
    if memory_mb is None:
        memory_mb = estimate_df_memory_mb(df)
    return len(df) >= LARGE_ROW_THRESHOLD or (memory_mb is not None and memory_mb >= LARGE_MEMORY_MB)

@st.cache_data(show_spinner=False)
def load_data_cached(file_path, encoding=None, auto_detect_encoding=True, auto_detect_structure=True, **kwargs):
    preprocessor = DataPreprocessor()
    return preprocessor.load_data(
        file_path,
        encoding=encoding,
        auto_detect_encoding=auto_detect_encoding,
        auto_detect_structure=auto_detect_structure,
        **kwargs
    )

st.set_page_config(
    page_title="データ前処理ツール",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

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
        color:
        border-bottom: 3px solid
        padding-bottom: 0.5rem;
    }
    h2 {
        color:
        border-bottom: 2px solid
        padding-bottom: 0.3rem;
        margin-top: 1.5rem;
    }
    h3 {
        color:
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color:
        border: 1px solid
        margin: 1rem 0;
    }
    .info-card {
        background: linear-gradient(135deg,
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background:
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid
        margin: 0.5rem 0;
    }
    [data-testid="stSidebar"] {
        background-color:
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

                                        st.markdown("---")
                                        st.markdown("
                                        csv = woe_results.to_csv(index=False, encoding='utf-8-sig')
                                        b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
                                        href = f'<a href="data:file/csv;base64,{b64}" download="woe_results.csv">📥 WOE計算結果をCSV形式でダウンロード</a>'
                                        st.markdown(href, unsafe_allow_html=True)
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
                                    else:
                                        st.success("✅ 共線性の問題は検出されませんでした")

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
                                            'high_vif_count': len(high_vif) if len(high_vif) > 0 else 0,
                                            'high_vif_vars': high_vif['変数'].tolist() if len(high_vif) > 0 else []
                                        }
                                    }
                                    st.session_state['processing_history'].append(history_entry)

                                    st.markdown("---")
                                    st.markdown("
                                    csv = vif_results.to_csv(index=False, encoding='utf-8-sig')
                                    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
                                    href = f'<a href="data:file/csv;base64,{b64}" download="vif_analysis_results.csv">📥 VIF分析結果をCSV形式でダウンロード</a>'
                                    st.markdown(href, unsafe_allow_html=True)
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

                                            with st.expander("処理結果の詳細", expanded=True):
                                                col1, col2, col3 = st.columns(3)
                                                with col1:
                                                    st.metric("元のデータ行数", df_before)
                                                with col2:
                                                    st.metric("学習データ行数", train_size)
                                                with col3:
                                                    st.metric("テストデータ行数", test_size_actual)

                                            st.session_state['split_result'] = split_result

                                            st.markdown("---")
                                            st.markdown("

                                            train_csv = split_result['X_train'].to_csv(index=False, encoding='utf-8-sig')
                                            train_b64 = base64.b64encode(train_csv.encode('utf-8-sig')).decode()
                                            train_href = f'<a href="data:file/csv;base64,{train_b64}" download="train_data.csv">📥 学習データ（CSV）</a>'
                                            st.markdown(train_href, unsafe_allow_html=True)

                                            test_csv = split_result['X_test'].to_csv(index=False, encoding='utf-8-sig')
                                            test_b64 = base64.b64encode(test_csv.encode('utf-8-sig')).decode()
                                            test_href = f'<a href="data:file/csv;base64,{test_b64}" download="test_data.csv">📥 テストデータ（CSV）</a>'
                                            st.markdown(test_href, unsafe_allow_html=True)
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

                                if 'parameters' in entry and entry['parameters']:
                                    st.markdown("**詳細パラメータ**:")
                                    param_text = "\n".join([f"- **{key}**: {value}" for key, value in entry['parameters'].items()])
                                    st.markdown(param_text)

        finally:

            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    else:

        pass

if __name__ == "__main__":
    main()

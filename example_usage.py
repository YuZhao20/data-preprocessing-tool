"""
データ前処理プログラムの使用例
"""

from data_preprocessor import DataPreprocessor
import pandas as pd
import numpy as np

# サンプルデータの作成（実際の使用時は、この部分を削除して実際のデータファイルを使用）
def create_sample_data():
    """サンプルデータを作成（整数型のカテゴリ変数を含む）"""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'age': np.random.randint(20, 80, n_samples),  # 数値変数
        'income': np.random.normal(50000, 15000, n_samples),  # 数値変数
        'city': np.random.choice(['Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya'], n_samples),  # 文字列カテゴリ
        'education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], n_samples),  # 文字列カテゴリ
        'gender': np.random.choice([0, 1], n_samples),  # 整数カテゴリ（0=女性, 1=男性）
        'status': np.random.choice([0, 1, 2], n_samples),  # 整数カテゴリ（0=未処理, 1=処理中, 2=完了）
        'experience': np.random.randint(0, 30, n_samples),  # 数値変数
        'target': np.random.choice([0, 1], n_samples)  # 分類問題のターゲット
    }
    
    df = pd.DataFrame(data)
    
    # 意図的に欠損値を追加
    missing_indices = np.random.choice(df.index, size=int(n_samples * 0.1), replace=False)
    df.loc[missing_indices, 'income'] = np.nan
    
    # 外れ値を追加
    df.loc[0, 'income'] = 200000
    df.loc[1, 'age'] = 150
    
    return df


def example_1_basic_usage():
    """基本的な使用例（整数型のカテゴリ変数も自動識別）"""
    print("=" * 60)
    print("例1: 基本的な使用例")
    print("=" * 60)
    
    # サンプルデータを作成
    df = create_sample_data()
    df.to_csv('sample_data.csv', index=False)
    
    print("\n元のデータ:")
    print(df.head())
    print(f"\n各列のユニーク値数:")
    for col in df.columns:
        print(f"  {col}: {df[col].nunique()}個")
    
    # 前処理オブジェクトを作成
    preprocessor = DataPreprocessor()
    
    # カテゴリ変数を識別（整数型のカテゴリ変数も含む）
    numerical_cols, categorical_cols = preprocessor.identify_columns(df, categorical_threshold=10)
    print(f"\n識別された数値列: {numerical_cols}")
    print(f"識別されたカテゴリ列: {categorical_cols}")
    
    # パイプラインで前処理を実行
    processed_df = preprocessor.preprocess_pipeline(
        file_path='sample_data.csv',
        target_col='target',
        missing_strategy='auto',
        encoding_method='auto',
        scaling_method='standard',
        remove_outliers_flag=True,
        feature_selection=True,
        k_features=5,
        categorical_threshold=10  # ユニーク値10以下の整数列をカテゴリ変数として扱う
    )
    
    # 結果を保存
    preprocessor.save_processed_data(processed_df, 'processed_data.csv')
    
    print("\n前処理後のデータ:")
    print(processed_df.head())
    print(f"\nデータ形状: {processed_df.shape}")


def example_2_step_by_step():
    """ステップバイステップの使用例"""
    print("\n" + "=" * 60)
    print("例2: ステップバイステップの使用例")
    print("=" * 60)
    
    # サンプルデータを作成
    df = create_sample_data()
    
    preprocessor = DataPreprocessor()
    
    # 1. 列のタイプを識別（整数型のカテゴリ変数も含む）
    preprocessor.identify_columns(df, categorical_threshold=10)
    print(f"数値列: {preprocessor.numerical_columns}")
    print(f"カテゴリ列: {preprocessor.categorical_columns}")
    
    # 2. 欠損値を処理
    df = preprocessor.handle_missing_values(df, strategy='fill', method='mean')
    print(f"\n欠損値処理後: {df.isnull().sum().sum()}個の欠損値")
    
    # 3. 外れ値を除去
    df = preprocessor.remove_outliers(df, method='iqr')
    print(f"外れ値除去後: {df.shape}")
    
    # 4. カテゴリ変数をエンコーディング
    df = preprocessor.encode_categorical(df, method='onehot')
    print(f"エンコーディング後: {df.shape}")
    
    # 5. 特徴量をスケーリング
    df = preprocessor.scale_features(df, method='standard')
    print(f"スケーリング後: {df.shape}")
    
    print("\n処理後のデータ:")
    print(df.head())


def example_3_custom_settings():
    """カスタム設定の使用例（明示的にカテゴリ変数を指定）"""
    print("\n" + "=" * 60)
    print("例3: カスタム設定の使用例")
    print("=" * 60)
    
    df = create_sample_data()
    df.to_csv('sample_data.csv', index=False)
    
    preprocessor = DataPreprocessor()
    
    # カスタム設定で前処理
    processed_df = preprocessor.preprocess_pipeline(
        file_path='sample_data.csv',
        missing_strategy='knn',  # KNN imputationを使用
        encoding_method='label',  # Label encodingを使用
        scaling_method='minmax',  # Min-Max scalingを使用
        remove_outliers_flag=False,  # 外れ値除去をスキップ
        feature_selection=False,  # 特徴量選択をスキップ
        categorical_threshold=5,  # より厳しい閾値
        explicit_categorical=['experience']  # experienceを明示的にカテゴリ変数として指定
    )
    
    print("\nカスタム設定での前処理結果:")
    print(processed_df.head())
    print(f"\n識別されたカテゴリ列: {preprocessor.categorical_columns}")


def example_4_different_file_formats():
    """異なるファイル形式の使用例"""
    print("\n" + "=" * 60)
    print("例4: 異なるファイル形式の使用例")
    print("=" * 60)
    
    df = create_sample_data()
    
    # 複数の形式で保存
    df.to_csv('data.csv', index=False)
    df.to_excel('data.xlsx', index=False)
    df.to_json('data.json', orient='records')
    
    preprocessor = DataPreprocessor()
    
    # CSVファイルの読み込み（自動検出）
    df_csv = preprocessor.load_data('data.csv')
    print(f"CSV読み込み: {df_csv.shape}")
    
    # Excelファイルの読み込み
    df_excel = preprocessor.load_data('data.xlsx')
    print(f"Excel読み込み: {df_excel.shape}")
    
    # JSONファイルの読み込み
    df_json = preprocessor.load_data('data.json')
    print(f"JSON読み込み: {df_json.shape}")


def example_4b_file_structure_detection():
    """ファイル構造の自動検出例"""
    print("\n" + "=" * 60)
    print("例4b: ファイル構造の自動検出")
    print("=" * 60)
    
    preprocessor = DataPreprocessor()
    
    # 標準形式（ヘッダー行あり）
    print("\n【標準形式の読み込み】")
    df = create_sample_data()
    df.to_csv('standard_data.csv', index=False)
    df_loaded = preprocessor.load_data('standard_data.csv', auto_detect_structure=True)
    print(f"読み込み成功: {df_loaded.shape}")
    print(f"列名: {list(df_loaded.columns)}")
    
    # ヘッダー行がない場合
    print("\n【ヘッダー行がない場合】")
    df_no_header = create_sample_data()
    df_no_header.to_csv('no_header_data.csv', index=False, header=False)
    df_loaded2 = preprocessor.load_data(
        'no_header_data.csv',
        header=None,
        names=['age', 'income', 'city', 'education', 'gender', 'status', 'experience', 'target']
    )
    print(f"読み込み成功: {df_loaded2.shape}")
    
    # 特定の行をスキップする場合
    print("\n【特定の行をスキップする場合】")
    with open('skiprows_data.csv', 'w', encoding='utf-8') as f:
        f.write("これは説明行です\n")
        f.write("これも説明行です\n")
        df.to_csv(f, index=False)
    
    df_loaded3 = preprocessor.load_data('skiprows_data.csv', skiprows=[0, 1])
    print(f"読み込み成功: {df_loaded3.shape}")


def example_5_categorical_identification():
    """カテゴリ変数の識別を確認する例"""
    print("\n" + "=" * 60)
    print("例5: カテゴリ変数の識別を確認")
    print("=" * 60)
    
    df = create_sample_data()
    
    preprocessor = DataPreprocessor()
    
    # 異なる閾値でカテゴリ変数を識別
    print("閾値=10の場合:")
    numerical_cols, categorical_cols = preprocessor.identify_columns(df, categorical_threshold=10)
    print(f"  数値列: {numerical_cols}")
    print(f"  カテゴリ列: {categorical_cols}")
    
    print("\n閾値=5の場合:")
    numerical_cols, categorical_cols = preprocessor.identify_columns(df, categorical_threshold=5)
    print(f"  数値列: {numerical_cols}")
    print(f"  カテゴリ列: {categorical_cols}")
    
    print("\n明示的にカテゴリ変数を指定した場合:")
    numerical_cols, categorical_cols = preprocessor.identify_columns(
        df, 
        categorical_threshold=10,
        explicit_categorical=['experience']
    )
    print(f"  数値列: {numerical_cols}")
    print(f"  カテゴリ列: {categorical_cols}")
    
    print("\n各列の詳細情報:")
    for col in df.columns:
        print(f"\n{col}:")
        print(f"  データ型: {df[col].dtype}")
        print(f"  ユニーク値数: {df[col].nunique()}")
        if df[col].dtype in [np.int64, np.int32, np.int16, np.int8]:
            print(f"  値の範囲: {df[col].min()} - {df[col].max()}")
            print(f"  ユニーク値: {sorted(df[col].unique())}")


def example_6_japanese_file_handling():
    """日本語ファイルの読み込み例（文字化け対策）"""
    print("\n" + "=" * 60)
    print("例6: 日本語ファイルの読み込み（文字化け対策）")
    print("=" * 60)
    
    preprocessor = DataPreprocessor()
    
    # 日本語を含むサンプルデータを作成
    df = create_sample_data()
    df['都道府県'] = np.random.choice(['東京都', '大阪府', '京都府'], len(df))
    df['職業'] = np.random.choice(['エンジニア', 'デザイナー', 'マーケター'], len(df))
    
    # Shift-JISで保存（Windowsでよく使われる形式）
    df.to_csv('japanese_data_sjis.csv', index=False, encoding='shift_jis')
    print("Shift-JIS形式でファイルを保存しました: japanese_data_sjis.csv")
    
    # 自動エンコーディング検出で読み込み
    print("\n自動エンコーディング検出で読み込み:")
    df_loaded = preprocessor.load_data('japanese_data_sjis.csv', auto_detect_encoding=True)
    print(df_loaded.head())
    
    # 明示的にエンコーディングを指定して読み込み
    print("\n明示的にエンコーディングを指定して読み込み:")
    df_loaded2 = preprocessor.load_data('japanese_data_sjis.csv', encoding='shift_jis')
    print(df_loaded2.head())
    
    # UTF-8-SIGで保存（Excel互換）
    preprocessor.save_processed_data(df_loaded, 'japanese_data_utf8.csv', encoding='utf-8-sig')
    print("\nUTF-8-SIG形式で保存しました（Excelで開いても文字化けしません）")


def example_7_statistics_and_visualization():
    """記述統計量と可視化の例"""
    print("\n" + "=" * 60)
    print("例7: 記述統計量と可視化")
    print("=" * 60)
    
    df = create_sample_data()
    preprocessor = DataPreprocessor()
    preprocessor.identify_columns(df)
    
    # 記述統計量を表示
    print("\n【記述統計量の表示】")
    preprocessor.describe_statistics(df, include_all=True)
    
    # データの可視化
    print("\n【データの可視化】")
    print("グラフを表示します...")
    preprocessor.visualize_data(df, save_path='example_visualization.png')
    
    # 相関行列の可視化
    if len(preprocessor.numerical_columns) >= 2:
        print("\n【相関行列の可視化】")
        preprocessor.visualize_correlation(df, save_path='example_correlation.png')
    
    # 欠損値の可視化
    if df.isnull().sum().sum() > 0:
        print("\n【欠損値の可視化】")
        preprocessor.visualize_missing_values(df, save_path='example_missing.png')
    
    # 包括的な分析（すべて一度に実行）
    print("\n【包括的な分析】")
    preprocessor.analyze_data(df, visualize=True, save_plots=True, output_dir='.')
    print("\n分析が完了しました。グラフが保存されました。")


if __name__ == '__main__':
    # 各例を実行
    example_1_basic_usage()
    example_2_step_by_step()
    example_3_custom_settings()
    example_4_different_file_formats()
    example_5_categorical_identification()
    example_6_japanese_file_handling()
    example_7_statistics_and_visualization()
    
def example_8_isolation_forest():
    """Isolation Forestによる外れ値検出の例"""
    print("\n" + "=" * 60)
    print("例8: Isolation Forestによる外れ値検出")
    print("=" * 60)
    
    df = create_sample_data()
    preprocessor = DataPreprocessor()
    preprocessor.identify_columns(df)
    
    print("元のデータ形状:", df.shape)
    
    # IQR法による外れ値除去
    print("\n【IQR法による外れ値除去】")
    df_iqr = preprocessor.remove_outliers(df, method='iqr')
    print(f"処理後のデータ形状: {df_iqr.shape}")
    
    # Z-score法による外れ値除去
    print("\n【Z-score法による外れ値除去】")
    df_zscore = preprocessor.remove_outliers(df, method='zscore')
    print(f"処理後のデータ形状: {df_zscore.shape}")
    
    # Isolation Forestによる外れ値除去
    print("\n【Isolation Forestによる外れ値除去】")
    df_iso = preprocessor.remove_outliers(df, method='isolation_forest', contamination=0.1)
    print(f"処理後のデータ形状: {df_iso.shape}")


def example_9_statistical_tests():
    """統計検定の例"""
    print("\n" + "=" * 60)
    print("例9: 統計検定")
    print("=" * 60)
    
    df = create_sample_data()
    preprocessor = DataPreprocessor()
    preprocessor.identify_columns(df)
    
    # 正規性検定のみ
    print("\n【正規性検定のみ】")
    normality_results = preprocessor.test_normality(df, alpha=0.05)
    
    # 包括的な統計検定
    print("\n【包括的な統計検定】")
    test_results = preprocessor.statistical_tests(df, alpha=0.05)
    
    print("\n検定結果の辞書を取得しました。")
    print("結果を確認するには、返された辞書を参照してください。")


if __name__ == '__main__':
    # 各例を実行
    example_1_basic_usage()
    example_2_step_by_step()
    example_3_custom_settings()
    example_4_different_file_formats()
    example_4b_file_structure_detection()
    example_5_categorical_identification()
    example_6_japanese_file_handling()
    example_7_statistics_and_visualization()
    example_8_isolation_forest()
    example_9_statistical_tests()
    
    print("\n" + "=" * 60)
    print("すべての例が完了しました！")
    print("=" * 60)


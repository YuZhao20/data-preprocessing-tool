import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.feature_selection import SelectKBest, f_regression, f_classif
from sklearn.ensemble import IsolationForest
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import os
import urllib.request
from pandas.api.types import is_integer_dtype, is_numeric_dtype
from typing import Any, Dict, List, Optional
import joblib
logger = logging.getLogger(__name__)
try:
    import japanize_matplotlib
    JAPANIZE_AVAILABLE = True
except ImportError:
    JAPANIZE_AVAILABLE = False
ENABLE_FONT_DOWNLOAD = os.getenv('DPT_FONT_DOWNLOAD', '0') == '1'

def setup_japanese_font():
    import matplotlib.font_manager as fm
    from matplotlib import font_manager
    if JAPANIZE_AVAILABLE:
        try:
            import japanize_matplotlib
            plt.rcParams['axes.unicode_minus'] = False
            return font_manager.FontProperties(fname=None)
        except Exception:
            pass
    system = platform.system()
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    os.makedirs(font_dir, exist_ok=True)

    def ensure_local_font():
        preferred_files = ['NotoSansJP-Regular.otf', 'NotoSansCJKjp-Regular.otf', 'IPAexGothic.ttf']
        for fname in preferred_files:
            fpath = os.path.join(font_dir, fname)
            if os.path.exists(fpath):
                return fpath
        if not ENABLE_FONT_DOWNLOAD:
            return None
        download_targets = [('NotoSansJP-Regular.otf', 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansJP-Regular.otf'), ('NotoSansCJKjp-Regular.otf', 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf')]
        for fname, url in download_targets:
            fpath = os.path.join(font_dir, fname)
            try:
                urllib.request.urlretrieve(url, fpath)
                return fpath
            except Exception:
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass
                continue
        return None
    font_path = None
    existing_fonts = [f for f in os.listdir(font_dir) if f.endswith(('.ttf', '.otf'))]
    if existing_fonts:
        font_path = os.path.join(font_dir, existing_fonts[0])
    else:
        font_path = ensure_local_font()
    if font_path and os.path.exists(font_path):
        try:
            font_manager.fontManager.addfont(font_path)
            font_prop = font_manager.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
            plt.rcParams['axes.unicode_minus'] = False
            return font_prop
        except Exception:
            pass
    try:
        available_fonts = [f.name for f in fm.fontManager.ttflist]
    except Exception:
        available_fonts = []
    if system == 'Darwin':
        font_candidates = ['Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Hiragino Mincho ProN', 'AppleGothic', 'Osaka']
    elif system == 'Windows':
        font_candidates = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'MS PGothic', 'MS Mincho']
    else:
        font_candidates = ['Noto Sans CJK JP', 'Noto Sans CJK', 'Noto Sans Japanese', 'TakaoGothic', 'IPAexGothic', 'IPAPGothic', 'DejaVu Sans']
    for font in font_candidates:
        if font in available_fonts:
            try:
                plt.rcParams['font.family'] = font
                plt.rcParams['axes.unicode_minus'] = False
                return font_manager.FontProperties(family=font)
            except Exception:
                continue
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    return font_manager.FontProperties(family='DejaVu Sans')
if JAPANIZE_AVAILABLE:
    try:
        import japanize_matplotlib
        plt.rcParams['axes.unicode_minus'] = False
    except:
        font_prop = setup_japanese_font()
else:
    setup_japanese_font()
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
    logger.warning('chardetがインストールされていません。エンコーディングの自動検出ができません。')

class DataPreprocessor:

    def __init__(self) -> None:
        self.scaler = None
        self.imputer = None
        self.label_encoders = {}
        self.onehot_encoder = None
        self.feature_selector = None
        self.categorical_columns = []
        self.numerical_columns = []
        self.selected_features = None
        self.fitted_ = False
        self.transformers_ = {}
        self.fit_params_ = {}

    def _validate_dataframe(self, df: pd.DataFrame, allow_empty: bool=False) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError('dfはpandas.DataFrameである必要があります。')
        if not allow_empty and df.empty:
            raise ValueError('dfが空です。データを読み込んでから実行してください。')

    def _validate_columns(self, df: pd.DataFrame, columns: Optional[List[str]], label: str) -> None:
        if columns is None:
            return
        missing = [col for col in columns if col not in df.columns]
        if missing:
            raise ValueError(f'{label}に存在しない列が含まれています: {missing}')

    def detect_encoding(self, file_path: str) -> Optional[str]:
        if not CHARDET_AVAILABLE:
            common_encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp']
            return common_encodings[0]
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                if encoding:
                    encoding_lower = encoding.lower()
                    if 'shift' in encoding_lower or 'sjis' in encoding_lower:
                        return 'shift_jis'
                    elif 'cp932' in encoding_lower:
                        return 'cp932'
                    elif 'euc' in encoding_lower:
                        return 'euc-jp'
                    elif 'utf' in encoding_lower:
                        return 'utf-8'
                return encoding if encoding else 'utf-8'
        except Exception as e:
            print(f'エンコーディング検出中にエラーが発生しました: {e}')
            return 'utf-8'

    def detect_file_structure(self, file_path: str, n_rows: int=10) -> Dict[str, Any]:
        file_path_lower = file_path.lower()
        if not file_path_lower.endswith('.csv'):
            return {'header': 0, 'skiprows': None}
        try:
            encoding = self.detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                lines = [f.readline() for _ in range(n_rows)]
            header_candidate = 0
            skiprows = None
            for i, line in enumerate(lines[:5]):
                if not line.strip():
                    continue
                parts = line.strip().split(',')
                numeric_count = 0
                for part in parts:
                    part = part.strip().strip('"').strip("'")
                    try:
                        float(part)
                        numeric_count += 1
                    except:
                        pass
                numeric_ratio = numeric_count / len(parts) if len(parts) > 0 else 0
                if i == 0 and numeric_ratio < 0.5:
                    header_candidate = 0
                    break
                elif i > 0 and numeric_ratio > 0.7:
                    header_candidate = i - 1
                    break
            return {'header': header_candidate if header_candidate >= 0 else None, 'skiprows': skiprows}
        except Exception as e:
            print(f'ファイル構造の検出中にエラー: {e}')
            return {'header': 0, 'skiprows': None}

    def load_data(self, file_path: str, encoding: Optional[str]=None, auto_detect_encoding: bool=True, auto_detect_structure: bool=True, header: Any='auto', skiprows: Optional[Any]=None, index_col: Optional[Any]=None, **kwargs: Any) -> pd.DataFrame:
        file_path_lower = file_path.lower()
        if encoding is None and auto_detect_encoding:
            if file_path_lower.endswith('.csv'):
                encoding = self.detect_encoding(file_path)
                print(f'検出されたエンコーディング: {encoding}')
        if encoding is None:
            encoding = 'utf-8'
        if auto_detect_structure and header == 'auto' and file_path_lower.endswith('.csv'):
            structure = self.detect_file_structure(file_path)
            if structure['header'] is not None:
                header = structure['header']
                print(f'検出されたヘッダー行: {header}')
            if structure['skiprows'] is not None:
                skiprows = structure['skiprows']
        if header == 'auto':
            header = 0
        try:
            if file_path_lower.endswith('.csv'):
                encodings_to_try = [encoding, 'utf-8', 'shift_jis', 'cp932', 'euc-jp'] if encoding else ['utf-8', 'shift_jis', 'cp932', 'euc-jp']
                for enc in encodings_to_try:
                    try:
                        df = pd.read_csv(file_path, encoding=enc, header=header, skiprows=skiprows, index_col=index_col, **kwargs)
                        if encoding != enc:
                            print(f"エンコーディング '{enc}' で正常に読み込めました。")
                        print(f'読み込み成功: {df.shape[0]}行 × {df.shape[1]}列')
                        if len(df.columns) > 0:
                            print(f'列名: {list(df.columns[:5])}{('...' if len(df.columns) > 5 else '')}')
                        return df
                    except (UnicodeDecodeError, UnicodeError) as e:
                        continue
                    except Exception as e:
                        if header != 0 or skiprows is not None:
                            try:
                                print(f'構造検出でエラーが発生しました。デフォルト設定で再試行します。')
                                df = pd.read_csv(file_path, encoding=enc, **kwargs)
                                print(f'読み込み成功（デフォルト設定）: {df.shape[0]}行 × {df.shape[1]}列')
                                return df
                            except:
                                continue
                        else:
                            raise
                raise ValueError(f'ファイルを読み込めませんでした。エンコーディング: {encodings_to_try}')
            elif file_path_lower.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, header=header, skiprows=skiprows, index_col=index_col, **kwargs)
                print(f'読み込み成功: {df.shape[0]}行 × {df.shape[1]}列')
                return df
            elif file_path_lower.endswith('.json'):
                if 'encoding' not in kwargs:
                    kwargs['encoding'] = encoding
                df = pd.read_json(file_path, **kwargs)
                print(f'読み込み成功: {df.shape[0]}行 × {df.shape[1]}列')
                return df
            elif file_path_lower.endswith('.parquet'):
                df = pd.read_parquet(file_path, **kwargs)
                print(f'読み込み成功: {df.shape[0]}行 × {df.shape[1]}列')
                return df
            else:
                raise ValueError(f'サポートされていないファイル形式: {file_path}')
        except Exception as e:
            print(f'ファイル読み込みエラー: {e}')
            print(f'試したエンコーディング: {(encoding if encoding else '自動検出')}')
            print('\nヒント:')
            print('- ヘッダー行を明示的に指定: header=0 または header=None')
            print('- スキップする行を指定: skiprows=[0, 1] など')
            print("- エンコーディングを明示的に指定: encoding='shift_jis' など")
            raise

    def identify_columns(self, df: pd.DataFrame, categorical_threshold: int=10, explicit_categorical: Optional[List[str]]=None) -> List[List[str]]:
        self._validate_dataframe(df)
        self._validate_columns(df, explicit_categorical, 'explicit_categorical')
        if explicit_categorical is None:
            explicit_categorical = []
        self.categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        potential_categorical = []
        for col in numeric_cols:
            if is_integer_dtype(df[col]):
                unique_count = df[col].nunique()
                if unique_count <= categorical_threshold:
                    if unique_count < len(df) * 0.5:
                        potential_categorical.append(col)
        self.categorical_columns.extend(potential_categorical)
        self.categorical_columns.extend(explicit_categorical)
        self.categorical_columns = list(set(self.categorical_columns))
        self.numerical_columns = [col for col in numeric_cols if col not in self.categorical_columns]
        return (self.numerical_columns, self.categorical_columns)

    def handle_missing_values(self, df: pd.DataFrame, strategy: str='auto', method: str='mean', columns: Optional[List[str]]=None, create_missing_flags: bool=False, n_iterations: int=5) -> pd.DataFrame:
        self._validate_dataframe(df)
        self._validate_columns(df, columns, 'columns')
        df = df.copy()
        if columns is None:
            columns = df.columns.tolist()
        if create_missing_flags:
            for col in columns:
                if df[col].isnull().sum() > 0:
                    flag_col_name = f'{col}_is_missing'
                    df[flag_col_name] = df[col].isnull().astype(int)
        if strategy == 'auto':
            missing_ratio = df[columns].isnull().sum() / len(df)
            cols_to_drop = missing_ratio[missing_ratio > 0.5].index.tolist()
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
                print(f'欠損率50%以上の列を削除: {cols_to_drop}')
            columns = [col for col in columns if col not in cols_to_drop]
            strategy = 'fill'
        if strategy == 'drop' or strategy == 'listwise':
            df = df.dropna(subset=columns)
            print(f'リストワイズ削除: {len(df)}行が残りました')
        elif strategy == 'fill':
            for col in columns:
                if df[col].isnull().sum() > 0:
                    if col in self.numerical_columns:
                        if method == 'mean':
                            fill_value = df[col].mean()
                            df[col].fillna(fill_value, inplace=True)
                        elif method == 'median':
                            fill_value = df[col].median()
                            df[col].fillna(fill_value, inplace=True)
                        elif method == 'forward_fill':
                            df[col].fillna(method='ffill', inplace=True)
                        elif method == 'backward_fill':
                            df[col].fillna(method='bfill', inplace=True)
                    elif method == 'mode':
                        mode_value = df[col].mode()[0] if len(df[col].mode()) > 0 else ''
                        df[col].fillna(mode_value, inplace=True)
                    else:
                        df[col].fillna('Unknown', inplace=True)
        elif strategy == 'knn':
            if len(self.numerical_columns) > 0:
                num_cols = [col for col in self.numerical_columns if col in columns]
                if len(num_cols) > 0:
                    self.imputer = KNNImputer(n_neighbors=5)
                    df[num_cols] = self.imputer.fit_transform(df[num_cols])
                    print(f'KNN補完を実行: {len(num_cols)}列')
        elif strategy == 'mice':
            try:
                from sklearn.experimental import enable_iterative_imputer
                from sklearn.impute import IterativeImputer
                num_cols = [col for col in self.numerical_columns if col in columns and df[col].isnull().sum() > 0]
                if len(num_cols) > 0:
                    self.imputer = IterativeImputer(max_iter=n_iterations, random_state=42)
                    df[num_cols] = self.imputer.fit_transform(df[num_cols])
                    print(f'MICE補完を実行: {len(num_cols)}列、{n_iterations}回反復')
                else:
                    print('MICE: 数値列の欠損値が見つかりませんでした')
            except ImportError:
                print('警告: MICEにはsklearn>=0.24が必要です。KNN補完を使用します。')
                if len(self.numerical_columns) > 0:
                    num_cols = [col for col in self.numerical_columns if col in columns]
                    self.imputer = KNNImputer(n_neighbors=5)
                    df[num_cols] = self.imputer.fit_transform(df[num_cols])
        return df

    def encode_categorical(self, df: pd.DataFrame, method: str='auto', columns: Optional[List[str]]=None, target_col: Optional[str]=None, cv_folds: int=5, smoothing: float=1.0) -> pd.DataFrame:
        self._validate_dataframe(df)
        self._validate_columns(df, columns, 'columns')
        df = df.copy()
        if columns is None:
            columns = self.categorical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) == 0:
            return df
        if method == 'auto':
            for col in columns:
                if col in df.columns:
                    unique_count = df[col].nunique()
                    if unique_count <= 5:
                        method = 'onehot'
                    else:
                        method = 'label'
                    break
        if method == 'label':
            for col in columns:
                if col in df.columns:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
        elif method == 'onehot':
            df_encoded_list = []
            for col in columns:
                if col in df.columns:
                    col_encoded = pd.get_dummies(df[col], prefix=col)
                    df_encoded_list.append(col_encoded)
            if df_encoded_list:
                df_encoded = pd.concat(df_encoded_list, axis=1)
                df = df.drop(columns=columns)
                df = pd.concat([df, df_encoded], axis=1)
        elif method == 'ordinal':
            for col in columns:
                if col in df.columns:
                    unique_vals = sorted(df[col].dropna().unique())
                    mapping = {val: idx for idx, val in enumerate(unique_vals)}
                    df[col] = df[col].map(mapping).fillna(-1).astype(int)
        elif method == 'target':
            if target_col is None or target_col not in df.columns:
                print('警告: Target encodingにはターゲット列が必要です。Label encodingを使用します。')
                method = 'label'
                for col in columns:
                    if col in df.columns:
                        if col not in self.label_encoders:
                            self.label_encoders[col] = LabelEncoder()
                        df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
            else:
                try:
                    from sklearn.model_selection import KFold
                    from category_encoders import TargetEncoder
                    for col in columns:
                        if col in df.columns:
                            kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
                            df[f'{col}_target_encoded'] = np.nan
                            for train_idx, val_idx in kf.split(df):
                                train_df = df.iloc[train_idx]
                                val_df = df.iloc[val_idx]
                                encoder = TargetEncoder(smoothing=smoothing)
                                encoder.fit(train_df[[col]], train_df[target_col])
                                df.loc[val_idx, f'{col}_target_encoded'] = encoder.transform(val_df[[col]]).values.flatten()
                            df = df.drop(columns=[col])
                            print(f'Target encoding完了: {col}')
                except ImportError:
                    print('警告: category-encodersがインストールされていません。Label encodingを使用します。')
                    method = 'label'
                    for col in columns:
                        if col in df.columns:
                            if col not in self.label_encoders:
                                self.label_encoders[col] = LabelEncoder()
                            df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
        elif method == 'frequency':
            for col in columns:
                if col in df.columns:
                    freq_map = df[col].value_counts().to_dict()
                    df[f'{col}_freq'] = df[col].map(freq_map)
                    df = df.drop(columns=[col])
        elif method == 'count':
            for col in columns:
                if col in df.columns:
                    count_map = df[col].value_counts().to_dict()
                    df[f'{col}_count'] = df[col].map(count_map)
                    df = df.drop(columns=[col])
        return df

    def scale_features(self, df: pd.DataFrame, method: str='standard', columns: Optional[List[str]]=None) -> pd.DataFrame:
        from sklearn.preprocessing import MaxAbsScaler, QuantileTransformer, PowerTransformer
        self._validate_dataframe(df)
        self._validate_columns(df, columns, 'columns')
        df = df.copy()
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) == 0:
            return df
        if method == 'standard':
            self.scaler = StandardScaler()
            df[columns] = self.scaler.fit_transform(df[columns])
        elif method == 'minmax':
            self.scaler = MinMaxScaler()
            df[columns] = self.scaler.fit_transform(df[columns])
        elif method == 'robust':
            self.scaler = RobustScaler()
            df[columns] = self.scaler.fit_transform(df[columns])
        elif method == 'max_abs':
            self.scaler = MaxAbsScaler()
            df[columns] = self.scaler.fit_transform(df[columns])
        elif method == 'quantile':
            self.scaler = QuantileTransformer(output_distribution='uniform', random_state=42)
            df[columns] = self.scaler.fit_transform(df[columns])
        elif method == 'quantile_normal':
            self.scaler = QuantileTransformer(output_distribution='normal', random_state=42)
            df[columns] = self.scaler.fit_transform(df[columns])
        elif method == 'power':
            self.scaler = PowerTransformer(method='yeo-johnson', standardize=True)
            df[columns] = self.scaler.fit_transform(df[columns])
        elif method == 'box_cox':
            try:
                self.scaler = PowerTransformer(method='box-cox', standardize=True)
                positive_cols = [col for col in columns if (df[col] > 0).all()]
                if len(positive_cols) > 0:
                    df[positive_cols] = self.scaler.fit_transform(df[positive_cols])
                else:
                    logger.warning('Box-Cox変換: 正の値のみの列が見つかりませんでした')
            except Exception as e:
                print(f'Box-Cox変換エラー: {e}')
        elif method == 'log':
            positive_cols = [col for col in columns if (df[col] > 0).all()]
            if len(positive_cols) > 0:
                df[positive_cols] = np.log1p(df[positive_cols])
            else:
                print('対数変換: 正の値のみの列が見つかりませんでした')
        elif method == 'sqrt':
            non_negative_cols = [col for col in columns if (df[col] >= 0).all()]
            if len(non_negative_cols) > 0:
                df[non_negative_cols] = np.sqrt(df[non_negative_cols])
            else:
                print('平方根変換: 非負の値のみの列が見つかりませんでした')
        else:
            raise ValueError(f'未知のスケーリング方法: {method}')
        return df

    def select_features(self, df: pd.DataFrame, target_col: str, k: str='auto', score_func: Optional[Any]=None) -> pd.DataFrame:
        self._validate_dataframe(df)
        if target_col not in df.columns:
            return df
        feature_cols = [col for col in self.numerical_columns if col in df.columns and col != target_col]
        if len(feature_cols) == 0:
            return df
        X = df[feature_cols]
        y = df[target_col]
        y_is_numeric = is_numeric_dtype(y)
        if not y_is_numeric:
            y_numeric = pd.to_numeric(y, errors='coerce')
            if y_numeric.notna().mean() > 0.9:
                y = y_numeric
                y_is_numeric = True
        if y_is_numeric or len(y.unique()) > 10:
            if score_func is None:
                score_func = f_regression
            problem_type = 'regression'
        else:
            if score_func is None:
                score_func = f_classif
            problem_type = 'classification'
        if k == 'auto':
            k = min(len(feature_cols), 10)
        self.feature_selector = SelectKBest(score_func=score_func, k=k)
        X_selected = self.feature_selector.fit_transform(X, y)
        selected_features = [feature_cols[i] for i in self.feature_selector.get_support(indices=True)]
        self.selected_features = selected_features
        df_selected = df[selected_features + [target_col]].copy()
        return df_selected

    def remove_outliers(self, df: pd.DataFrame, method: str='iqr', columns: Optional[List[str]]=None, contamination: float=0.1, z_threshold: float=3.0, iqr_multiplier: float=1.5, random_state: int=42, winsorize_limits: tuple=(0.01, 0.99), action: str='remove') -> pd.DataFrame:
        self._validate_dataframe(df)
        self._validate_columns(df, columns, 'columns')
        df = df.copy()
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) == 0:
            return df
        if method == 'iqr':
            for col in columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - iqr_multiplier * IQR
                upper_bound = Q3 + iqr_multiplier * IQR
                if action == 'remove':
                    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
                else:
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        elif method == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(df[columns]))
            if action == 'remove':
                df = df[(z_scores < z_threshold).all(axis=1)]
            else:
                for col in columns:
                    z_col = np.abs(stats.zscore(df[col]))
                    mask = z_col > z_threshold
                    if mask.any():
                        median = df[col].median()
                        std = df[col].std()
                        df.loc[mask, col] = np.clip(df.loc[mask, col], median - z_threshold * std, median + z_threshold * std)
        elif method == 'mad':
            from scipy import stats
            for col in columns:
                median = df[col].median()
                mad = (df[col] - median).abs().median()
                threshold = 3.0
                lower_bound = median - threshold * mad
                upper_bound = median + threshold * mad
                if action == 'remove':
                    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
                else:
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        elif method == 'winsorize':
            for col in columns:
                lower_limit = df[col].quantile(winsorize_limits[0])
                upper_limit = df[col].quantile(winsorize_limits[1])
                df[col] = df[col].clip(lower=lower_limit, upper=upper_limit)
        elif method == 'isolation_forest':
            df_temp = df[columns].copy()
            df_temp = df_temp.fillna(df_temp.median())
            iso_forest = IsolationForest(contamination=contamination, random_state=random_state, n_estimators=100)
            outliers = iso_forest.fit_predict(df_temp)
            if action == 'remove':
                df = df[outliers == 1]
                print(f'Isolation Forest: {np.sum(outliers == -1)}個の外れ値を検出・除去しました。')
            else:
                for col in columns:
                    outlier_mask = outliers == -1
                    if outlier_mask.any():
                        median = df[col].median()
                        std = df[col].std()
                        df.loc[outlier_mask, col] = np.clip(df.loc[outlier_mask, col], median - 3 * std, median + 3 * std)
                print(f'Isolation Forest: {np.sum(outliers == -1)}個の外れ値を検出・クリップしました。')
        elif method == 'mahalanobis':
            from scipy.spatial.distance import mahalanobis
            from scipy.linalg import inv
            try:
                df_temp = df[columns].dropna()
                if len(df_temp) == 0:
                    return df
                mean = df_temp.mean()
                cov = df_temp.cov()
                cov_inv = inv(cov)
                distances = []
                for idx, row in df_temp.iterrows():
                    try:
                        dist = mahalanobis(row.values, mean.values, cov_inv)
                        distances.append(dist)
                    except:
                        distances.append(np.nan)
                distances = np.array(distances)
                threshold = np.percentile(distances[~np.isnan(distances)], 95)
                if action == 'remove':
                    outlier_mask = distances > threshold
                    df = df[~df.index.isin(df_temp.index[outlier_mask])]
                else:
                    print('警告: Mahalanobis距離ではクリップではなく削除を推奨します')
                    outlier_mask = distances > threshold
                    df = df[~df.index.isin(df_temp.index[outlier_mask])]
            except Exception as e:
                print(f'Mahalanobis距離の計算エラー: {e}')
        else:
            raise ValueError(f'未知の外れ値検出方法: {method}')
        return df

    def preprocess_pipeline(self, file_path: str, target_col: Optional[str]=None, missing_strategy: str='auto', encoding_method: str='auto', scaling_method: str='standard', remove_outliers_flag: bool=False, feature_selection: bool=False, k_features: str='auto', categorical_threshold: int=10, explicit_categorical: Optional[List[str]]=None, **load_kwargs: Any) -> pd.DataFrame:
        print('データを読み込んでいます...')
        df = self.load_data(file_path, **load_kwargs)
        print(f'データ形状: {df.shape}')
        print('\n列のタイプを識別しています...')
        self.identify_columns(df, categorical_threshold=categorical_threshold, explicit_categorical=explicit_categorical)
        print(f'数値列: {len(self.numerical_columns)}個 - {self.numerical_columns}')
        print(f'カテゴリ列: {len(self.categorical_columns)}個 - {self.categorical_columns}')
        print('\n欠損値を処理しています...')
        df = self.handle_missing_values(df, strategy=missing_strategy)
        print(f'処理後のデータ形状: {df.shape}')
        if remove_outliers_flag and len(self.numerical_columns) > 0:
            print('\n外れ値を除去しています...')
            df = self.remove_outliers(df, method='iqr')
            print(f'処理後のデータ形状: {df.shape}')
        if len(self.categorical_columns) > 0:
            print('\nカテゴリ変数をエンコーディングしています...')
            df = self.encode_categorical(df, method=encoding_method)
            print(f'処理後のデータ形状: {df.shape}')
        if scaling_method and len(self.numerical_columns) > 0:
            print('\n特徴量をスケーリングしています...')
            df = self.scale_features(df, method=scaling_method)
        if feature_selection and target_col:
            print('\n特徴量を選択しています...')
            df = self.select_features(df, target_col, k=k_features)
            print(f'選択された特徴量: {len(self.selected_features)}個')
        print('\n前処理が完了しました！')
        return df

    def save_processed_data(self, df: pd.DataFrame, output_path: str, encoding: str='utf-8-sig') -> None:
        self._validate_dataframe(df, allow_empty=True)
        output_path_lower = output_path.lower()
        if output_path_lower.endswith('.csv'):
            df.to_csv(output_path, index=False, encoding=encoding)
        elif output_path_lower.endswith(('.xlsx', '.xls')):
            df.to_excel(output_path, index=False)
        elif output_path_lower.endswith('.json'):
            df.to_json(output_path, orient='records', force_ascii=False, ensure_ascii=False)
        elif output_path_lower.endswith('.parquet'):
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f'サポートされていないファイル形式: {output_path}')
        print(f'データを保存しました: {output_path}')

    def describe_statistics(self, df, include_all=False):
        print('=' * 80)
        print('記述統計量')
        print('=' * 80)
        if include_all:
            print('\n【全変数の基本統計】')
            print(df.describe(include='all'))
        else:
            print('\n【数値変数の基本統計】')
            if len(self.numerical_columns) > 0:
                num_cols = [col for col in self.numerical_columns if col in df.columns]
                if len(num_cols) > 0:
                    print(df[num_cols].describe())
                else:
                    print('数値変数がありません。')
            else:
                print('数値変数が識別されていません。identify_columns()を先に実行してください。')
        print('\n【データ情報】')
        print(f'行数: {len(df)}')
        print(f'列数: {len(df.columns)}')
        print(f'欠損値の合計: {df.isnull().sum().sum()}個')
        if len(self.categorical_columns) > 0:
            print('\n【カテゴリ変数の情報】')
            cat_cols = [col for col in self.categorical_columns if col in df.columns]
            for col in cat_cols:
                print(f'\n{col}:')
                print(f'  ユニーク値数: {df[col].nunique()}')
                print(f'  最頻値: {(df[col].mode()[0] if len(df[col].mode()) > 0 else 'N/A')}')
                print(f'  値の分布:')
                value_counts = df[col].value_counts().head(10)
                for val, count in value_counts.items():
                    print(f'    {val}: {count} ({count / len(df) * 100:.1f}%)')
        print('\n' + '=' * 80)

    def save_pipeline(self, output_path: str) -> None:
        payload = {'scaler': self.scaler, 'imputer': self.imputer, 'label_encoders': self.label_encoders, 'onehot_encoder': self.onehot_encoder, 'feature_selector': self.feature_selector, 'categorical_columns': self.categorical_columns, 'numerical_columns': self.numerical_columns, 'selected_features': self.selected_features, 'fitted_': self.fitted_, 'transformers_': self.transformers_, 'fit_params_': self.fit_params_}
        joblib.dump(payload, output_path)

    def load_pipeline(self, input_path: str) -> 'DataPreprocessor':
        payload = joblib.load(input_path)
        self.scaler = payload.get('scaler')
        self.imputer = payload.get('imputer')
        self.label_encoders = payload.get('label_encoders', {})
        self.onehot_encoder = payload.get('onehot_encoder')
        self.feature_selector = payload.get('feature_selector')
        self.categorical_columns = payload.get('categorical_columns', [])
        self.numerical_columns = payload.get('numerical_columns', [])
        self.selected_features = payload.get('selected_features')
        self.fitted_ = payload.get('fitted_', False)
        self.transformers_ = payload.get('transformers_', {})
        self.fit_params_ = payload.get('fit_params_', {})
        return self

    def visualize_data(self, df, figsize=(15, 10), save_path=None, dpi=300):
        font_prop = setup_japanese_font()
        if not hasattr(self, 'numerical_columns') or not hasattr(self, 'categorical_columns'):
            self.identify_columns(df)
        num_cols = [col for col in self.numerical_columns if col in df.columns]
        cat_cols = [col for col in self.categorical_columns if col in df.columns]
        if len(num_cols) == 0 and len(cat_cols) == 0:
            self.identify_columns(df)
            num_cols = [col for col in self.numerical_columns if col in df.columns]
            cat_cols = [col for col in self.categorical_columns if col in df.columns]
            if len(num_cols) == 0 and len(cat_cols) == 0:
                raise ValueError('可視化する変数がありません。データに数値変数またはカテゴリ変数が含まれていることを確認してください。')
        n_plots = 0
        if len(num_cols) > 0:
            n_plots += min(len(num_cols), 4)
        if len(cat_cols) > 0:
            n_plots += min(len(cat_cols), 4)
        if n_plots == 0:
            print('可視化する変数がありません。')
            return
        n_cols = 2
        n_rows = (n_plots + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        if n_plots == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        plot_idx = 0
        for col in num_cols[:4]:
            if plot_idx >= len(axes):
                break
            ax = axes[plot_idx]
            df[col].hist(bins=30, ax=ax, edgecolor='black')
            try:
                ax.set_title(f'{col}の分布', fontsize=12, fontproperties=font_prop)
                ax.set_xlabel(col, fontsize=10, fontproperties=font_prop)
                ax.set_ylabel('頻度', fontsize=10, fontproperties=font_prop)
            except Exception:
                ax.set_title(f'Distribution of {col}', fontsize=12)
                ax.set_xlabel(col, fontsize=10)
                ax.set_ylabel('Frequency', fontsize=10)
            for label in ax.get_xticklabels():
                try:
                    label.set_fontproperties(font_prop)
                except Exception:
                    pass
            for label in ax.get_yticklabels():
                try:
                    label.set_fontproperties(font_prop)
                except Exception:
                    pass
            ax.grid(True, alpha=0.3)
            plot_idx += 1
        for col in cat_cols[:4]:
            if plot_idx >= len(axes):
                break
            ax = axes[plot_idx]
            value_counts = df[col].value_counts().head(10)
            value_counts.plot(kind='bar', ax=ax, color='steelblue', edgecolor='black')
            try:
                ax.set_title(f'{col}の分布', fontsize=12, fontproperties=font_prop)
                ax.set_xlabel(col, fontsize=10, fontproperties=font_prop)
                ax.set_ylabel('頻度', fontsize=10, fontproperties=font_prop)
            except Exception:
                ax.set_title(f'Distribution of {col}', fontsize=12)
                ax.set_xlabel(col, fontsize=10)
                ax.set_ylabel('Frequency', fontsize=10)
            for label in ax.get_xticklabels():
                try:
                    label.set_fontproperties(font_prop)
                except Exception:
                    pass
            for label in ax.get_yticklabels():
                try:
                    label.set_fontproperties(font_prop)
                except Exception:
                    pass
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3, axis='y')
            plot_idx += 1
        for idx in range(plot_idx, len(axes)):
            axes[idx].axis('off')
        plt.tight_layout()
        if save_path:
            try:
                fig.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
                if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
                    raise IOError(f'グラフファイルの保存に失敗しました: {save_path}')
            except Exception as e:
                plt.close(fig)
                plt.clf()
                raise IOError(f'グラフの保存中にエラーが発生しました: {e}')
        else:
            plt.show()
        plt.close(fig)
        plt.clf()

    def visualize_correlation(self, df, figsize=(12, 10), save_path=None, dpi=300):
        font_prop = setup_japanese_font()
        if not hasattr(self, 'numerical_columns') or not hasattr(self, 'categorical_columns'):
            self.identify_columns(df)
        num_cols = [col for col in self.numerical_columns if col in df.columns]
        if len(num_cols) < 2:
            self.identify_columns(df)
            num_cols = [col for col in self.numerical_columns if col in df.columns]
            if len(num_cols) < 2:
                raise ValueError('相関行列を作成するには、少なくとも2つの数値変数が必要です。')
        corr_matrix = df[num_cols].corr()
        setup_japanese_font()
        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, square=True, linewidths=1, cbar_kws={'shrink': 0.8}, ax=ax)
        try:
            ax.set_title('変数間の相関行列', fontsize=14, pad=20, fontproperties=font_prop)
            ax.set_xlabel('相関行列列', fontsize=11, fontproperties=font_prop)
            ax.set_ylabel('相関行列行', fontsize=11, fontproperties=font_prop)
        except Exception:
            try:
                ax.set_title('Correlation Matrix', fontsize=14, pad=20)
                ax.set_xlabel('Columns', fontsize=11)
                ax.set_ylabel('Rows', fontsize=11)
            except Exception:
                pass
        for label in ax.get_xticklabels():
            try:
                label.set_fontproperties(font_prop)
            except Exception:
                pass
        for label in ax.get_yticklabels():
            try:
                label.set_fontproperties(font_prop)
            except Exception:
                pass
        plt.tight_layout()
        if save_path:
            try:
                fig.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
                if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
                    raise IOError(f'相関行列ファイルの保存に失敗しました: {save_path}')
            except Exception as e:
                plt.close(fig)
                plt.clf()
                raise IOError(f'相関行列の保存中にエラーが発生しました: {e}')
        else:
            plt.show()
        plt.close(fig)
        plt.clf()

    def visualize_missing_values(self, df, figsize=(12, 6), save_path=None, dpi=300):
        setup_japanese_font()
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
        if len(missing_data) == 0:
            print('欠損値はありません。')
            return
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        setup_japanese_font()
        missing_data.plot(kind='bar', ax=ax1, color='coral', edgecolor='black')
        try:
            ax1.set_title('欠損値の数', fontsize=12)
            ax1.set_xlabel('変数名', fontsize=10)
            ax1.set_ylabel('欠損値の数', fontsize=10)
        except Exception as e:
            ax1.set_title('Number of Missing Values', fontsize=12)
            ax1.set_xlabel('Variable Name', fontsize=10)
            ax1.set_ylabel('Number of Missing Values', fontsize=10)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3, axis='y')
        missing_pct = (missing_data / len(df) * 100).sort_values(ascending=False)
        missing_pct.plot(kind='bar', ax=ax2, color='steelblue', edgecolor='black')
        try:
            ax2.set_title('欠損値の割合 (%)', fontsize=12)
            ax2.set_xlabel('変数名', fontsize=10)
            ax2.set_ylabel('欠損値の割合 (%)', fontsize=10)
        except Exception as e:
            ax2.set_title('Missing Value Percentage (%)', fontsize=12)
            ax2.set_xlabel('Variable Name', fontsize=10)
            ax2.set_ylabel('Missing Value Percentage (%)', fontsize=10)
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
            print(f'欠損値の可視化を保存しました: {save_path}')
        else:
            plt.show()
        plt.close(fig)
        plt.clf()

    def statistical_tests(self, df, columns=None, alpha=0.05):
        from scipy import stats
        from scipy.stats import shapiro, normaltest, anderson, levene, bartlett, chi2_contingency
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) == 0:
            print('検定する数値変数がありません。')
            return {}
        results = {}
        print('=' * 80)
        print('統計検定結果')
        print('=' * 80)
        for col in columns:
            data = df[col].dropna()
            if len(data) < 3:
                continue
            print(f'\n【{col}】')
            results[col] = {}
            print('\n1. 正規性検定:')
            if len(data) <= 5000:
                stat_sw, p_value_sw = shapiro(data)
                results[col]['shapiro_wilk'] = {'statistic': stat_sw, 'p_value': p_value_sw, 'is_normal': p_value_sw > alpha}
                print(f'  Shapiro-Wilk検定:')
                print(f'    統計量: {stat_sw:.4f}')
                print(f'    p値: {p_value_sw:.4f}')
                print(f'    結果: {('正規分布' if p_value_sw > alpha else '非正規分布')} (α={alpha})')
            stat_dp, p_value_dp = normaltest(data)
            results[col]['dagostino_pearson'] = {'statistic': stat_dp, 'p_value': p_value_dp, 'is_normal': p_value_dp > alpha}
            print(f"  D'Agostino-Pearson検定:")
            print(f'    統計量: {stat_dp:.4f}')
            print(f'    p値: {p_value_dp:.4f}')
            print(f'    結果: {('正規分布' if p_value_dp > alpha else '非正規分布')} (α={alpha})')
            try:
                anderson_result = anderson(data, dist='norm')
                results[col]['anderson_darling'] = {'statistic': anderson_result.statistic, 'critical_values': anderson_result.critical_values.tolist(), 'significance_levels': anderson_result.significance_level.tolist()}
                print(f'  Anderson-Darling検定:')
                print(f'    統計量: {anderson_result.statistic:.4f}')
                print(f'    臨界値: {anderson_result.critical_values}')
            except Exception as e:
                print(f'  Anderson-Darling検定: エラー ({e})')
            skewness = stats.skew(data)
            kurtosis = stats.kurtosis(data)
            results[col]['skewness'] = skewness
            results[col]['kurtosis'] = kurtosis
            print(f'\n2. 分布の形状:')
            print(f'  歪度: {skewness:.4f} ({('右に歪む' if skewness > 0 else '左に歪む' if skewness < 0 else '対称')})')
            print(f'  尖度: {kurtosis:.4f} ({('尖っている' if kurtosis > 0 else '平ら' if kurtosis < 0 else '正規分布に近い')})')
        if len(columns) >= 2:
            print(f'\n【等分散性検定】')
            data_list = [df[col].dropna().values for col in columns if len(df[col].dropna()) > 0]
            if len(data_list) >= 2:
                stat_levene, p_value_levene = levene(*data_list)
                results['levene_test'] = {'statistic': stat_levene, 'p_value': p_value_levene, 'equal_variance': p_value_levene > alpha}
                print(f'  Levene検定:')
                print(f'    統計量: {stat_levene:.4f}')
                print(f'    p値: {p_value_levene:.4f}')
                print(f'    結果: {('等分散' if p_value_levene > alpha else '不等分散')} (α={alpha})')
            if len(data_list) >= 2:
                try:
                    stat_bartlett, p_value_bartlett = bartlett(*data_list)
                    results['bartlett_test'] = {'statistic': stat_bartlett, 'p_value': p_value_bartlett, 'equal_variance': p_value_bartlett > alpha}
                    print(f'  Bartlett検定:')
                    print(f'    統計量: {stat_bartlett:.4f}')
                    print(f'    p値: {p_value_bartlett:.4f}')
                    print(f'    結果: {('等分散' if p_value_bartlett > alpha else '不等分散')} (α={alpha})')
                except Exception as e:
                    print(f'  Bartlett検定: エラー ({e})')
        if len(self.categorical_columns) >= 2:
            print(f'\n【独立性検定（カテゴリ変数）】')
            cat_cols = [col for col in self.categorical_columns if col in df.columns]
            if len(cat_cols) >= 2:
                col1, col2 = (cat_cols[0], cat_cols[1])
                contingency_table = pd.crosstab(df[col1], df[col2])
                if contingency_table.size > 0:
                    chi2, p_value_chi2, dof, expected = chi2_contingency(contingency_table)
                    results['chi_square_test'] = {'statistic': chi2, 'p_value': p_value_chi2, 'degrees_of_freedom': dof, 'independent': p_value_chi2 > alpha}
                    print(f'  {col1} と {col2} の独立性検定（カイ二乗検定）:')
                    print(f'    統計量: {chi2:.4f}')
                    print(f'    p値: {p_value_chi2:.4f}')
                    print(f'    自由度: {dof}')
                    print(f'    結果: {('独立' if p_value_chi2 > alpha else '従属')} (α={alpha})')
        print('\n' + '=' * 80)
        return results

    def test_normality(self, df, columns=None, alpha=0.05):
        from scipy.stats import shapiro, normaltest
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        results = {}
        print('=' * 80)
        print('正規性検定')
        print('=' * 80)
        for col in columns:
            data = df[col].dropna()
            if len(data) < 3:
                continue
            results[col] = {}
            if len(data) <= 5000:
                stat, p_value = shapiro(data)
                results[col]['shapiro_wilk'] = {'statistic': stat, 'p_value': p_value, 'is_normal': p_value > alpha}
            stat, p_value = normaltest(data)
            results[col]['dagostino_pearson'] = {'statistic': stat, 'p_value': p_value, 'is_normal': p_value > alpha}
            print(f'\n{col}:')
            if 'shapiro_wilk' in results[col]:
                print(f'  Shapiro-Wilk: p={results[col]['shapiro_wilk']['p_value']:.4f}, {('正規分布' if results[col]['shapiro_wilk']['is_normal'] else '非正規分布')}')
            print(f"  D'Agostino-Pearson: p={results[col]['dagostino_pearson']['p_value']:.4f}, {('正規分布' if results[col]['dagostino_pearson']['is_normal'] else '非正規分布')}")
        print('=' * 80)
        return results

    def analyze_data(self, df, visualize=True, save_plots=False, output_dir='.'):
        self.describe_statistics(df, include_all=True)
        if visualize:
            plot_path = f'{output_dir}/data_visualization.png' if save_plots else None
            self.visualize_data(df, save_path=plot_path)
            if len(self.numerical_columns) >= 2:
                corr_path = f'{output_dir}/correlation_matrix.png' if save_plots else None
                self.visualize_correlation(df, save_path=corr_path)
            if df.isnull().sum().sum() > 0:
                missing_path = f'{output_dir}/missing_values.png' if save_plots else None
                self.visualize_missing_values(df, save_path=missing_path)

    def remove_duplicates(self, df, subset=None, keep='first', method='exact'):
        df = df.copy()
        if method == 'exact':
            if subset is None:
                df = df.drop_duplicates(keep=keep)
            else:
                df = df.drop_duplicates(subset=subset, keep=keep)
            print(f'重複削除: {len(df)}行が残りました')
        elif method == 'key':
            if subset is None:
                print('警告: キー列が指定されていません。全列で重複チェックします。')
                df = df.drop_duplicates(keep=keep)
            else:
                df = df.drop_duplicates(subset=subset, keep=keep)
            print(f'キー重複削除: {len(df)}行が残りました')
        elif method == 'similarity':
            try:
                from difflib import SequenceMatcher
                if subset is None:
                    text_cols = df.select_dtypes(include=['object']).columns.tolist()
                else:
                    text_cols = subset
                if len(text_cols) == 0:
                    print('警告: テキスト列が見つかりません。完全一致で重複チェックします。')
                    df = df.drop_duplicates(keep=keep)
                else:
                    threshold = 0.9
                    to_drop = []
                    for i in range(len(df)):
                        if i in to_drop:
                            continue
                        for j in range(i + 1, len(df)):
                            if j in to_drop:
                                continue
                            similar = True
                            for col in text_cols:
                                val1 = str(df.iloc[i][col])
                                val2 = str(df.iloc[j][col])
                                similarity = SequenceMatcher(None, val1, val2).ratio()
                                if similarity < threshold:
                                    similar = False
                                    break
                            if similar:
                                to_drop.append(j)
                    df = df.drop(df.index[to_drop]).reset_index(drop=True)
                    print(f'近似重複削除: {len(to_drop)}行を削除、{len(df)}行が残りました')
            except Exception as e:
                print(f'近似重複削除エラー: {e}。完全一致で重複チェックします。')
                df = df.drop_duplicates(keep=keep)
        return df

    def feature_engineering(self, df, interactions=False, polynomial=False, binning=False, n_bins=5, binning_method='equal_freq'):
        df = df.copy()
        if interactions and len(self.numerical_columns) >= 2:
            num_cols = [col for col in self.numerical_columns if col in df.columns]
            for i, col1 in enumerate(num_cols[:5]):
                for col2 in num_cols[i + 1:6]:
                    df[f'{col1}_x_{col2}'] = df[col1] * df[col2]
            print(f'交互作用項を作成しました')
        if polynomial and len(self.numerical_columns) > 0:
            from sklearn.preprocessing import PolynomialFeatures
            num_cols = [col for col in self.numerical_columns if col in df.columns][:5]
            if len(num_cols) > 0:
                poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=False)
                poly_features = poly.fit_transform(df[num_cols])
                poly_df = pd.DataFrame(poly_features, columns=poly.get_feature_names_out(num_cols), index=df.index)
                df = df.drop(columns=num_cols)
                df = pd.concat([df, poly_df], axis=1)
                print(f'多項式特徴を作成しました: {len(poly_df.columns)}個の特徴量')
        if binning and len(self.numerical_columns) > 0:
            num_cols = [col for col in self.numerical_columns if col in df.columns]
            for col in num_cols[:10]:
                if binning_method == 'equal_freq':
                    df[f'{col}_binned'] = pd.qcut(df[col], q=n_bins, duplicates='drop', labels=False)
                else:
                    df[f'{col}_binned'] = pd.cut(df[col], bins=n_bins, labels=False, duplicates='drop')
            print(f'ビニングを実行しました: {len(num_cols[:10])}列')
        return df

    def calculate_vif(self, df, columns=None, threshold=10.0):
        try:
            from statsmodels.stats.outliers_influence import variance_inflation_factor
        except ImportError:
            print('警告: statsmodelsが必要です。VIF計算をスキップします。')
            return pd.DataFrame()
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) < 2:
            print('VIF計算には少なくとも2つの数値変数が必要です。')
            return pd.DataFrame()
        df_temp = df[columns].dropna()
        if len(df_temp) == 0:
            print('VIF計算: 有効なデータがありません。')
            return pd.DataFrame()
        try:
            vif_data = pd.DataFrame()
            vif_data['変数'] = columns
            vif_data['VIF'] = [variance_inflation_factor(df_temp.values, i) for i in range(len(columns))]
            vif_data['共線性あり'] = vif_data['VIF'] > threshold
            return vif_data
        except Exception as e:
            print(f'VIF計算エラー: {e}')
            return pd.DataFrame()

    def handle_imbalance(self, df, target_col, method='smote', sampling_strategy='auto'):
        if target_col not in df.columns:
            print('警告: ターゲット列が見つかりません。')
            return df
        try:
            from imblearn.over_sampling import SMOTE, ADASYN, RandomOverSampler
            from imblearn.under_sampling import RandomUnderSampler
            X = df.drop(columns=[target_col])
            y = df[target_col]
            num_cols = [col for col in self.numerical_columns if col in X.columns]
            if len(num_cols) == 0:
                print('警告: 数値変数が見つかりません。')
                return df
            X_num = X[num_cols].fillna(X[num_cols].median())
            if method == 'smote':
                sampler = SMOTE(sampling_strategy=sampling_strategy, random_state=42)
            elif method == 'adasyn':
                sampler = ADASYN(sampling_strategy=sampling_strategy, random_state=42)
            elif method == 'random_oversample':
                sampler = RandomOverSampler(sampling_strategy=sampling_strategy, random_state=42)
            elif method == 'random_undersample':
                sampler = RandomUnderSampler(sampling_strategy=sampling_strategy, random_state=42)
            else:
                print(f'未知のサンプリング方法: {method}')
                return df
            X_resampled, y_resampled = sampler.fit_resample(X_num, y)
            df_resampled = pd.DataFrame(X_resampled, columns=num_cols)
            df_resampled[target_col] = y_resampled
            print(f'{method}適用: {len(df)}行 → {len(df_resampled)}行')
            return df_resampled
        except ImportError:
            print('警告: imbalanced-learnがインストールされていません。')
            return df
        except Exception as e:
            print(f'クラス不均衡処理エラー: {e}')
            return df

    def split_data(self, df, target_col, test_size=0.2, method='random', n_splits=5, groups=None, stratify=True):
        from sklearn.model_selection import train_test_split, TimeSeriesSplit, GroupKFold, StratifiedKFold, KFold
        if target_col not in df.columns:
            print('警告: ターゲット列が見つかりません。')
            return None
        X = df.drop(columns=[target_col])
        y = df[target_col]
        y_is_numeric = is_numeric_dtype(y)
        if method == 'random':
            if stratify and (not y_is_numeric) and (len(y.unique()) <= 10):
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
            else:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
            return {'X_train': X_train, 'X_test': X_test, 'y_train': y_train, 'y_test': y_test}
        elif method == 'timeseries':
            tscv = TimeSeriesSplit(n_splits=n_splits)
            splits = []
            for train_idx, test_idx in tscv.split(X):
                splits.append({'train': train_idx.tolist(), 'test': test_idx.tolist()})
            return {'splits': splits, 'cv': tscv}
        elif method == 'group':
            if groups is None:
                print('警告: グループ列が指定されていません。ランダム分割を使用します。')
                return self.split_data(df, target_col, test_size, 'random', stratify=stratify)
            group_col = df[groups]
            gkf = GroupKFold(n_splits=n_splits)
            splits = []
            for train_idx, test_idx in gkf.split(X, y, group_col):
                splits.append({'train': train_idx.tolist(), 'test': test_idx.tolist()})
            return {'splits': splits, 'cv': gkf}
        elif method == 'stratified':
            if not y_is_numeric and len(y.unique()) <= 10:
                skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
                splits = []
                for train_idx, test_idx in skf.split(X, y):
                    splits.append({'train': train_idx.tolist(), 'test': test_idx.tolist()})
                return {'splits': splits, 'cv': skf}
            else:
                print('警告: Stratified分割にはカテゴリ変数が必要です。通常のKFoldを使用します。')
                kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
                splits = []
                for train_idx, test_idx in kf.split(X):
                    splits.append({'train': train_idx.tolist(), 'test': test_idx.tolist()})
                return {'splits': splits, 'cv': kf}
        return None

    def calculate_condition_number(self, df, columns=None):
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) < 2:
            print('条件数計算には少なくとも2つの数値変数が必要です。')
            return None
        try:
            df_temp = df[columns].dropna()
            if len(df_temp) == 0:
                print('条件数計算: 有効なデータがありません。')
                return None
            corr_matrix = df_temp.corr().values
            condition_num = np.linalg.cond(corr_matrix)
            return condition_num
        except Exception as e:
            print(f'条件数計算エラー: {e}')
            return None

    def cluster_correlations(self, df, columns=None, method='ward', n_clusters=None):
        try:
            from scipy.cluster.hierarchy import linkage, fcluster
            from scipy.spatial.distance import squareform
        except ImportError:
            print('警告: scipyが必要です。相関クラスタリングをスキップします。')
            return {}
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) < 2:
            print('相関クラスタリングには少なくとも2つの数値変数が必要です。')
            return {}
        try:
            df_temp = df[columns].dropna()
            if len(df_temp) == 0:
                print('相関クラスタリング: 有効なデータがありません。')
                return {}
            corr_matrix = df_temp.corr().values
            distance_matrix = 1 - np.abs(corr_matrix)
            condensed_distances = squareform(distance_matrix, checks=False)
            linkage_matrix = linkage(condensed_distances, method=method)
            if n_clusters is None:
                threshold = 0.3
                clusters = fcluster(linkage_matrix, threshold, criterion='distance')
            else:
                clusters = fcluster(linkage_matrix, n_clusters, criterion='maxclust')
            cluster_dict = {}
            for i, col in enumerate(columns):
                cluster_id = clusters[i]
                if cluster_id not in cluster_dict:
                    cluster_dict[cluster_id] = []
                cluster_dict[cluster_id].append(col)
            return cluster_dict
        except Exception as e:
            print(f'相関クラスタリングエラー: {e}')
            return {}

    def diagnose_missing_patterns(self, df):
        missing_data = df.isnull()
        missing_ratio = missing_data.sum() / len(df)
        results = {'missing_ratios': missing_ratio.to_dict(), 'patterns': {}, 'suspected_type': {}}
        for col in df.columns:
            if missing_data[col].sum() > 0:
                col_missing_ratio = missing_ratio[col]
                if col_missing_ratio < 0.1:
                    results['suspected_type'][col] = 'MCAR (可能性あり)'
                else:
                    other_cols = [c for c in df.columns if c != col]
                    if len(other_cols) > 0:
                        missing_flag = missing_data[col].astype(int)
                        correlations = {}
                        for other_col in other_cols:
                            if is_numeric_dtype(df[other_col]):
                                try:
                                    corr = df[other_col].corr(missing_flag)
                                    if not np.isnan(corr):
                                        correlations[other_col] = abs(corr)
                                except:
                                    pass
                        if correlations and max(correlations.values()) > 0.3:
                            results['suspected_type'][col] = 'MAR (可能性あり)'
                        else:
                            results['suspected_type'][col] = 'MNAR (可能性あり)'
        return results

    def rule_based_anomaly_detection(self, df, rules=None):
        if rules is None:
            return pd.DataFrame()
        anomalies = []
        for col, rule in rules.items():
            if col not in df.columns:
                continue
            col_data = df[col]
            if 'min' in rule:
                min_val = rule['min']
                mask_min = col_data < min_val
                if mask_min.any():
                    for idx in df.index[mask_min]:
                        anomalies.append({'行番号': idx, '列名': col, '値': col_data.loc[idx], '異常理由': f'最小値 {min_val} 未満'})
            if 'max' in rule:
                max_val = rule['max']
                mask_max = col_data > max_val
                if mask_max.any():
                    for idx in df.index[mask_max]:
                        anomalies.append({'行番号': idx, '列名': col, '値': col_data.loc[idx], '異常理由': f'最大値 {max_val} 超過'})
            if 'allowed_values' in rule:
                allowed = rule['allowed_values']
                mask_allowed = ~col_data.isin(allowed)
                if mask_allowed.any():
                    for idx in df.index[mask_allowed]:
                        anomalies.append({'行番号': idx, '列名': col, '値': col_data.loc[idx], '異常理由': f'許可されていない値（許可値: {allowed}）'})
        if len(anomalies) > 0:
            return pd.DataFrame(anomalies)
        else:
            return pd.DataFrame(columns=['行番号', '列名', '値', '異常理由'])

    def remove_outliers_advanced(self, df, method='one_class_svm', columns=None, contamination=0.1, nu=0.1, gamma='scale', n_neighbors=20, action='remove'):
        df = df.copy()
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) == 0:
            return df
        df_temp = df[columns].copy()
        df_temp = df_temp.fillna(df_temp.median())
        if method == 'one_class_svm':
            try:
                from sklearn.svm import OneClassSVM
                iso_svm = OneClassSVM(nu=nu, gamma=gamma)
                outliers = iso_svm.fit_predict(df_temp)
                if action == 'remove':
                    df = df[outliers == 1]
                    print(f'One-Class SVM: {np.sum(outliers == -1)}個の外れ値を検出・除去しました。')
                else:
                    for col in columns:
                        outlier_mask = outliers == -1
                        if outlier_mask.any():
                            median = df[col].median()
                            std = df[col].std()
                            df.loc[outlier_mask, col] = np.clip(df.loc[outlier_mask, col], median - 3 * std, median + 3 * std)
                    print(f'One-Class SVM: {np.sum(outliers == -1)}個の外れ値を検出・クリップしました。')
            except ImportError:
                print('警告: sklearnが必要です。One-Class SVMをスキップします。')
        elif method == 'lof':
            try:
                from sklearn.neighbors import LocalOutlierFactor
                lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
                outliers = lof.fit_predict(df_temp)
                if action == 'remove':
                    df = df[outliers == 1]
                    print(f'LOF: {np.sum(outliers == -1)}個の外れ値を検出・除去しました。')
                else:
                    for col in columns:
                        outlier_mask = outliers == -1
                        if outlier_mask.any():
                            median = df[col].median()
                            std = df[col].std()
                            df.loc[outlier_mask, col] = np.clip(df.loc[outlier_mask, col], median - 3 * std, median + 3 * std)
                    print(f'LOF: {np.sum(outliers == -1)}個の外れ値を検出・クリップしました。')
            except ImportError:
                print('警告: sklearnが必要です。LOFをスキップします。')
        return df

    def impute_missing_em(self, df, columns=None, max_iter=100, tol=0.001):
        df = df.copy()
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) == 0:
            return df
        try:
            df_temp = df[columns].copy()
            df_temp = df_temp.fillna(df_temp.mean())
            for iteration in range(max_iter):
                mean_old = df_temp.mean()
                cov_old = df_temp.cov()
                for col in columns:
                    missing_mask = df[col].isnull()
                    if missing_mask.any():
                        other_cols = [c for c in columns if c != col]
                        if len(other_cols) > 0:
                            X = df_temp.loc[~missing_mask, other_cols]
                            y = df_temp.loc[~missing_mask, col]
                            if len(X) > 0 and len(y) > 0:
                                try:
                                    from sklearn.linear_model import LinearRegression
                                    reg = LinearRegression()
                                    reg.fit(X, y)
                                    X_missing = df_temp.loc[missing_mask, other_cols]
                                    if len(X_missing) > 0:
                                        df_temp.loc[missing_mask, col] = reg.predict(X_missing)
                                except:
                                    df_temp.loc[missing_mask, col] = df_temp[col].mean()
                mean_new = df_temp.mean()
                if np.allclose(mean_old, mean_new, atol=tol):
                    print(f'EMアルゴリズム: {iteration + 1}回で収束しました')
                    break
            df[columns] = df_temp[columns]
            print(f'EMアルゴリズムによる欠損値補完を完了しました')
        except Exception as e:
            print(f'EMアルゴリズムエラー: {e}')
        return df

    def create_spline_features(self, df, columns=None, n_knots=3, degree=3):
        try:
            from scipy.interpolate import BSpline
            from scipy import stats
        except ImportError:
            print('警告: scipyが必要です。スプライン変換をスキップします。')
            return df
        df = df.copy()
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) == 0:
            return df
        try:
            for col in columns:
                data = df[col].dropna()
                if len(data) < n_knots + degree + 1:
                    continue
                knots = np.linspace(data.min(), data.max(), n_knots + 2)[1:-1]
                for i in range(n_knots):
                    df[f'{col}_spline_{i}'] = np.maximum(0, (df[col] - knots[i]) ** degree)
            print(f'スプライン変換を実行しました: {len(columns)}列')
        except Exception as e:
            print(f'スプライン変換エラー: {e}')
        return df

    def calculate_woe(self, df, feature_col, target_col, n_bins=5):
        if feature_col not in df.columns or target_col not in df.columns:
            print('警告: 指定された列が見つかりません。')
            return pd.DataFrame()
        try:
            df_temp = df[[feature_col, target_col]].copy()
            df_temp = df_temp.dropna()
            if len(df_temp) == 0:
                return pd.DataFrame()
            df_temp['bin'] = pd.qcut(df_temp[feature_col], q=n_bins, duplicates='drop', labels=False)
            woe_data = []
            for bin_id in df_temp['bin'].unique():
                if pd.isna(bin_id):
                    continue
                bin_data = df_temp[df_temp['bin'] == bin_id]
                good_count = (bin_data[target_col] == 0).sum() if len(bin_data[target_col].unique()) == 2 else 0
                bad_count = (bin_data[target_col] == 1).sum() if len(bin_data[target_col].unique()) == 2 else len(bin_data)
                total_good = (df_temp[target_col] == 0).sum() if len(df_temp[target_col].unique()) == 2 else 0
                total_bad = (df_temp[target_col] == 1).sum() if len(df_temp[target_col].unique()) == 2 else len(df_temp)
                if total_good > 0 and total_bad > 0 and (good_count > 0) and (bad_count > 0):
                    woe = np.log(bad_count / total_bad / (good_count / total_good))
                    woe_data.append({'bin': bin_id, 'woe': woe, 'good_count': good_count, 'bad_count': bad_count})
            return pd.DataFrame(woe_data)
        except Exception as e:
            print(f'WOE計算エラー: {e}')
            return pd.DataFrame()

    def select_features_mutual_info(self, df, target_col, k='auto', discrete_features='auto'):
        try:
            from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
        except ImportError:
            print('警告: sklearnが必要です。相互情報量による特徴量選択をスキップします。')
            return df
        if target_col not in df.columns:
            return df
        feature_cols = [col for col in self.numerical_columns if col in df.columns and col != target_col]
        if len(feature_cols) == 0:
            return df
        X = df[feature_cols]
        y = df[target_col]
        y_is_numeric = is_numeric_dtype(y)
        if not y_is_numeric:
            y_numeric = pd.to_numeric(y, errors='coerce')
            if y_numeric.notna().mean() > 0.9:
                y = y_numeric
                y_is_numeric = True
        if y_is_numeric and len(y.unique()) > 10:
            mi_scores = mutual_info_regression(X, y, discrete_features=discrete_features)
            problem_type = 'regression'
        else:
            mi_scores = mutual_info_classif(X, y, discrete_features=discrete_features)
            problem_type = 'classification'
        feature_scores = list(zip(feature_cols, mi_scores))
        feature_scores.sort(key=lambda x: x[1], reverse=True)
        if k == 'auto':
            k = min(len(feature_cols), 10)
        selected_features = [feat for feat, score in feature_scores[:k]]
        self.selected_features = selected_features
        df_selected = df[selected_features + [target_col]].copy()
        print(f'相互情報量による特徴量選択: {len(selected_features)}個の特徴量を選択')
        return df_selected

    def select_features_rfe(self, df, target_col, estimator=None, n_features_to_select=None, step=1):
        try:
            from sklearn.feature_selection import RFE
            from sklearn.linear_model import LogisticRegression, LinearRegression
        except ImportError:
            print('警告: sklearnが必要です。RFEによる特徴量選択をスキップします。')
            return df
        if target_col not in df.columns:
            return df
        feature_cols = [col for col in self.numerical_columns if col in df.columns and col != target_col]
        if len(feature_cols) == 0:
            return df
        X = df[feature_cols].fillna(df[feature_cols].median())
        y = df[target_col]
        if estimator is None:
            y_is_numeric = is_numeric_dtype(y)
            if not y_is_numeric:
                y_numeric = pd.to_numeric(y, errors='coerce')
                if y_numeric.notna().mean() > 0.9:
                    y = y_numeric
                    y_is_numeric = True
            if not y_is_numeric or len(y.unique()) <= 10:
                estimator = LogisticRegression(max_iter=1000, random_state=42)
            else:
                estimator = LinearRegression()
        if n_features_to_select is None:
            n_features_to_select = min(len(feature_cols), 10)
        rfe = RFE(estimator=estimator, n_features_to_select=n_features_to_select, step=step)
        rfe.fit(X, y)
        selected_features = [feature_cols[i] for i in range(len(feature_cols)) if rfe.support_[i]]
        self.selected_features = selected_features
        self.feature_selector = rfe
        df_selected = df[selected_features + [target_col]].copy()
        print(f'RFEによる特徴量選択: {len(selected_features)}個の特徴量を選択')
        return df_selected

    def reduce_dimensions(self, df, method='pca', n_components=2, columns=None, target_col=None):
        df = df.copy()
        if columns is None:
            columns = self.numerical_columns
        columns = [col for col in columns if col in df.columns]
        if len(columns) == 0:
            return df
        df_temp = df[columns].fillna(df[columns].median())
        if method == 'pca':
            try:
                from sklearn.decomposition import PCA
                pca = PCA(n_components=n_components, random_state=42)
                transformed = pca.fit_transform(df_temp)
                for i in range(n_components):
                    df[f'PC{i + 1}'] = transformed[:, i]
                print(f'PCA: {len(columns)}次元 → {n_components}次元（寄与率: {pca.explained_variance_ratio_.sum():.2%}）')
            except ImportError:
                print('警告: sklearnが必要です。PCAをスキップします。')
        elif method == 'umap':
            try:
                import umap
                reducer = umap.UMAP(n_components=n_components, random_state=42)
                transformed = reducer.fit_transform(df_temp)
                for i in range(n_components):
                    df[f'UMAP{i + 1}'] = transformed[:, i]
                print(f'UMAP: {len(columns)}次元 → {n_components}次元')
            except ImportError:
                print('警告: umap-learnが必要です。UMAPをスキップします。')
        elif method == 'tsne':
            try:
                from sklearn.manifold import TSNE
                tsne = TSNE(n_components=n_components, random_state=42, perplexity=30)
                transformed = tsne.fit_transform(df_temp)
                for i in range(n_components):
                    df[f'tSNE{i + 1}'] = transformed[:, i]
                print(f't-SNE: {len(columns)}次元 → {n_components}次元')
            except ImportError:
                print('警告: sklearnが必要です。t-SNEをスキップします。')
        elif method == 'mca':
            try:
                from sklearn.decomposition import PCA
                from sklearn.preprocessing import LabelEncoder
                cat_cols = [col for col in self.categorical_columns if col in df.columns]
                if len(cat_cols) == 0:
                    print('警告: MCAにはカテゴリ変数が必要です。')
                    return df
                df_cat = df[cat_cols].copy()
                for col in cat_cols:
                    le = LabelEncoder()
                    df_cat[col] = le.fit_transform(df_cat[col].astype(str))
                pca = PCA(n_components=n_components, random_state=42)
                transformed = pca.fit_transform(df_cat)
                for i in range(n_components):
                    df[f'MCA{i + 1}'] = transformed[:, i]
                print(f'MCA: {len(cat_cols)}次元 → {n_components}次元')
            except ImportError:
                print('警告: sklearnが必要です。MCAをスキップします。')
        return df

    def optimize_threshold(self, y_true, y_pred_proba, metric='f1', pos_label=1):
        try:
            from sklearn.metrics import roc_curve, precision_recall_curve, f1_score, precision_score, recall_score
        except ImportError:
            print('警告: sklearnが必要です。しきい値最適化をスキップします。')
            return 0.5
        try:
            if metric == 'roc':
                fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba, pos_label=pos_label)
                optimal_idx = np.argmax(tpr - fpr)
                optimal_threshold = thresholds[optimal_idx]
            elif metric == 'pr':
                precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba, pos_label=pos_label)
                f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
                optimal_idx = np.argmax(f1_scores)
                optimal_threshold = thresholds[optimal_idx]
            elif metric == 'f1':
                thresholds = np.linspace(0, 1, 100)
                best_threshold = 0.5
                best_f1 = 0
                for threshold in thresholds:
                    y_pred = (y_pred_proba >= threshold).astype(int)
                    f1 = f1_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
                    if f1 > best_f1:
                        best_f1 = f1
                        best_threshold = threshold
                optimal_threshold = best_threshold
            elif metric == 'precision':
                thresholds = np.linspace(0, 1, 100)
                best_threshold = 0.5
                best_precision = 0
                for threshold in thresholds:
                    y_pred = (y_pred_proba >= threshold).astype(int)
                    precision = precision_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
                    if precision > best_precision:
                        best_precision = precision
                        best_threshold = threshold
                optimal_threshold = best_threshold
            elif metric == 'recall':
                thresholds = np.linspace(0, 1, 100)
                best_threshold = 0.5
                best_recall = 0
                for threshold in thresholds:
                    y_pred = (y_pred_proba >= threshold).astype(int)
                    recall = recall_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
                    if recall > best_recall:
                        best_recall = recall
                        best_threshold = threshold
                optimal_threshold = best_threshold
            else:
                optimal_threshold = 0.5
            print(f'最適なしきい値 ({metric}): {optimal_threshold:.4f}')
            return optimal_threshold
        except Exception as e:
            print(f'しきい値最適化エラー: {e}')
            return 0.5

def main():
    preprocessor = DataPreprocessor()
    print('DataPreprocessorクラスが利用可能です。')
    print('使用例については、example_usage.pyを参照してください。')
if __name__ == '__main__':
    main()

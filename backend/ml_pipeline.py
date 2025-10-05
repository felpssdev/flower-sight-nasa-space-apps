"""
FlowerSight ML Pipeline - Ensemble de Modelos para Predição de Floração
Usa LSTM + Random Forest + ANN com dados NDVI, GNDVI, SAVI e clima
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
import warnings
warnings.filterwarnings('ignore')

# Deep Learning
from tensorflow import keras
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, Input
from keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Machine Learning
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Data processing
import joblib
import xgboost as xgb


class SpectralIndexCalculator:
    """Calcula índices espectrais a partir de bandas de satélite"""
    
    @staticmethod
    def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
        """Normalized Difference Vegetation Index"""
        return (nir - red) / (nir + red + 1e-8)
    
    @staticmethod
    def gndvi(nir: np.ndarray, green: np.ndarray) -> np.ndarray:
        """Green NDVI - Sensível à clorofila"""
        return (nir - green) / (nir + green + 1e-8)
    
    @staticmethod
    def savi(nir: np.ndarray, red: np.ndarray, L: float = 0.5) -> np.ndarray:
        """Soil Adjusted Vegetation Index"""
        return ((nir - red) / (nir + red + L)) * (1 + L)
    
    @staticmethod
    def evi(nir: np.ndarray, red: np.ndarray, blue: np.ndarray) -> np.ndarray:
        """Enhanced Vegetation Index"""
        return 2.5 * ((nir - red) / (nir + 6*red - 7.5*blue + 1))


class FeatureEngineering:
    """Engenharia de features para predição de floração"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def extract_temporal_features(self, ndvi_series: np.ndarray, 
                                  window_sizes: List[int] = [7, 14, 30]) -> Dict:
        """
        Extrai features temporais da série NDVI
        
        Args:
            ndvi_series: Array com valores NDVI ao longo do tempo
            window_sizes: Tamanhos das janelas móveis
        
        Returns:
            Dict com features extraídas
        """
        features = {}
        
        # Estatísticas básicas
        features['ndvi_mean'] = np.mean(ndvi_series)
        features['ndvi_std'] = np.std(ndvi_series)
        features['ndvi_max'] = np.max(ndvi_series)
        features['ndvi_min'] = np.min(ndvi_series)
        
        # Percentis
        features['ndvi_p25'] = np.percentile(ndvi_series, 25)
        features['ndvi_p75'] = np.percentile(ndvi_series, 75)
        features['ndvi_p90'] = np.percentile(ndvi_series, 90)
        
        # Taxa de mudança (primeira derivada)
        if len(ndvi_series) > 1:
            ndvi_diff = np.diff(ndvi_series)
            features['ndvi_rate_mean'] = np.mean(ndvi_diff)
            features['ndvi_rate_max'] = np.max(ndvi_diff)
            features['ndvi_acceleration'] = np.mean(np.diff(ndvi_diff)) if len(ndvi_diff) > 1 else 0
        
        # Tendência linear
        if len(ndvi_series) >= 3:
            x = np.arange(len(ndvi_series))
            slope, _ = np.polyfit(x, ndvi_series, 1)
            features['ndvi_trend'] = slope
        
        # Janelas móveis
        for window in window_sizes:
            if len(ndvi_series) >= window:
                recent_mean = np.mean(ndvi_series[-window:])
                features[f'ndvi_last_{window}d'] = recent_mean
        
        return features
    
    def calculate_gdd(self, temp_series: np.ndarray, 
                     base_temp: float = 10.0) -> float:
        """
        Calcula Growing Degree Days acumulados
        
        Args:
            temp_series: Série de temperaturas médias diárias (°C)
            base_temp: Temperatura base para a cultura
        """
        gdd = np.sum(np.maximum(temp_series - base_temp, 0))
        return gdd
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara todas as features para o modelo (row-by-row)
        APRIMORADO: Inclui features temporais e de tendência
        
        Expected columns in data:
        - ndvi, gndvi, savi, evi, temperature, precipitation, date
        """
        features_list = []
        
        # Pré-calcular séries temporais para features avançadas
        if 'ndvi' in data.columns:
            ndvi_series = data['ndvi'].values
        if 'temperature' in data.columns:
            temp_series = data['temperature'].values
        
        # Processar cada linha individualmente
        for idx in range(len(data)):
            row_features = {}
            
            # ============================================================
            # 1. FEATURES ESPECTRAIS DIRETAS
            # ============================================================
            for col in ['ndvi', 'gndvi', 'savi', 'evi']:
                if col in data.columns:
                    row_features[col] = data[col].iloc[idx]
            
            # ============================================================
            # 2. FEATURES CLIMÁTICAS DIRETAS
            # ============================================================
            if 'temperature' in data.columns:
                row_features['temperature'] = data['temperature'].iloc[idx]
            
            if 'precipitation' in data.columns:
                row_features['precipitation'] = data['precipitation'].iloc[idx]
            
            # ============================================================
            # 3. FEATURES DE SAZONALIDADE
            # ============================================================
            if 'date' in data.columns:
                doy = data['date'].iloc[idx].timetuple().tm_yday
                row_features['day_of_year'] = doy
                row_features['sin_doy'] = np.sin(2 * np.pi * doy / 365)
                row_features['cos_doy'] = np.cos(2 * np.pi * doy / 365)
                
                # Fase do ciclo anual (0-1)
                row_features['annual_phase'] = (doy % 365) / 365
            
            # ============================================================
            # 4. FEATURES TEMPORAIS DE NDVI (Tendências e Velocidade)
            # ============================================================
            if 'ndvi' in data.columns:
                # Taxa de mudança (7, 14, 30 dias)
                if idx >= 7:
                    row_features['ndvi_change_7d'] = ndvi_series[idx] - ndvi_series[idx-7]
                else:
                    row_features['ndvi_change_7d'] = 0
                
                if idx >= 14:
                    row_features['ndvi_change_14d'] = ndvi_series[idx] - ndvi_series[idx-14]
                else:
                    row_features['ndvi_change_14d'] = 0
                
                if idx >= 30:
                    row_features['ndvi_change_30d'] = ndvi_series[idx] - ndvi_series[idx-30]
                else:
                    row_features['ndvi_change_30d'] = 0
                
                # Média móvel de NDVI (7, 14, 30 dias)
                window_7 = max(0, idx-7)
                window_14 = max(0, idx-14)
                window_30 = max(0, idx-30)
                
                row_features['ndvi_ma_7d'] = np.mean(ndvi_series[window_7:idx+1])
                row_features['ndvi_ma_14d'] = np.mean(ndvi_series[window_14:idx+1])
                row_features['ndvi_ma_30d'] = np.mean(ndvi_series[window_30:idx+1])
                
                # Aceleração de NDVI (mudança da mudança)
                if idx >= 14:
                    change_now = ndvi_series[idx] - ndvi_series[idx-7]
                    change_prev = ndvi_series[idx-7] - ndvi_series[idx-14]
                    row_features['ndvi_acceleration'] = change_now - change_prev
                else:
                    row_features['ndvi_acceleration'] = 0
            
            # ============================================================
            # 5. FEATURES CLIMÁTICAS TEMPORAIS
            # ============================================================
            if 'temperature' in data.columns:
                # Média móvel de temperatura (7, 14, 30 dias)
                window_7 = max(0, idx-7)
                window_14 = max(0, idx-14)
                window_30 = max(0, idx-30)
                
                row_features['temp_ma_7d'] = np.mean(temp_series[window_7:idx+1])
                row_features['temp_ma_14d'] = np.mean(temp_series[window_14:idx+1])
                row_features['temp_ma_30d'] = np.mean(temp_series[window_30:idx+1])
                
                # Tendência de temperatura
                if idx >= 14:
                    row_features['temp_trend'] = temp_series[idx] - temp_series[idx-14]
                else:
                    row_features['temp_trend'] = 0
            
            # ============================================================
            # 6. GDD ACUMULADO (Growing Degree Days)
            # ============================================================
            if 'temperature' in data.columns and idx > 0:
                temp_history = data['temperature'].iloc[:idx+1].values
                row_features['gdd_cumsum'] = self.calculate_gdd(temp_history)
            else:
                row_features['gdd_cumsum'] = 0
            
            # ============================================================
            # 7. FEATURES FENOLÓGICAS (NOVO - Para qualquer época do ano)
            # ============================================================
            if 'ndvi' in data.columns and 'date' in data.columns:
                # Histórico de 12 meses de NDVI (se disponível)
                current_date = data['date'].iloc[idx]
                
                # NDVI histórico (30, 60, 90, 180, 365 dias atrás)
                for lookback_days in [30, 60, 90, 180, 365]:
                    historical_idx = idx - lookback_days
                    if historical_idx >= 0:
                        row_features[f'ndvi_lag_{lookback_days}d'] = ndvi_series[historical_idx]
                    else:
                        row_features[f'ndvi_lag_{lookback_days}d'] = ndvi_series[0]
                
                # NDVI relativo (comparado com média histórica)
                if idx >= 30:
                    historical_mean = np.mean(ndvi_series[max(0, idx-365):idx])
                    row_features['ndvi_relative'] = ndvi_series[idx] / (historical_mean + 1e-6)
                else:
                    row_features['ndvi_relative'] = 1.0
                
                # Fase fenológica inferida (0=dormência, 1=crescimento, 2=pico)
                if idx >= 30:
                    recent_mean = np.mean(ndvi_series[max(0, idx-30):idx+1])
                    if recent_mean < 0.2:
                        row_features['phenology_phase'] = 0  # Dormência
                    elif recent_mean < 0.5:
                        row_features['phenology_phase'] = 1  # Crescimento
                    else:
                        row_features['phenology_phase'] = 2  # Pico vegetativo
                else:
                    row_features['phenology_phase'] = 1
                
                # Taxa de mudança de longo prazo (30-60 dias)
                if idx >= 60:
                    ndvi_30d_ago = ndvi_series[idx-30]
                    ndvi_60d_ago = ndvi_series[idx-60]
                    row_features['ndvi_longterm_change'] = ndvi_30d_ago - ndvi_60d_ago
                else:
                    row_features['ndvi_longterm_change'] = 0
            
            features_list.append(row_features)
        
        features_df = pd.DataFrame(features_list)
        
        return features_df
    
    def _count_consecutive_zeros(self, arr: np.ndarray) -> int:
        """Conta dias consecutivos sem chuva"""
        count = 0
        for val in reversed(arr):
            if val == 0:
                count += 1
            else:
                break
        return count


class LSTMBloomPredictor:
    """Modelo LSTM para predição de série temporal"""
    
    def __init__(self, sequence_length: int = 60):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler()
        
    def build_model(self, n_features: int = 1):
        """Constrói arquitetura LSTM"""
        model = Sequential([
            Input(shape=(self.sequence_length, n_features)),
            LSTM(128, return_sequences=True),
            Dropout(0.3),
            LSTM(64),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dense(1)  # Predição: dias até floração
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def prepare_sequences(self, data: np.ndarray, 
                         target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara sequências temporais para LSTM"""
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(target[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 100, batch_size: int = 32):
        """Treina modelo LSTM"""
        
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predição"""
        return self.model.predict(X, verbose=0).flatten()


class RandomForestBloomPredictor:
    """Modelo Random Forest para predição robusta"""
    
    def __init__(self, n_estimators: int = 200):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.feature_importance = None
    
    def train(self, X_train: pd.DataFrame, y_train: np.ndarray):
        """Treina Random Forest"""
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled, y_train)
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predição"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Retorna importância das features"""
        return self.feature_importance


class ANNBloomPredictor:
    """Rede Neural Feedforward para predição"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    def build_model(self, n_features: int):
        """Constrói arquitetura ANN"""
        model = Sequential([
            Input(shape=(n_features,)),
            Dense(128, activation='relu'),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dense(1)  # Dias até floração
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def train(self, X_train: pd.DataFrame, y_train: np.ndarray,
              X_val: pd.DataFrame, y_val: np.ndarray,
              epochs: int = 100, batch_size: int = 32):
        """Treina ANN"""
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        history = self.model.fit(
            X_train_scaled, y_train,
            validation_data=(X_val_scaled, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predição"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled, verbose=0).flatten()


class XGBoostBloomPredictor:
    """
    XGBoost Bloom Predictor - Otimizado para séries temporais
    Melhor para capturar padrões sazonais e relações não-lineares
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    def build_model(self, n_features: int):
        """Constrói modelo XGBoost otimizado"""
        self.model = xgb.XGBRegressor(
            n_estimators=500,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.01,  # L1 regularization
            reg_lambda=1.0,   # L2 regularization
            random_state=42,
            n_jobs=-1,
            tree_method='hist',  # Mais rápido
            early_stopping_rounds=30
        )
        return self.model
    
    def train(self, X_train: pd.DataFrame, y_train: np.ndarray,
              X_val: pd.DataFrame, y_val: np.ndarray):
        """Treina XGBoost com validação"""
        
        # Escalar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Treinar com early stopping
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_val_scaled, y_val)],
            verbose=False
        )
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predição"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Retorna importância das features"""
        if self.model is None:
            return None
        
        importance = self.model.feature_importances_
        return pd.DataFrame({
            'feature': range(len(importance)),
            'importance': importance
        }).sort_values('importance', ascending=False)


class FlowerSightEnsemble:
    """
    Ensemble de modelos LSTM + Random Forest + ANN + XGBoost
    Combina predições com pesos otimizados
    APRIMORADO: XGBoost para capturar padrões sazonais complexos
    """
    
    def __init__(self):
        self.lstm_model = LSTMBloomPredictor(sequence_length=60)
        self.rf_model = RandomForestBloomPredictor(n_estimators=200)
        self.ann_model = ANNBloomPredictor()
        self.xgb_model = XGBoostBloomPredictor()  # NOVO
        self.feature_eng = FeatureEngineering()
        
        # Pesos do ensemble otimizados
        # XGBoost é excelente para features fenológicas e sazonalidade
        self.weights = {
            'lstm': 0.10,  # Reduzido (alta variância)
            'rf': 0.30,    # Reduzido (bom, mas menos flexível)
            'ann': 0.15,   # Reduzido (performance média)
            'xgb': 0.45    # NOVO - Maior peso (melhor para sazonalidade)
        }
        
        self.is_trained = False
    
    def train(self, data: pd.DataFrame, target: np.ndarray,
              val_split: float = 0.2):
        """
        Treina todos os modelos do ensemble
        
        Args:
            data: DataFrame com colunas ndvi, gndvi, savi, temperature, etc
            target: Array com dias até floração (ground truth)
            val_split: Proporção para validação
        """
        
        print("=" * 60)
        print("TREINANDO FLOWERSIGHT ENSEMBLE")
        print("=" * 60)
        
        # 1. Preparar features agregadas para RF e ANN
        print("\n[1/4] Preparando features...")
        features_df = self.feature_eng.prepare_features(data)
        
        # Split train/val
        X_train_agg, X_val_agg, y_train, y_val = train_test_split(
            features_df, target, test_size=val_split, random_state=42
        )
        
        # 2. Treinar Random Forest
        print("\n[2/4] Treinando Random Forest...")
        self.rf_model.train(X_train_agg, y_train)
        rf_val_pred = self.rf_model.predict(X_val_agg)
        rf_mae = mean_absolute_error(y_val, rf_val_pred)
        print(f"✓ Random Forest - MAE: {rf_mae:.2f} dias")
        
        # 3. Treinar XGBoost (NOVO)
        print("\n[3/5] Treinando XGBoost...")
        self.xgb_model.build_model(n_features=X_train_agg.shape[1])
        self.xgb_model.train(X_train_agg, y_train, X_val_agg, y_val)
        xgb_val_pred = self.xgb_model.predict(X_val_agg)
        xgb_mae = mean_absolute_error(y_val, xgb_val_pred)
        print(f"✓ XGBoost - MAE: {xgb_mae:.2f} dias")
        
        # 4. Treinar ANN
        print("\n[4/5] Treinando ANN...")
        self.ann_model.build_model(n_features=X_train_agg.shape[1])
        self.ann_model.train(X_train_agg, y_train, X_val_agg, y_val, epochs=100)
        ann_val_pred = self.ann_model.predict(X_val_agg)
        ann_mae = mean_absolute_error(y_val, ann_val_pred)
        print(f"✓ ANN - MAE: {ann_mae:.2f} dias")
        
        # 5. Treinar LSTM (requer sequências temporais)
        print("\n[5/5] Treinando LSTM...")
        if 'ndvi' in data.columns:
            ndvi_data = data['ndvi'].values.reshape(-1, 1)
            X_seq, y_seq = self.lstm_model.prepare_sequences(ndvi_data, target)
            
            # Split sequencial
            split_idx = int(len(X_seq) * (1 - val_split))
            X_train_seq, X_val_seq = X_seq[:split_idx], X_seq[split_idx:]
            y_train_seq, y_val_seq = y_seq[:split_idx], y_seq[split_idx:]
            
            self.lstm_model.build_model(n_features=1)
            self.lstm_model.train(X_train_seq, y_train_seq, 
                                X_val_seq, y_val_seq, epochs=100)
            
            lstm_val_pred = self.lstm_model.predict(X_val_seq)
            lstm_mae = mean_absolute_error(y_val_seq, lstm_val_pred)
            print(f"✓ LSTM - MAE: {lstm_mae:.2f} dias")
        
        # 5. Avaliar ensemble
        print("\n" + "=" * 60)
        print("AVALIAÇÃO DO ENSEMBLE")
        print("=" * 60)
        
        # Ensemble prediction (apenas onde temos todas as predições)
        min_len = min(len(rf_val_pred), len(ann_val_pred))
        ensemble_pred = (
            self.weights['rf'] * rf_val_pred[:min_len] +
            self.weights['ann'] * ann_val_pred[:min_len]
        )
        
        if 'ndvi' in data.columns and len(lstm_val_pred) > 0:
            # Ajustar tamanhos se necessário
            min_len = min(min_len, len(lstm_val_pred))
            ensemble_pred = (
                self.weights['lstm'] * lstm_val_pred[:min_len] +
                self.weights['rf'] * rf_val_pred[:min_len] +
                self.weights['ann'] * ann_val_pred[:min_len] +
                self.weights['xgb'] * xgb_val_pred[:min_len]
            )
        
        ensemble_mae = mean_absolute_error(y_val[:min_len], ensemble_pred)
        ensemble_rmse = np.sqrt(mean_squared_error(y_val[:min_len], ensemble_pred))
        ensemble_r2 = r2_score(y_val[:min_len], ensemble_pred)
        
        print(f"\n📊 MÉTRICAS FINAIS:")
        print(f"   MAE:  {ensemble_mae:.2f} dias")
        print(f"   RMSE: {ensemble_rmse:.2f} dias")
        print(f"   R²:   {ensemble_r2:.3f}")
        print("=" * 60)
        
        self.is_trained = True
        
        return {
            'mae': ensemble_mae,
            'rmse': ensemble_rmse,
            'r2': ensemble_r2
        }
    
    def predict(self, data: pd.DataFrame) -> Dict:
        """
        Predição com ensemble + intervalo de confiança
        
        Returns:
            Dict com:
            - predicted_days: dias até floração (média ponderada)
            - confidence_interval: (lower, upper)
            - individual_predictions: dict com predição de cada modelo
        """
        
        if not self.is_trained:
            raise ValueError("Modelo não treinado! Execute .train() primeiro.")
        
        # Preparar features
        features_df = self.feature_eng.prepare_features(data)
        
        # Predições individuais
        predictions = {}
        
        # Random Forest
        predictions['rf'] = self.rf_model.predict(features_df)[0]
        
        # ANN
        predictions['ann'] = self.ann_model.predict(features_df)[0]
        
        # XGBoost (NOVO)
        predictions['xgb'] = self.xgb_model.predict(features_df)[0]
        
        # LSTM (se tiver dados de sequência)
        if 'ndvi' in data.columns and len(data) >= self.lstm_model.sequence_length:
            ndvi_seq = data['ndvi'].values[-self.lstm_model.sequence_length:].reshape(1, -1, 1)
            predictions['lstm'] = self.lstm_model.predict(ndvi_seq)[0]
        
        # Ensemble (média ponderada)
        if 'lstm' in predictions:
            predicted_days = (
                self.weights['lstm'] * predictions['lstm'] +
                self.weights['rf'] * predictions['rf'] +
                self.weights['ann'] * predictions['ann'] +
                self.weights['xgb'] * predictions['xgb']
            )
        else:
            # Sem LSTM, redistribuir pesos
            total_weight = self.weights['rf'] + self.weights['ann'] + self.weights['xgb']
            w_rf = self.weights['rf'] / total_weight
            w_ann = self.weights['ann'] / total_weight
            w_xgb = self.weights['xgb'] / total_weight
            predicted_days = (
                w_rf * predictions['rf'] + 
                w_ann * predictions['ann'] + 
                w_xgb * predictions['xgb']
            )
        
        # Intervalo de confiança baseado na variância entre modelos
        pred_values = list(predictions.values())
        std_dev = np.std(pred_values)
        ci_lower = predicted_days - 1.96 * std_dev
        ci_upper = predicted_days + 1.96 * std_dev
        
        # Agreement score: quanto mais próximos os modelos, maior o score (0-1)
        # Usa coeficiente de variação invertido com normalização robusta
        mean_pred = np.mean(pred_values)
        if mean_pred > 0:
            # Coefficient of Variation (CV): std_dev / mean
            cv = std_dev / mean_pred
            # Normalizar para [0, 1]: quanto menor o CV, maior o agreement
            # CV < 0.1 (10%) = excelente (>90%)
            # CV = 0.5 (50%) = moderado (~60%)
            # CV > 1.0 (100%) = péssimo (<40%)
            agreement_score = max(0.0, min(1.0, 1 / (1 + cv)))
        else:
            agreement_score = 0.0
        
        return {
            'predicted_days': int(np.round(predicted_days)),
            'confidence_interval': (int(np.round(ci_lower)), int(np.round(ci_upper))),
            'individual_predictions': predictions,
            'agreement_score': float(agreement_score),
            'model_std_dev': float(std_dev),  # Para debug
            'model_mean': float(mean_pred)  # Para debug
        }
    
    def save_models(self, path: str = 'models/'):
        """Salva modelos treinados"""
        import os
        os.makedirs(path, exist_ok=True)
        
        # Salvar modelos Keras
        self.lstm_model.model.save(f'{path}lstm_model.h5')
        self.ann_model.model.save(f'{path}ann_model.h5')
        
        # Salvar Random Forest, XGBoost e scalers
        joblib.dump(self.rf_model.model, f'{path}rf_model.pkl')
        joblib.dump(self.xgb_model.model, f'{path}xgb_model.pkl')
        joblib.dump(self.rf_model.scaler, f'{path}rf_scaler.pkl')
        joblib.dump(self.xgb_model.scaler, f'{path}xgb_scaler.pkl')
        joblib.dump(self.ann_model.scaler, f'{path}ann_scaler.pkl')
        joblib.dump(self.lstm_model.scaler, f'{path}lstm_scaler.pkl')
        
        print(f"✓ Modelos salvos em {path}")
    
    def load_models(self, path: str = 'models/'):
        """Carrega modelos salvos"""
        from keras.models import load_model
        
        self.lstm_model.model = load_model(f'{path}lstm_model.h5')
        self.ann_model.model = load_model(f'{path}ann_model.h5')
        self.rf_model.model = joblib.load(f'{path}rf_model.pkl')
        self.xgb_model.model = joblib.load(f'{path}xgb_model.pkl')
        self.rf_model.scaler = joblib.load(f'{path}rf_scaler.pkl')
        self.xgb_model.scaler = joblib.load(f'{path}xgb_scaler.pkl')
        self.ann_model.scaler = joblib.load(f'{path}ann_scaler.pkl')
        self.lstm_model.scaler = joblib.load(f'{path}lstm_scaler.pkl')
        
        self.is_trained = True
        print(f"✓ Modelos carregados de {path}")


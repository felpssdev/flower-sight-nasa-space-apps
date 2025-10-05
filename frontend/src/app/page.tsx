'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import {
  Leaf,
  Calendar,
  TrendingUp,
  AlertCircle,
  ChevronDown,
  Loader2,
  MapPin,
  Info,
  Map as MapIcon,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'

// ============================================================================
// CONFIG
// ============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Dynamic import do mapa (evita SSR issues)
const MapComponent = dynamic(() => import('./components/Map'), {
  ssr: false,
  loading: () => (
    <div className="h-full flex items-center justify-center bg-gray-100">
      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
    </div>
  ),
})

// ============================================================================
// TYPES
// ============================================================================

interface PredictionResult {
  days_until_bloom: number
  predicted_bloom_date: string
  confidence_low: string
  confidence_high: string
  agreement_score: number
  farm_name: string
  crop_type: string
  location: { lat: number; lon: number }
  individual_predictions?: {
    lstm: number
    rf: number
    ann: number
    xgb?: number
  }
  ndvi_trend: Array<{ date: string; ndvi: number }>
  recommendations?: string[]
  phenology_stage?: string
  phenology_stage_name?: string
  phenology_confidence?: number
  phenology_message?: string
  can_predict_bloom?: boolean
  estimated_bloom_window?: {
    earliest: string
    latest: string
    confidence: string
  }
}

interface Farm {
  id: string
  name: string
  crop: string
  lat: number
  lon: number
  location: string
  icon?: string
  color?: string
}

// ============================================================================
// DATA
// ============================================================================

const FARMS: Farm[] = [
  {
    id: 'almond',
    name: 'Central Valley Almond',
    crop: 'almond', // Backend usa lowercase
    lat: 36.7468,
    lon: -119.7726,
    location: 'California, USA',
  },
  {
    id: 'apple',
    name: 'Yakima Valley Orchard',
    crop: 'apple', // Backend usa lowercase
    lat: 46.6021,
    lon: -120.5059,
    location: 'Washington, USA',
  },
  {
    id: 'cherry',
    name: 'Michigan Cherry Farm',
    crop: 'cherry', // Backend usa lowercase
    lat: 44.7631,
    lon: -85.6206,
    location: 'Michigan, USA',
  },
  {
    id: 'chile-apple',
    name: 'Valle Central Apple',
    crop: 'apple', // Backend usa lowercase
    lat: -35.0,
    lon: -71.5,
    location: 'Curicó, Chile 🇨🇱',
    icon: '🌸',
    color: 'emerald',
  },
]

const LOADING_STEPS = [
  { label: 'Conectando à NASA...', duration: 500 },
  { label: 'Coletando dados NDVI...', duration: 1500 },
  { label: 'Analisando clima...', duration: 1000 },
  { label: 'Processando features...', duration: 800 },
  { label: 'Executando modelos...', duration: 1200 },
  { label: 'Calculando confiança...', duration: 500 },
]

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function FlowerSight() {
  const [selectedFarm, setSelectedFarm] = useState<Farm | null>(null)
  const [prediction, setPrediction] = useState<PredictionResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [showMap, setShowMap] = useState(false)

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const animateSteps = async () => {
    for (let i = 0; i < LOADING_STEPS.length; i++) {
      setLoadingStep(i)
      await new Promise((resolve) =>
        setTimeout(resolve, LOADING_STEPS[i].duration),
      )
    }
  }

  const handlePredict = async (farm: Farm) => {
    setIsLoading(true)
    setLoadingStep(0)
    setPrediction(null)

    try {
      const totalDuration = LOADING_STEPS.reduce(
        (sum, step) => sum + step.duration,
        0,
      )

      const animationPromise = animateSteps()
      const apiPromise = fetch(`${API_URL}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          farm_name: farm.name,
          crop_type: farm.crop, // CORRIGIDO: usa farm.crop em vez de farm.id
          lat: farm.lat,
          lon: farm.lon,
        }),
      }).then((res) => res.json())

      await Promise.all([
        animationPromise,
        new Promise((resolve) => setTimeout(resolve, totalDuration)),
      ])

      const data = await apiPromise
      setPrediction(data)
    } catch (error) {
      console.error('Erro:', error)
      alert('Erro ao buscar previsão')
    } finally {
      setIsLoading(false)
      setLoadingStep(0)
    }
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[9999] flex items-center justify-center">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
            <div className="flex items-center gap-4 mb-6">
              <Loader2 className="w-8 h-8 animate-spin text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Processando Previsão
                </h3>
                <p className="text-sm text-gray-500">
                  {LOADING_STEPS[loadingStep]?.label}
                </p>
              </div>
            </div>
            <div className="space-y-2">
              {LOADING_STEPS.map((step, idx) => (
                <div
                  key={idx}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    idx < loadingStep
                      ? 'bg-green-600'
                      : idx === loadingStep
                        ? 'bg-green-400'
                        : 'bg-gray-200'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
              <Leaf className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">FlowerSight</h1>
              <p className="text-xs text-gray-500">
                Previsão de Floração por IA
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Map Toggle */}
            <button
              onClick={() => setShowMap(!showMap)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                showMap
                  ? 'bg-green-100 text-green-700 border border-green-300'
                  : 'bg-white text-gray-700 border border-gray-300 hover:border-gray-400'
              }`}
            >
              <MapIcon className="w-4 h-4" />
              <span className="hidden sm:inline">Mapa</span>
            </button>

            {/* Farm Selector */}
            <div className="relative">
              <select
                value={selectedFarm?.id || ''}
                onChange={(e) => {
                  const farm = FARMS.find((f) => f.id === e.target.value)
                  if (farm) {
                    setSelectedFarm(farm)
                    setPrediction(null)
                  }
                }}
                className="appearance-none bg-white border border-gray-300 rounded-xl px-4 py-2.5 pr-10 text-sm font-medium text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all cursor-pointer"
              >
                <option value="">Selecionar Fazenda</option>
                {FARMS.map((farm) => (
                  <option key={farm.id} value={farm.id}>
                    {farm.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>
        </div>
      </header>

      {/* Map Section (collapsible) */}
      {showMap && (
        <div className="border-b border-gray-200 bg-white">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <div className="h-[500px] rounded-2xl overflow-hidden border border-gray-200 shadow-lg">
              <MapComponent
                farms={FARMS.map((f) => ({
                  ...f,
                  icon:
                    f.crop === 'Almond'
                      ? '🌰'
                      : f.crop === 'Apple'
                        ? '🍎'
                        : '🍒',
                  color:
                    f.crop === 'Almond'
                      ? '#8b5a3c'
                      : f.crop === 'Apple'
                        ? '#ef4444'
                        : '#dc2626',
                }))}
                selectedFarm={
                  selectedFarm
                    ? {
                        ...selectedFarm,
                        icon:
                          selectedFarm.crop === 'Almond'
                            ? '🌰'
                            : selectedFarm.crop === 'Apple'
                              ? '🍎'
                              : '🍒',
                        color:
                          selectedFarm.crop === 'Almond'
                            ? '#8b5a3c'
                            : selectedFarm.crop === 'Apple'
                              ? '#ef4444'
                              : '#dc2626',
                      }
                    : null
                }
                onSelectFarm={(farm) => {
                  if (farm) {
                    // Encontrar a fazenda original sem icon/color
                    const originalFarm = FARMS.find((f) => f.id === farm.id)
                    if (originalFarm) {
                      setSelectedFarm(originalFarm)
                      setPrediction(null)
                    }
                  }
                }}
                isLoading={isLoading}
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {!selectedFarm ? (
          // Empty State
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center">
              <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MapPin className="w-10 h-10 text-gray-400" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Selecione uma Fazenda
              </h2>
              <p className="text-gray-500 mb-6">
                Escolha uma fazenda no menu acima para iniciar a análise
              </p>
            </div>
          </div>
        ) : !prediction ? (
          // Farm Selected - No Prediction Yet
          <div className="space-y-6">
            {/* Farm Card */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-1">
                    {selectedFarm.name}
                  </h2>
                  <p className="text-sm text-gray-500 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" />
                    {selectedFarm.location}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-500 mb-1">Cultura</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {selectedFarm.crop}
                  </div>
                </div>
              </div>

              <button
                onClick={() => handlePredict(selectedFarm)}
                className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-semibold py-4 rounded-xl transition-all shadow-lg shadow-green-500/30 hover:shadow-xl hover:shadow-green-500/40"
              >
                Iniciar Análise de Floração
              </button>
            </div>
          </div>
        ) : (
          // Prediction Results
          <div className="space-y-6">
            {/* Phenology Alert (if can't predict) */}
            {prediction.can_predict_bloom === false && (
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <AlertCircle className="w-6 h-6 text-amber-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-900 mb-2">
                      Previsão de ML Não Disponível
                    </h3>
                    <p className="text-sm text-gray-700 mb-4">
                      <strong>Estágio Atual:</strong>{' '}
                      {prediction.phenology_stage_name}
                    </p>
                    <div className="bg-white/60 rounded-xl p-4 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {prediction.phenology_message}
                    </div>
                    {prediction.estimated_bloom_window && (
                      <div className="mt-4 flex items-center gap-4">
                        <div className="flex-1 bg-white/60 rounded-xl p-3">
                          <div className="text-xs text-gray-600 mb-1">
                            Janela Estimada
                          </div>
                          <div className="font-semibold text-gray-900">
                            {new Date(
                              prediction.estimated_bloom_window.earliest,
                            ).toLocaleDateString('pt-BR', {
                              month: 'short',
                            })}{' '}
                            -{' '}
                            {new Date(
                              prediction.estimated_bloom_window.latest,
                            ).toLocaleDateString('pt-BR', {
                              month: 'short',
                              year: 'numeric',
                            })}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ML Prediction (if available) */}
            {prediction.can_predict_bloom !== false && (
              <>
                {/* Main KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Days Until Bloom */}
                  <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-6 text-white col-span-1 md:col-span-2">
                    <div className="flex items-center gap-2 mb-4">
                      <Calendar className="w-5 h-5 opacity-90" />
                      <span className="text-sm font-medium opacity-90">
                        Previsão de Floração
                      </span>
                    </div>
                    <div className="text-6xl font-black mb-2">
                      {prediction.days_until_bloom}
                    </div>
                    <div className="text-xl opacity-90 mb-6">
                      dias até a floração
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <div>
                        <div className="opacity-75 mb-1">Data Prevista</div>
                        <div className="font-semibold text-lg">
                          {new Date(
                            prediction.predicted_bloom_date,
                          ).toLocaleDateString('pt-BR', {
                            day: '2-digit',
                            month: 'long',
                          })}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Confidence */}
                  <div className="bg-white border border-gray-200 rounded-2xl p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <TrendingUp className="w-5 h-5 text-gray-600" />
                      <span className="text-sm font-medium text-gray-600">
                        Confiança do Modelo
                      </span>
                    </div>
                    <div className="text-5xl font-black text-gray-900 mb-4">
                      {Math.round(prediction.agreement_score * 100)}%
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full transition-all"
                        style={{
                          width: `${prediction.agreement_score * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Confidence Interval */}
                {prediction.confidence_low && prediction.confidence_high && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white border border-gray-200 rounded-2xl p-5">
                      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        Mais Cedo
                      </div>
                      <div className="text-3xl font-bold text-gray-900">
                        {new Date(prediction.confidence_low).toLocaleDateString(
                          'pt-BR',
                          {
                            day: '2-digit',
                            month: 'short',
                          },
                        )}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Intervalo 95%
                      </div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded-2xl p-5">
                      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        Mais Tarde
                      </div>
                      <div className="text-3xl font-bold text-gray-900">
                        {new Date(
                          prediction.confidence_high,
                        ).toLocaleDateString('pt-BR', {
                          day: '2-digit',
                          month: 'short',
                        })}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Intervalo 95%
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* NDVI Chart */}
            {prediction.ndvi_trend && prediction.ndvi_trend.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-6">
                  <Leaf className="w-5 h-5 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    Evolução NDVI (NASA)
                  </h3>
                  <div className="ml-auto">
                    <button className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1">
                      <Info className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="h-64 mb-6">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={prediction.ndvi_trend}
                      margin={{ top: 5, right: 5, left: -20, bottom: 5 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#e5e7eb"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 11, fill: '#6b7280' }}
                        tickFormatter={(date: string) =>
                          new Date(date).toLocaleDateString('pt-BR', {
                            day: '2-digit',
                            month: 'short',
                          })
                        }
                        axisLine={{ stroke: '#e5e7eb' }}
                        tickLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 11, fill: '#6b7280' }}
                        domain={[0, 0.8]}
                        tickFormatter={(value: number) => value.toFixed(2)}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(255,255,255,0.98)',
                          border: '1px solid #e5e7eb',
                          borderRadius: '12px',
                          fontSize: '12px',
                          padding: '12px',
                          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                        }}
                        formatter={(value: number) => [
                          value.toFixed(4),
                          'NDVI',
                        ]}
                        labelFormatter={(label: string) =>
                          new Date(label).toLocaleDateString('pt-BR')
                        }
                      />
                      <Line
                        type="monotone"
                        dataKey="ndvi"
                        stroke="#10b981"
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 5, fill: '#10b981' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* NDVI Stats */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-gray-50 rounded-xl p-3 text-center">
                    <div className="text-xs text-gray-500 mb-1">Média</div>
                    <div className="text-lg font-bold text-gray-900">
                      {(
                        prediction.ndvi_trend.reduce(
                          (sum, p) => sum + p.ndvi,
                          0,
                        ) / prediction.ndvi_trend.length
                      ).toFixed(3)}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3 text-center">
                    <div className="text-xs text-gray-500 mb-1">Máximo</div>
                    <div className="text-lg font-bold text-green-600">
                      {Math.max(
                        ...prediction.ndvi_trend.map((p) => p.ndvi),
                      ).toFixed(3)}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3 text-center">
                    <div className="text-xs text-gray-500 mb-1">Mínimo</div>
                    <div className="text-lg font-bold text-orange-600">
                      {Math.min(
                        ...prediction.ndvi_trend.map((p) => p.ndvi),
                      ).toFixed(3)}
                    </div>
                  </div>
                  <div
                    className={`rounded-xl p-3 text-center ${
                      prediction.ndvi_trend.reduce(
                        (sum, p) => sum + p.ndvi,
                        0,
                      ) /
                        prediction.ndvi_trend.length >=
                      0.5
                        ? 'bg-green-50'
                        : prediction.ndvi_trend.reduce(
                              (sum, p) => sum + p.ndvi,
                              0,
                            ) /
                              prediction.ndvi_trend.length >=
                            0.3
                          ? 'bg-yellow-50'
                          : 'bg-red-50'
                    }`}
                  >
                    <div className="text-xs text-gray-500 mb-1">Status</div>
                    <div
                      className={`text-sm font-bold ${
                        prediction.ndvi_trend.reduce(
                          (sum, p) => sum + p.ndvi,
                          0,
                        ) /
                          prediction.ndvi_trend.length >=
                        0.5
                          ? 'text-green-700'
                          : prediction.ndvi_trend.reduce(
                                (sum, p) => sum + p.ndvi,
                                0,
                              ) /
                                prediction.ndvi_trend.length >=
                              0.3
                            ? 'text-yellow-700'
                            : 'text-red-700'
                      }`}
                    >
                      {prediction.ndvi_trend.reduce(
                        (sum, p) => sum + p.ndvi,
                        0,
                      ) /
                        prediction.ndvi_trend.length >=
                      0.5
                        ? '✓ OK'
                        : prediction.ndvi_trend.reduce(
                              (sum, p) => sum + p.ndvi,
                              0,
                            ) /
                              prediction.ndvi_trend.length >=
                            0.3
                          ? '○ Mod'
                          : '✕ Baixo'}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white/80 backdrop-blur-sm mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-sm text-gray-500">
          Powered by <strong>NASA Earth Data</strong> + Machine Learning (LSTM,
          Random Forest, ANN, XGBoost)
        </div>
      </footer>
    </div>
  )
}

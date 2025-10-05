'use client'

import { useState } from 'react'

interface PredictionData {
  farm_name: string
  crop_type: string
  location: { lat: number; lon: number }
  predicted_bloom_date: string
  confidence_low: string
  confidence_high: string
  days_until_bloom: number
  agreement_score: number
  recommendations: string[]
  ndvi_trend?: Array<{ date: string; ndvi: number }>
  individual_predictions: {
    lstm: number
    rf: number
    ann: number
  }
  historical_average?: string
  days_shift?: number
}

export default function Home() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PredictionData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedCrop, setSelectedCrop] = useState<string | null>(null)

  const handleQuickTest = async (crop: string) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setSelectedCrop(crop)

    try {
      const response = await fetch(
        `http://localhost:8000/api/predict/test/${crop}`,
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erro ao buscar predição')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-green-50 to-blue-50">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 text-gray-900">
            🌸 BloomWatch
          </h1>
          <p className="text-xl text-gray-800 font-medium mb-2">
            Predição de Floração com Dados NASA + Machine Learning
          </p>
          <p className="text-gray-700">
            Selecione uma cultura para ver a previsão de floração
          </p>
        </div>

        {/* Botões de Seleção */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Almond */}
          <button
            onClick={() => handleQuickTest('almond')}
            disabled={loading}
            className={`relative overflow-hidden bg-gradient-to-br from-amber-100 to-amber-200 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none border-4 ${
              selectedCrop === 'almond'
                ? 'border-amber-600'
                : 'border-transparent'
            }`}
          >
            <div className="text-6xl mb-4">🌰</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Almond</h3>
            <p className="text-gray-800 font-medium mb-1">Amêndoa</p>
            <p className="text-sm text-gray-700">Central Valley, CA</p>
            <p className="text-xs text-gray-600 mt-2">36.75°N, 119.77°W</p>
          </button>

          {/* Apple */}
          <button
            onClick={() => handleQuickTest('apple')}
            disabled={loading}
            className={`relative overflow-hidden bg-gradient-to-br from-red-100 to-red-200 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none border-4 ${
              selectedCrop === 'apple' ? 'border-red-600' : 'border-transparent'
            }`}
          >
            <div className="text-6xl mb-4">🍎</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Apple</h3>
            <p className="text-gray-800 font-medium mb-1">Maçã</p>
            <p className="text-sm text-gray-700">Yakima Valley, WA</p>
            <p className="text-xs text-gray-600 mt-2">46.60°N, 120.51°W</p>
          </button>

          {/* Cherry */}
          <button
            onClick={() => handleQuickTest('cherry')}
            disabled={loading}
            className={`relative overflow-hidden bg-gradient-to-br from-pink-100 to-pink-200 p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none border-4 ${
              selectedCrop === 'cherry'
                ? 'border-pink-600'
                : 'border-transparent'
            }`}
          >
            <div className="text-6xl mb-4">🍒</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Cherry</h3>
            <p className="text-gray-800 font-medium mb-1">Cereja</p>
            <p className="text-sm text-gray-700">Traverse City, MI</p>
            <p className="text-xs text-gray-600 mt-2">44.76°N, 85.62°W</p>
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white p-8 rounded-2xl shadow-lg text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
            <p className="text-xl font-semibold text-gray-900">
              Buscando dados NASA...
            </p>
            <p className="text-gray-700 mt-2">
              Coletando NDVI e dados climáticos em tempo real
            </p>
          </div>
        )}

        {/* Erro */}
        {error && !loading && (
          <div className="bg-red-50 border-2 border-red-400 text-red-800 p-6 rounded-2xl shadow-lg">
            <div className="flex items-center mb-2">
              <span className="text-3xl mr-3">❌</span>
              <strong className="text-xl">Erro</strong>
            </div>
            <p className="text-gray-900">{error}</p>
          </div>
        )}

        {/* Resultados */}
        {result && !loading && (
          <div className="bg-white p-8 rounded-2xl shadow-2xl">
            <h2 className="text-3xl font-bold mb-6 text-gray-900 text-center">
              📊 Resultado da Predição
            </h2>

            {/* Cards Principais */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl border-2 border-blue-200">
                <h3 className="font-semibold text-gray-900 mb-3 text-lg flex items-center">
                  <span className="text-2xl mr-2">🏡</span> Fazenda
                </h3>
                <p className="text-3xl font-bold text-blue-600 mb-2">
                  {result.farm_name}
                </p>
                <p className="text-gray-800 font-semibold">
                  {result.crop_type.toUpperCase()}
                </p>
                <p className="text-sm text-gray-700 mt-1">
                  {result.location.lat.toFixed(4)}°,{' '}
                  {result.location.lon.toFixed(4)}°
                </p>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border-2 border-green-200">
                <h3 className="font-semibold text-gray-900 mb-3 text-lg flex items-center">
                  <span className="text-2xl mr-2">🌸</span> Data de Floração
                </h3>
                <p className="text-3xl font-bold text-green-600 mb-2">
                  {result.predicted_bloom_date}
                </p>
                <p className="text-xl text-gray-800 font-semibold">
                  em {result.days_until_bloom} dias
                </p>
              </div>
            </div>

            {/* Intervalo de Confiança */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-xl mb-6 border-2 border-purple-200">
              <h3 className="font-semibold text-gray-900 mb-3 text-lg flex items-center">
                <span className="text-2xl mr-2">📊</span> Intervalo de Confiança
              </h3>
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <p className="text-sm text-gray-700 font-semibold">Mínimo</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {result.confidence_low}
                  </p>
                </div>
                <div className="text-4xl">↔️</div>
                <div>
                  <p className="text-sm text-gray-700 font-semibold">Máximo</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {result.confidence_high}
                  </p>
                </div>
              </div>
              <p className="text-gray-800 mt-4 font-medium">
                Concordância dos modelos:{' '}
                <span className="text-purple-700 font-bold">
                  {(result.agreement_score * 100).toFixed(1)}%
                </span>
              </p>
            </div>

            {/* Predições dos Modelos */}
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-4 text-lg flex items-center">
                <span className="text-2xl mr-2">🤖</span> Predições dos Modelos
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-100 p-4 rounded-xl text-center border-2 border-gray-300">
                  <p className="text-sm text-gray-800 font-bold mb-2">LSTM</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {result.individual_predictions.lstm.toFixed(1)}
                  </p>
                  <p className="text-xs text-gray-700 mt-1">dias</p>
                </div>
                <div className="bg-gray-100 p-4 rounded-xl text-center border-2 border-gray-300">
                  <p className="text-sm text-gray-800 font-bold mb-2">
                    Random Forest
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {result.individual_predictions.rf.toFixed(1)}
                  </p>
                  <p className="text-xs text-gray-700 mt-1">dias</p>
                </div>
                <div className="bg-gray-100 p-4 rounded-xl text-center border-2 border-gray-300">
                  <p className="text-sm text-gray-800 font-bold mb-2">ANN</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {result.individual_predictions.ann.toFixed(1)}
                  </p>
                  <p className="text-xs text-gray-700 mt-1">dias</p>
                </div>
              </div>
            </div>

            {/* Recomendações */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-4 text-lg flex items-center">
                  <span className="text-2xl mr-2">💡</span> Recomendações
                </h3>
                <ul className="space-y-3">
                  {result.recommendations.map((rec, idx) => (
                    <li
                      key={idx}
                      className="bg-yellow-50 p-4 rounded-xl text-gray-900 border-l-4 border-yellow-500"
                    >
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Histórico NDVI */}
            {result.ndvi_trend && result.ndvi_trend.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-4 text-lg flex items-center">
                  <span className="text-2xl mr-2">📈</span> Histórico NDVI
                  (últimos registros)
                </h3>
                <div className="bg-gray-50 p-6 rounded-xl overflow-x-auto border-2 border-gray-200">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-2 border-gray-300">
                        <th className="text-left p-3 text-gray-900 font-bold">
                          Data
                        </th>
                        <th className="text-right p-3 text-gray-900 font-bold">
                          NDVI
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.ndvi_trend.slice(-10).map((point, idx) => (
                        <tr key={idx} className="border-b border-gray-200">
                          <td className="p-3 text-gray-900 font-medium">
                            {point.date}
                          </td>
                          <td className="text-right p-3 font-mono text-gray-900 font-semibold">
                            {point.ndvi.toFixed(6)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

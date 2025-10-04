/* eslint-disable @typescript-eslint/no-explicit-any */
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

  // Form state
  const [lat, setLat] = useState('36.7468')
  const [lon, setLon] = useState('-119.7726')
  const [cropType, setCropType] = useState('almond')
  const [farmName, setFarmName] = useState('Central Valley Farm')

  const handlePredict = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8000/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lat: parseFloat(lat),
          lon: parseFloat(lon),
          crop_type: cropType,
          farm_name: farmName,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erro ao buscar predição')
      }

      const data = await response.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickTest = async (crop: string) => {
    setLoading(true)
    setError(null)
    setResult(null)

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
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 text-gray-900">🌸 BloomWatch</h1>
        <p className="text-gray-800 mb-8 font-medium">
          Predição de Floração com Dados NASA + ML
        </p>

        {/* Formulário Simples */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold mb-4">Nova Predição</h2>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-semibold mb-1 text-gray-900">
                Latitude
              </label>
              <input
                type="number"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                className="w-full p-2 border rounded text-gray-900"
                step="0.0001"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold mb-1 text-gray-900">
                Longitude
              </label>
              <input
                type="number"
                value={lon}
                onChange={(e) => setLon(e.target.value)}
                className="w-full p-2 border rounded text-gray-900"
                step="0.0001"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-semibold mb-1 text-gray-900">
                Cultura
              </label>
              <select
                value={cropType}
                onChange={(e) => setCropType(e.target.value)}
                className="w-full p-2 border rounded text-gray-900"
              >
                <option value="almond">Almond (Amêndoa)</option>
                <option value="apple">Apple (Maçã)</option>
                <option value="cherry">Cherry (Cereja)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-1 text-gray-900">
                Nome da Fazenda
              </label>
              <input
                type="text"
                value={farmName}
                onChange={(e) => setFarmName(e.target.value)}
                className="w-full p-2 border rounded text-gray-900"
              />
            </div>
          </div>

          <button
            onClick={handlePredict}
            disabled={loading}
            className="w-full bg-blue-600 text-white p-3 rounded font-semibold hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Buscando...' : '🔮 Fazer Predição'}
          </button>
        </div>

        {/* Testes Rápidos */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold mb-4">Testes Rápidos</h2>
          <div className="flex gap-4">
            <button
              onClick={() => handleQuickTest('almond')}
              disabled={loading}
              className="flex-1 bg-green-600 text-white p-3 rounded font-semibold hover:bg-green-700 disabled:bg-gray-400"
            >
              🌰 Almond
            </button>
            <button
              onClick={() => handleQuickTest('apple')}
              disabled={loading}
              className="flex-1 bg-red-600 text-white p-3 rounded font-semibold hover:bg-red-700 disabled:bg-gray-400"
            >
              🍎 Apple
            </button>
            <button
              onClick={() => handleQuickTest('cherry')}
              disabled={loading}
              className="flex-1 bg-pink-600 text-white p-3 rounded font-semibold hover:bg-pink-700 disabled:bg-gray-400"
            >
              🍒 Cherry
            </button>
          </div>
        </div>

        {/* Erro */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 p-4 rounded mb-6">
            <strong>Erro:</strong> {error}
          </div>
        )}

        {/* Resultados */}
        {result && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-6 text-gray-900">
              📊 Resultado da Predição
            </h2>

            {/* Informações Básicas */}
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="bg-blue-50 p-4 rounded">
                <h3 className="font-semibold text-gray-900 mb-2">🏡 Fazenda</h3>
                <p className="text-2xl font-bold text-blue-600">
                  {result.farm_name}
                </p>
                <p className="text-sm text-gray-800 mt-1">
                  {result.crop_type.toUpperCase()} •{' '}
                  {result.location.lat.toFixed(4)},{' '}
                  {result.location.lon.toFixed(4)}
                </p>
              </div>

              <div className="bg-green-50 p-4 rounded">
                <h3 className="font-semibold text-gray-900 mb-2">
                  🌸 Data de Floração
                </h3>
                <p className="text-2xl font-bold text-green-600">
                  {result.predicted_bloom_date}
                </p>
                <p className="text-sm text-gray-800 mt-1">
                  em {result.days_until_bloom} dias
                </p>
              </div>
            </div>

            {/* Intervalo de Confiança */}
            <div className="bg-purple-50 p-4 rounded mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                📊 Intervalo de Confiança
              </h3>
              <p className="text-gray-900">
                <strong>Mínimo:</strong> {result.confidence_low} &nbsp;|&nbsp;
                <strong>Máximo:</strong> {result.confidence_high}
              </p>
              <p className="text-sm text-gray-800 mt-1">
                Concordância dos modelos:{' '}
                {(result.agreement_score * 100).toFixed(1)}%
              </p>
            </div>

            {/* Predições Individuais */}
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">
                🤖 Predições dos Modelos
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 p-3 rounded text-center">
                  <p className="text-sm text-gray-800 font-semibold">LSTM</p>
                  <p className="text-xl font-bold text-gray-900">
                    {result.individual_predictions.lstm.toFixed(1)} dias
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded text-center">
                  <p className="text-sm text-gray-800 font-semibold">
                    Random Forest
                  </p>
                  <p className="text-xl font-bold text-gray-900">
                    {result.individual_predictions.rf.toFixed(1)} dias
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded text-center">
                  <p className="text-sm text-gray-800 font-semibold">ANN</p>
                  <p className="text-xl font-bold text-gray-900">
                    {result.individual_predictions.ann.toFixed(1)} dias
                  </p>
                </div>
              </div>
            </div>

            {/* Recomendações */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-3">
                  💡 Recomendações
                </h3>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, idx) => (
                    <li
                      key={idx}
                      className="bg-yellow-50 p-3 rounded text-gray-900"
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
                <h3 className="font-semibold text-gray-900 mb-3">
                  📈 Histórico NDVI (últimos registros)
                </h3>
                <div className="bg-gray-50 p-4 rounded overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2 text-gray-900 font-semibold">
                          Data
                        </th>
                        <th className="text-right p-2 text-gray-900 font-semibold">
                          NDVI
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.ndvi_trend.slice(-10).map((point, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2 text-gray-900">{point.date}</td>
                          <td className="text-right p-2 font-mono text-gray-900">
                            {point.ndvi.toFixed(4)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* JSON Bruto (para debug) */}
            <details className="mt-6">
              <summary className="cursor-pointer font-semibold text-gray-900">
                🔍 Ver JSON Completo
              </summary>
              <pre className="mt-2 bg-gray-900 text-green-400 p-4 rounded overflow-x-auto text-xs">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  )
}

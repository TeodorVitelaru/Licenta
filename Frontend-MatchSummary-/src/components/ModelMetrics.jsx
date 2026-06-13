import React from 'react'
import './ModelMetrics.css'

/**
 * Componenta pentru afisarea metricilor modelului ML
 */
const ModelMetrics = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="model-metrics empty">
        <p>Metricile modelului nu sunt disponibile</p>
      </div>
    )
  }

  // Functie pentru a determina clasa de culoare bazata pe valoare
  const getRatingClass = (rating) => {
    if (rating === 'excellent') return 'rating-excellent'
    if (rating === 'good') return 'rating-good'
    return 'rating-acceptable'
  }

  const getRPSRating = (rps) => {
    if (rps < 0.15) return 'excellent'
    if (rps < 0.20) return 'good'
    return 'acceptable'
  }

  const getAccuracyRating = (accuracy) => {
    if (accuracy > 0.65) return 'excellent'
    if (accuracy > 0.55) return 'good'
    return 'acceptable'
  }

  const getCalibrationRating = (calibration) => {
    if (calibration < 0.05) return 'excellent'
    if (calibration < 0.10) return 'good'
    return 'acceptable'
  }

  return (
    <div className="model-metrics">
      <div className="metrics-header">
        <h3>
          <span className="metrics-icon"></span>
          Informatii Model ML
        </h3>
        <p className="metrics-subtitle">
          {metrics.model_info?.model_type || 'Gradient Boosting Classifier'}
        </p>
      </div>

      <div className="metrics-grid">
        {/* RPS Score */}
        <div className={`metric-card ${getRatingClass(getRPSRating(metrics.metrics?.rps?.mean))}`}>
          <div className="metric-label">RPS Score</div>
          <div className="metric-value">
            {metrics.metrics?.rps?.mean?.toFixed(4) || 'N/A'}
          </div>
          <div className="metric-description">
            {getRPSRating(metrics.metrics?.rps?.mean) === 'excellent' && 'Excellent - Predictii foarte precise'}
            {getRPSRating(metrics.metrics?.rps?.mean) === 'good' && 'Good - Predictii bune'}
            {getRPSRating(metrics.metrics?.rps?.mean) === 'acceptable' && 'Acceptable - Predictii acceptabile'}
          </div>
          <div className="metric-bar">
            <div
              className="metric-bar-fill"
              style={{ width: `${Math.max(0, 100 - (metrics.metrics?.rps?.mean * 500))}%` }}
            />
          </div>
        </div>

        {/* Accuracy */}
        <div className={`metric-card ${getRatingClass(getAccuracyRating(metrics.metrics?.accuracy))}`}>
          <div className="metric-label">Accuracy</div>
          <div className="metric-value">
            {metrics.metrics?.accuracy ? `${(metrics.metrics.accuracy * 100).toFixed(1)}%` : 'N/A'}
          </div>
          <div className="metric-description">
            {getAccuracyRating(metrics.metrics?.accuracy) === 'excellent' && 'Excellent - Performanta puternica'}
            {getAccuracyRating(metrics.metrics?.accuracy) === 'good' && 'Good - Performanta buna'}
            {getAccuracyRating(metrics.metrics?.accuracy) === 'acceptable' && 'Acceptable - Performanta acceptabila'}
          </div>
          <div className="metric-bar">
            <div
              className="metric-bar-fill"
              style={{ width: `${(metrics.metrics?.accuracy * 100) || 0}%` }}
            />
          </div>
        </div>

        {/* Calibration */}
        <div className={`metric-card ${getRatingClass(getCalibrationRating(metrics.metrics?.calibration_error?.mean))}`}>
          <div className="metric-label">Calibration</div>
          <div className="metric-value">
            {metrics.metrics?.calibration_error?.mean
              ? `${((1 - metrics.metrics.calibration_error.mean) * 100).toFixed(1)}%`
              : 'N/A'}
          </div>
          <div className="metric-description">
            {getCalibrationRating(metrics.metrics?.calibration_error?.mean) === 'excellent' && 'Excellent - Probabilitati de incredere'}
            {getCalibrationRating(metrics.metrics?.calibration_error?.mean) === 'good' && 'Good - Probabilitati fiabile'}
            {getCalibrationRating(metrics.metrics?.calibration_error?.mean) === 'acceptable' && 'Acceptable - Probabilitati acceptabile'}
          </div>
          <div className="metric-bar">
            <div
              className="metric-bar-fill"
              style={{ width: `${((1 - (metrics.metrics?.calibration_error?.mean || 0)) * 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Info suplimentare */}
      {metrics.model_info && (
        <div className="metrics-footer">
          <div className="footer-stat">
            <span className="footer-label">Features:</span>
            <span className="footer-value">{metrics.model_info.features_count || 24}</span>
          </div>
          <div className="footer-stat">
            <span className="footer-label">Test Matches:</span>
            <span className="footer-value">{metrics.model_info.test_matches || 'N/A'}</span>
          </div>
          <div className="footer-stat">
            <span className="footer-label">Test Samples:</span>
            <span className="footer-value">
              {metrics.model_info.test_samples
                ? metrics.model_info.test_samples.toLocaleString('ro-RO')
                : 'N/A'}
            </span>
          </div>
        </div>
      )}

      {/* Overall rating */}
      {metrics.summary?.rating && (
        <div className={`overall-rating ${getRatingClass(metrics.summary.rating)}`}>
          <span className="rating-icon">
            {metrics.summary.rating === 'excellent' && '⭐⭐⭐'}
            {metrics.summary.rating === 'good' && '⭐⭐'}
            {metrics.summary.rating === 'acceptable' && '⭐'}
          </span>
          <span className="rating-text">
            Model Rating: {metrics.summary.rating.toUpperCase()}
          </span>
        </div>
      )}
    </div>
  )
}

export default ModelMetrics

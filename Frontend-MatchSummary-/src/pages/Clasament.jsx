import React from 'react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import Loading from '../components/Loading'
import { useSuperligaStandings } from '../hooks'
import './Clasament.css'

const Clasament = () => {
  const { data, loading, error, refetch } = useSuperligaStandings()
  const clasamentData = Array.isArray(data) && data.length > 0 ? data : null
  
  const getPozitieClass = (pozitie) => {
    if (pozitie <= 3) return 'pozitie-top'
    if (pozitie <= 6) return 'pozitie-europa'
    if (pozitie >= 15) return 'pozitie-relegare'
    return ''
  }

  return (
    <div className="clasament-container">
      <Navbar />
      <div className="clasament-content">
        <div className="clasament-header">
          <div className="clasament-header-content">
            <span className="clasament-badge">Superliga Romaniei</span>
            <span className="clasament-subtitle">Clasament actual</span>
            {clasamentData && (
              <button 
                className="refresh-button" 
                onClick={refetch}
                title="Reimprospateaza datele"
              >
                <i className="fas fa-sync-alt"></i>
              </button>
            )}
          </div>
        </div>

        {/* Mesaj de eroare */}
        {error && (
          <div className="error-message">
            <i className="fas fa-exclamation-triangle"></i>
            <span>{error}</span>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <Loading message="Se incarca clasamentul..." size="large" />
        )}

        {/* Tabel clasament */}
        {clasamentData && clasamentData.length > 0 && (
          <>
            <div className="clasament-table-wrapper">
              <table className="clasament-table">
                <thead>
                  <tr>
                    <th>Poz</th>
                    <th>Echipa</th>
                    <th>M</th>
                    <th>V</th>
                    <th>E</th>
                    <th>I</th>
                    <th>GM</th>
                    <th>GP</th>
                    <th>G</th>
                    <th>Pct</th>
                  </tr>
                </thead>
                <tbody>
                  {clasamentData.map((echipa) => (
                <tr key={echipa.pozitie} className={getPozitieClass(echipa.pozitie)}>
                  <td className="pozitie-cell">{echipa.pozitie}</td>
                  <td className="echipa-cell">
                    {echipa.logo && (
                      <img 
                        src={echipa.logo} 
                        alt={echipa.echipa}
                        className="team-logo"
                        onError={(e) => {
                          // Daca logo-ul nu se incarca, ascunde imaginea
                          e.target.style.display = 'none'
                        }}
                      />
                    )}
                    <span className="echipa-name-text">{echipa.echipa}</span>
                  </td>
                  <td>{echipa.meciuri}</td>
                  <td>{echipa.victorii}</td>
                  <td>{echipa.egaluri}</td>
                  <td>{echipa.infrangeri}</td>
                  <td>{echipa.goluriMarcate}</td>
                  <td>{echipa.goluriPrimite}</td>
                  <td className={echipa.golaveraj >= 0 ? 'golaveraj-pozitiv' : 'golaveraj-negativ'}>
                    {echipa.golaveraj > 0 ? '+' : ''}{echipa.golaveraj}
                  </td>
                  <td className="puncte-cell">{echipa.puncte}</td>
                  </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="clasament-legend">
          <div className="legend-item">
            <span className="legend-color pozitie-top"></span>
            <span>Calificare Champions League / Europa League</span>
          </div>
          <div className="legend-item">
            <span className="legend-color pozitie-europa"></span>
            <span>Calificare Conference League</span>
          </div>
          <div className="legend-item">
            <span className="legend-color pozitie-relegare"></span>
            <span>Zona de retrogradare</span>
          </div>
        </div>
        </>
        )}

        {/* Mesaj cand nu sunt date */}
        {!loading && !clasamentData && (
          <div className="no-data-message">
            <i className="fas fa-info-circle"></i>
            <p>Nu s-au putut incarca datele clasamentului.</p>
            <button onClick={refetch} className="retry-button">
              <i className="fas fa-redo"></i> Incearca din nou
            </button>
          </div>
        )}
      </div>
      <Footer />
    </div>
  )
}

export default Clasament



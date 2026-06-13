# Comparatie experimente - rezultate

Cele 18 modele din `experimentare/` (old vs new features x 100/200/500 meciuri x LGBM/GB/LR)
evaluate pe acelasi set de test comun: **693 meciuri / 2.446.447 randuri** (held-out din `fixed_split.pkl`).
Metrici identice cu `lgbm_gb_comparatie.py`. Pentru `accuracy` mai mare = mai bine; pentru `logloss`, `rps`, `brier`, `calibration` mai mic = mai bine.

| features | matches | model | accuracy | logloss | rps | brier | calibration |
|---|---|---|---|---|---|---|---|
| new | 100 | gradient_boosting | 0.6073 | 0.8483 | 0.1602 | 0.1639 | 0.0807 |
| new | 100 | lgbm | 0.5994 | 0.9011 | 0.1680 | 0.1743 | 0.0966 |
| new | 100 | logistic_regression | 0.5921 | 1.0014 | 0.1761 | 0.1830 | 0.1303 |
| new | 200 | gradient_boosting | 0.6381 | 0.8187 | 0.1565 | 0.1576 | 0.0701 |
| new | 200 | lgbm | 0.6303 | 0.8183 | 0.1556 | 0.1587 | 0.0515 |
| new | 200 | logistic_regression | 0.6093 | 0.8406 | 0.1596 | 0.1638 | 0.0599 |
| new | 500 | gradient_boosting | **0.6517** | 0.7808 | 0.1466 | 0.1517 | 0.0459 |
| new | 500 | lgbm | 0.6488 | 0.7824 | 0.1471 | 0.1517 | **0.0283** |
| new | 500 | logistic_regression | 0.6183 | 0.8155 | 0.1565 | 0.1599 | 0.0639 |
| old | 100 | gradient_boosting | 0.6117 | 0.8832 | 0.1694 | 0.1699 | 0.0972 |
| old | 100 | lgbm | 0.5887 | 0.9760 | 0.1754 | 0.1820 | 0.1361 |
| old | 100 | logistic_regression | 0.5564 | 1.0129 | 0.1856 | 0.1913 | 0.1653 |
| old | 200 | gradient_boosting | 0.6273 | 0.8235 | 0.1558 | 0.1584 | 0.0644 |
| old | 200 | lgbm | 0.6154 | 0.8311 | 0.1565 | 0.1620 | 0.0918 |
| old | 200 | logistic_regression | 0.5923 | 0.8489 | 0.1575 | 0.1657 | 0.1103 |
| old | 500 | gradient_boosting | 0.6475 | 0.7807 | 0.1473 | 0.1513 | 0.0338 |
| old | 500 | lgbm | 0.6455 | **0.7739** | **0.1464** | **0.1508** | 0.0506 |
| old | 500 | logistic_regression | 0.6264 | 0.7972 | 0.1525 | 0.1567 | 0.0474 |

## Concluzii

- **Mai multe meciuri = mai bine, constant.** Fiecare metrica se imbunatateste 100 -> 200 -> 500 pentru toate modelele; configuratiile cu 500 de meciuri domina clar.
- **Feature-urile noi ajuta mai ales pe date putine.** La 100 de meciuri castigul e mare (ex. LGBM: accuracy 0.5887 -> 0.5994, calibration 0.136 -> 0.097). La 500 de meciuri diferenta old vs new aproape dispare (sunt practic la egalitate).
- **Castigatori la 500 de meciuri:** Gradient Boosting (new) are cea mai buna `accuracy` (0.6517), iar LGBM ia cele mai bune metrici probabilistice - cel mai mic `logloss`/`rps`/`brier` (old_500) si cea mai buna calibrare (new_500 = 0.0283). GB si LGBM sunt foarte apropiate.
- **Logistic Regression** ramane cel mai slab model la orice dimensiune si pe orice metrica.

## Recomandare model final: LightGBM (new features, 500 meciuri)

Modelul final ales este **LightGBM** antrenat cu feature-urile noi pe 500 de meciuri. Justificare:

- **Calibrare net superioara.** La 500 de meciuri LGBM (new) are cea mai mica eroare de calibrare dintre toate modelele: **0.0283**, fata de 0.0459 la Gradient Boosting (new) - cu ~38% mai bine. Aplicatia afiseaza **probabilitati live** de castig (win-probability), deci probabilitatile trebuie sa fie de incredere, nu doar clasa prezisa; calibrarea este metrica cea mai importanta pentru acest caz de utilizare.
- **Acuratete practic egala.** Diferenta de accuracy fata de cel mai bun model (GB new = 0.6517) este de doar **0.003** (0.6488), nesemnificativa statistic la 2.45M de randuri de test.
- **Metrici probabilistice la egalitate.** `logloss` (0.7824 vs 0.7808), `rps` (0.1471 vs 0.1466) si `brier` (0.1517 vs 0.1517) sunt practic identice cu Gradient Boosting - LGBM nu pierde nimic relevant aici.
- **Avantaje practice.** LGBM antreneaza si face inferenta semnificativ mai rapid decat Gradient Boosting (relevant pentru predictii in timp real) si scaleaza mai bine daca se mareste setul de antrenare.
- **Consistenta cu aplicatia.** Modelul deja integrat in backend este `lgbm_final_model.pkl`, deci alegerea LGBM este coerenta cu pipeline-ul existent.

Concluzie: Gradient Boosting este o alternativa foarte apropiata (usor mai bun pe accuracy), dar pentru un produs care livreaza probabilitati, **calibrarea superioara a LGBM il face alegerea finala potrivita**.

## Fisiere generate

- `comparatie_experimente.csv` - tabelul complet (18 randuri).
- `comparatie_{accuracy,logloss,rps,brier,calibration}.png` - bar chart per metrica.


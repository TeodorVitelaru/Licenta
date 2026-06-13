# Win Probability - Predictia in-game a probabilitatii de victorie

Aplicatie web pentru analiza post-meci a meciurilor de fotbal din Superliga Romaniei. Sistemul reconstituie evolutia probabilitatilor de victorie (gazda / egal / oaspeti) folosind un model LightGBM antrenat pe evenimente StatsBomb.

## Structura proiectului

```
licenta_final/
├── backend/                  # API FastAPI (autentificare, predictii, Superliga)
├── Frontend-MatchSummary-/   # Interfata React (Vite)
├── model_3_clase/            # Antrenare, evaluare si artefacte model ML
├── documentatie_latex/       # Lucrarea de licenta (LaTeX)
└── diagrame_src/             # Diagrame arhitectura (PlantUML / Mermaid)
```

## Cerinte

| Componenta | Versiune recomandata |
|------------|----------------------|
| Python     | 3.10+ (testat si pe 3.13) |
| Node.js    | 18+ |
| npm        | 9+ |

Optional, pentru functionalitati Superliga live:
- Cheie **API-Football** ([api-sports.io](https://www.api-sports.io/))

---

## Rulare cu Docker

Metoda recomandata pentru **demo si prezentare**: o singura comanda porneste backend-ul, frontend-ul si modelul ML.

### Cerinte

| Componenta | Detalii |
|------------|---------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Windows / macOS (include Docker Compose) |
| Model ML | `{ROOT}/model_3_clase/experimentare/lgbm_final_model.pkl` |
| Configurare | `backend/.env` cu `SECRET_KEY` si `API_FOOTBALL_KEY` |

Verifica instalarea (PowerShell sau CMD):

```powershell
docker --version
docker compose version
```

**Important:** ruleaza comenzile din **PowerShell / CMD** (Windows) sau **Ubuntu WSL** (cu integrare Docker activata). **Nu** folosi shell-ul intern `docker-desktop`.

### Configurare (prima data)

1. Porneste **Docker Desktop** si asteapta statusul **Running**.

2. Copiaza sablonul de environment:

```powershell
cd E:\licenta_final
copy .env.docker.example backend\.env
```

3. Editeaza `backend\.env`:

```env
SECRET_KEY=o-cheie-lunga-si-unica
API_FOOTBALL_KEY=cheia_ta_de_la_api-sports.io
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
SUPERLIGA_LEAGUE_ID=283
SUPERLIGA_CACHE_SECONDS=600
LOG_LEVEL=INFO
```

4. Verifica ca modelul exista inainte de build:

```
model_3_clase/experimentare/lgbm_final_model.pkl
```

### Pornire

Din radacina proiectului:

```powershell
cd E:\licenta_final
docker compose up --build
```

Prima rulare (sau dupa modificari de cod) foloseste `--build`. Urmatoarele porniri pot folosi doar:

```powershell
docker compose up
```

Ruleaza in fundal (terminal liber):

```powershell
docker compose up -d --build
```

### Acces aplicatie

| Serviciu | URL |
|----------|-----|
| **Aplicatie web** | http://localhost:8080 |
| **API backend** | http://localhost:8000 |
| **Swagger (documentatie API)** | http://localhost:8000/docs |
| **Health check** | http://localhost:8000/health |

Flux utilizare:
1. Deschide http://localhost:8080
2. **Register** → creeaza cont
3. **Login** → autentificare
4. Navigheaza: **Clasament**, **Meciuri**, **Analiza Meci**

### Oprire si comenzi utile

```powershell
# Oprire containere
docker compose down

# Loguri (cand ruleaza cu -d)
docker compose logs -f

# Status containere
docker compose ps

# Rebuild dupa modificari cod
docker compose up --build

# Sterge volumul cu date utilizatori (conturi, predictii)
docker compose down -v
```

### Cum functioneaza

```
Browser (:8080)
    |
    v
[frontend]  nginx + React (build static)
    |  proxy: /auth, /api, /predict, /matches, /health
    v
[backend]   FastAPI + LightGBM (:8000)
    |
    +-- /app/model_3_clase/experimentare/lgbm_final_model.pkl
    +-- API-Football (cheie din backend/.env)
```

- **backend** — imagine Python cu FastAPI; incarca modelul din `model_3_clase/`
- **frontend** — build React servit de nginx; API-ul e apelat prin acelasi host (fara CORS intre porturi)
- **backend_user_data** — volum Docker pentru date utilizatori (persista intre restarturi)

### Fisiere Docker

```
docker-compose.yml                    # Orchestreaza serviciile
backend/Dockerfile                    # Imagine backend
Frontend-MatchSummary-/Dockerfile     # Build frontend + nginx
Frontend-MatchSummary-/nginx.conf     # Proxy API catre backend
.dockerignore                         # Exclude fisiere din build
.env.docker.example                   # Sablon pentru backend/.env
```

### Cand folosesti `--build`

| Situatie | Comanda |
|----------|---------|
| Prima pornire | `docker compose up --build` |
| Porniri ulterioare (fara schimbari) | `docker compose up` |
| Ai modificat cod backend/frontend | `docker compose up --build` |
| Ai schimbat doar `backend/.env` | `docker compose down` apoi `docker compose up` |

---

## Pornire rapida (fara Docker — development)

Aplicatia ruleaza in doua procese: backend (port 8000) si frontend (port 5173).

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

Copiaza fisierul de configurare si completeaza valorile:

```bash
copy .env.example .env        # Windows
cp .env.example .env          # Linux / macOS
```

Editeaza `backend/.env`:

```env
SECRET_KEY=schimba-cu-o-cheie-securizata
API_FOOTBALL_KEY=cheia_ta_api_football
```

Verifica ca modelul ML exista la calea folosita de backend:

```
model_3_clase/experimentare/lgbm_final_model.pkl
```

Daca fisierul lipseste, antreneaza modelul (vezi sectiunea [Model ML](#model-ml)).

Porneste serverul:

```bash
python main.py
```

Backend disponibil la:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 2. Frontend

Intr-un terminal separat:

```bash
cd Frontend-MatchSummary-
npm install
npm run dev
```

Aplicatia web: http://localhost:5173

Optional, creeaza `Frontend-MatchSummary-/.env` daca backend-ul nu ruleaza pe localhost:8000:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Utilizare

1. Deschide http://localhost:5173
2. Creeaza un cont sau autentifica-te
3. Navigheaza la **Clasament**, **Meciuri** sau **Analiza Meci**
4. Pentru predictii pe meciuri Superliga, backend-ul foloseste date API-Football (cheie necesara in `.env`)

## Model ML

Backend-ul incarca modelul final LightGBM:

```
model_3_clase/experimentare/lgbm_final_model.pkl
```

Pipeline antrenare (din folderul `model_3_clase`, cu mediul Python activ):

```bash
cd model_3_clase
pip install pandas numpy scikit-learn lightgbm joblib matplotlib tqdm

# Antrenare model multiclass (pasii principali)
python 2_train_model_multiclass.py
python 3_detect_decisive_multiclass.py

# Sau reantrenare model final cu 33 features
python experimentare/retrain_lgbm_33features.py
```

## Testare backend

Cu backend-ul pornit:

```bash
cd backend
pip install requests
python tests/test_api.py
```

## Build productie (frontend)

```bash
cd Frontend-MatchSummary-
npm run build
npm run preview
```

Fisierele generate apar in `Frontend-MatchSummary-/dist/`.

## Documentatie LaTeX

```bash
cd documentatie_latex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Endpoint-uri principale (backend)

| Metoda | Ruta | Descriere |
|--------|------|-----------|
| GET | `/health` | Status server si model |
| POST | `/auth/register` | Inregistrare utilizator |
| POST | `/auth/login` | Autentificare |
| GET | `/api/superliga/standings` | Clasament Superliga |
| GET | `/api/superliga/fixtures/{season}` | Lista meciuri sezon |
| POST | `/predict/by-fixture-id` | Predictie pe baza fixture API-Football |
| GET | `/matches` | Istoric predictii utilizator |
| GET | `/matches/{match_id}` | Detalii predictie |

## Depanare

### Docker

**`permission denied` / `docker.sock` (WSL)**
- Ruleaza din **PowerShell**, nu din shell-ul `docker-desktop`
- Docker Desktop → Settings → WSL Integration → activeaza Ubuntu

**`Cannot connect to the Docker daemon`**
- Porneste Docker Desktop si asteapta statusul Running

**Backend unhealthy / model error**
- Verifica `model_3_clase/experimentare/lgbm_final_model.pkl` exista inainte de `docker compose up --build`
- Consulta loguri: `docker compose logs backend`

**Clasament / meciuri goale**
- Adauga `API_FOOTBALL_KEY` valid in `backend/.env`
- Reporneste: `docker compose down` apoi `docker compose up`

**Port 8080 sau 8000 ocupat**
- Opreste alte procese pe aceste porturi sau modifica porturile in `docker-compose.yml`

**Modificari `.env` nu se aplica**
- `docker compose down` apoi `docker compose up` (rebuild nu e necesar pentru .env)

### Rulare locala (fara Docker)

**Modelul nu se incarca**
- Verifica existenta fisierului `model_3_clase/experimentare/lgbm_final_model.pkl`
- Consulta logurile la pornirea backend-ului (`python main.py`)

**Frontend nu primeste date**
- Confirma ca backend-ul ruleaza pe portul 8000
- Verifica `VITE_API_BASE_URL` in frontend (daca e setat)

**Clasament / meciuri goale**
- Adauga `API_FOOTBALL_KEY` valid in `backend/.env`
- Verifica `/health` si `/api/superliga/standings` in Swagger

**Eroare CORS**
- Backend-ul are CORS activ pentru development; frontend-ul trebuie sa apeleze acelasi host configurat in `VITE_API_BASE_URL`

## Licenta

Proiect de licenta - utilizare academica.

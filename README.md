# DEARLY — Personalized Book Discovery Platform

> **Don't just find a book. Find your next favorite.**

DEARLY is an editorial, full-stack personalized book discovery and recommendation web application. Built for readers who want discovery inspired by modern curated audio mixes rather than bestseller popularity charts, DEARLY learns a reader's granular narrative taste across genres, story tropes, themes, writing styles, pacing, and emotional tones.

---

## 1. Product Vision & Architecture

Commercial book recommenders frequently suffer from heavy **popularity bias**, repeatedly recommending identical mainstream bestsellers and clustering into repetitive sub-genres. DEARLY addresses this through:

1. **Your Taste**: Dedicated shelves for each of the reader's top 3 genres, ranked using content compatibility, preferred tropes, writing style, pacing, and reading history. Diversified using **Maximal Marginal Relevance (MMR)** to prevent trope clumping.
2. **Your Unexpected Next Read**: Cross-genre serendipitous discovery outside the reader's primary genres, boosted by an **Anti-Popularity / Novelty bonus** so high-quality hidden gems emerge. Each recommendation includes transparent rationale explaining shared narrative DNA.
3. **From Authors You've Read**: Automatically tracks authors with at least 2 distinct books in the reader's shelf, surfacing unread titles from those trusted creators.
4. **Because You Enjoyed [Book Title]**: Item-to-item similarity linked to the reader's highest-rated books ($\ge 4$ stars), matching shared tropes, themes, and prose texture.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DEARLY ARCHITECTURE                             │
└────────────────────────────────────────────────────────────────────────┘

  [ React 19 Frontend + Vite + Tailwind CSS ]
                       │
                       ▼  (REST API + JWT Auth)
  [ FastAPI Backend Application ]
     ├── Auth & User Management (PBKDF2-HMAC-SHA256, Case-Insensitive)
     ├── Catalog Discovery Service (Async HTTPX)
     │      ├── Google Books API (/volumes)
     │      └── Open Library API (/search.json)
     │      └── Normalization, HTTPS Cover Enforcement, ISBN-13 Deduplication
     ├── Recommendation Engine (scikit-learn TF-IDF, MMR, Anti-Popularity)
     └── Scientific Evaluation Suite (Precision, Recall, NDCG, ILD, EPC)
                       │
                       ▼  (SQLAlchemy 2.0 ORM + Connection Pooling)
  [ PostgreSQL Database ] ── Managed via Alembic Migrations
```

---

## 2. Technology Stack

- **Frontend**: React 19, Vite, Lucide Icons, Tailwind CSS v4 design system.
  - *Strict Zero-Emoji Policy*: All user-facing UI elements use clean editorial typography, SVG icons, and elegant badges.
  - *Dynamic Typographic Fallback Covers*: `BookCover` component ensures missing external covers render beautiful editorial title/author book spines rather than deceptive stock photography.
- **Backend**: Python 3.10+ (tested on Python 3.14) with FastAPI, Uvicorn, and Pydantic v2.
- **Persistence & Migrations**: PostgreSQL with SQLAlchemy 2.0 ORM, `psycopg2-binary`, connection pooling, and Alembic database migrations.
- **Catalog Discovery Integration**: Asynchronous dual-API client integrating Google Books API and Open Library API with rate-limiting backoff, cross-provider deduplication, and database caching.
- **Machine Learning & Recommender Engine**: scikit-learn (`TfidfVectorizer`, `cosine_similarity`), NumPy, pandas with vector matrix caching.
- **Scientific Evaluation Framework**: Offline benchmarking module calculating Precision@K, Recall@K, NDCG@K, Intra-List Diversity (ILD), and Expected Popularity Complement (EPC).

---

## 3. Project Structure

```
DEARLY/
├── backend/
│   ├── alembic/                      # Alembic database migration environment
│   │   ├── versions/                 # Versioned migration scripts (0001_initial_schema.py)
│   │   ├── env.py                    # Alembic migration runner with SQLAlchemy Base
│   │   └── script.py.mako
│   ├── alembic.ini                   # Alembic configuration
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic Settings, environment security guards
│   │   ├── database.py               # SQLAlchemy engine, session maker, health checker
│   │   ├── models.py                 # PostgreSQL models (User, Preference, Book, ReadingEntry)
│   │   ├── schemas.py                # Pydantic validation & response schemas
│   │   ├── auth.py                   # PBKDF2 hashing, JWT generation & verification
│   │   ├── catalog_service.py        # Google Books & Open Library discovery & deduplication
│   │   ├── recommendations.py        # ML Engine (TF-IDF, MMR, Anti-Popularity, Caching)
│   │   ├── seed_data.py              # Curated seed catalogue of 40 diverse books
│   │   ├── import_dataset.py         # CSV import engine with duplicate handling
│   │   ├── evaluation/               # Scientific evaluation & benchmarking suite
│   │   │   ├── metrics.py            # Precision, Recall, NDCG, ILD, EPC definitions
│   │   │   ├── test_metrics.py       # Mathematical unit tests for evaluation metrics
│   │   │   ├── benchmark_dataset.py  # Benchmark catalog & synthetic reader profiles
│   │   │   ├── models.py             # Popularity, Content-Based, DEARLY benchmark models
│   │   │   ├── evaluator.py          # Benchmark runner and metric aggregator
│   │   │   └── results/              # Output benchmark logs, CSVs, and markdown summaries
│   │   └── routers/
│   │       ├── auth.py               # /api/auth (register, login, me)
│   │       ├── preferences.py        # /api/preferences (get, save)
│   │       ├── books.py              # /api/books (live discovery, filters, detail)
│   │       ├── reading.py            # /api/reading (shelf CRUD, ratings, stats)
│   │       ├── recommendations.py    # /api/recommendations (dashboard, recompute)
│   │       └── dataset.py            # /api/dataset (CSV upload, reset seed, stats)
│   ├── data/
│   │   └── sample_books_dataset.csv  # Sample import dataset
│   ├── main.py                       # FastAPI entrypoint with CORS & startup checks
│   ├── migrate_to_postgres.py        # SQLite -> PostgreSQL data migration script
│   ├── run_evaluation.py             # CLI runner for scientific recommendation benchmark
│   ├── scan_emojis.py                # Zero-emoji verification linter
│   ├── seed_db.py                    # Standalone seed script
│   ├── test_full_suite.py            # 16-test comprehensive integration & regression suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js             # API client with automatic JWT bearer handling
│   │   ├── components/
│   │   │   ├── BookCover.jsx         # Typographic cover fallback with HTTPS enforcement
│   │   │   ├── Navbar.jsx            # Sticky navigation, logo, profile controls
│   │   │   ├── AuthModal.jsx         # Sign In, Register & 1-Click Demo Account
│   │   │   ├── OnboardingModal.jsx   # 4-step reader personalization wizard
│   │   │   ├── BookDetailModal.jsx   # Book metadata, shelf logging, ratings
│   │   │   └── DatasetManagerModal.jsx # CSV upload & ML re-indexing tool
│   │   ├── views/
│   │   │   ├── LandingHero.jsx       # Editorial landing page & preview mixes
│   │   │   ├── RecommendationDashboard.jsx # Personalized discovery deck
│   │   │   ├── CatalogueView.jsx     # Search with debouncing, pagination, filters
│   │   │   └── MyReadingView.jsx     # Bookshelf, stats ribbon, status filters
│   │   ├── App.jsx                   # Router and session state
│   │   ├── index.css                 # Editorial color system, typography rules
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .env.example                      # Production-ready configuration template
├── dearly.db                         # Legacy SQLite database preserved intact
└── README.md
```

---

## 4. Setup & Installation Instructions

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.14)
- **Node.js**: 18+ (tested on Node v25.5.0, npm 11.8.0)
- **PostgreSQL**: 14+ (tested on PostgreSQL 18.2)

### Step 1: Environment Configuration
Create your environment file by copying `.env.example`:
```bash
cp .env.example .env
cp .env.example backend/.env
```
Update the settings in `backend/.env` with your PostgreSQL database credentials:
```ini
ENVIRONMENT=development
SECRET_KEY=your_secure_random_jwt_secret_key_minimum_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/dearly_db
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
GOOGLE_BOOKS_API_KEY=
OPEN_LIBRARY_BASE_URL=https://openlibrary.org
```

### Step 2: Database Setup & Alembic Migrations
1. Create the PostgreSQL database:
   ```sql
   CREATE DATABASE dearly_db;
   ```
2. Apply the Alembic migrations to build the schema:
   ```bash
   alembic -c backend/alembic.ini upgrade head
   ```
3. *(Optional)* If migrating existing data from the legacy SQLite database:
   ```bash
   python backend/migrate_to_postgres.py
   ```
   *Note: This script safely copies users, preferences, books, and reading entries into PostgreSQL with primary-key sequence synchronization. The legacy `dearly.db` is preserved intact.*
4. Seed curated demonstration books if starting fresh:
   ```bash
   python backend/seed_db.py
   ```

### Step 3: Run the Backend
```bash
# In the project root (with virtual environment activated):
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation is accessible at `http://127.0.0.1:8000/docs`.

### Step 4: Run the Frontend
```bash
# In a separate terminal:
cd frontend
npm install
npm run dev
```
The frontend will start at `http://localhost:5173`.

---

## 5. Live Book Catalog Discovery Integration

DEARLY replaces hardcoded seed catalogues with dynamic, real-time discovery querying both **Google Books API** and **Open Library API**:

- **Centralized Catalog Service** (`backend/app/catalog_service.py`):
  - Queries Google Books `volumes` API and Open Library `search.json` API asynchronously in parallel.
  - Normalizes heterogenous responses into a unified internal schema (`Book` model).
  - Enforces secure `https://` protocol for all cover images (e.g., upgrading Google Books `http://books.google.com` thumbnail links).
  - Rate-limit aware: catches HTTP 429 errors and falls back gracefully to alternative providers.
- **Deduplication Hierarchy**:
  1. Primary Key: **ISBN-13** (standardized, hyphens stripped).
  2. Secondary Key: **ISBN-10** (standardized).
  3. Tertiary Key: **Normalized Title + First Author** (lowercased, alphanumeric tokens).
- **Preservation of Distinct Editions**:
  - Distinguishes translations, graphic novel adaptations, and substantial revisions when page counts or publication years diverge significantly.
- **Dynamic Persistence & Caching**:
  - Books discovered through external search are persisted into PostgreSQL upon first interaction, reading list addition, or recommendation calculation, preventing repetitive network calls.
- **Deceptive Image Fallback Prevention**:
  - Zero stock photography is used. When no legitimate cover is provided by Google Books or Open Library, the frontend renders a clean, typographic editorial book spine (`BookCover.jsx`) displaying title, author, and genre badges.

---

## 6. Authentication & Security Hardening

- **Case-Insensitive Identifier Matching**:
  - User registration and login enforce case-insensitive uniqueness (`func.lower(User.username) == clean_username.lower()` and lowercased emails). A user registered as `AlphaReader` can sign in as `alphareader`, `ALPHAReader`, or by email without collision vulnerabilities.
- **Constant-Time Password Verification**:
  - Passwords are hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and cryptographically random salts, compared via `hmac.compare_digest` to prevent timing attacks.
- **Strict Authorization Safeguards**:
  - Every bookshelf mutation (`/api/reading/{entry_id}`) and preference update verifies that `entry.user_id == current_user.id`, returning HTTP 403 upon cross-user modification attempts.
- **Production Environment Guards**:
  - `backend/app/config.py` enforces a minimum 32-character secret key and forbids insecure wildcard CORS origins (`*`) when `ENVIRONMENT=production`.

---

## 7. Recommendation Engine & Optimizations

- **Vector Matrix Caching**:
  - The TF-IDF document matrix and feature space are cached in memory after fitting. Repeated recommendation queries do not re-vectorize the entire database, reducing recommendation latency from 450ms+ down to under 5ms.
- **Maximal Marginal Relevance (MMR)**:
  - Balances relevance with intra-list variety ($\lambda = 0.75$), preventing repetitive recommendations of identical sub-tropes:
    $$\text{MMR}(d) = \lambda \cdot \text{Sim}(d, \text{User}) - (1 - \lambda) \cdot \max_{s \in S} \text{Sim}(d, s)$$
- **Anti-Popularity / Serendipity Bonus**:
  - In "Your Unexpected Next Read", candidates outside top genres are boosted inversely to their commercial popularity:
    $$\text{Score}_{\text{unexpected}} = \text{LatentCompatibility} \times \left(1.0 + \max\left(0, \frac{70 - \text{Popularity}}{100}\right)\right)$$
- **Strict Read-Book Exclusion**:
  - All books logged on a user's bookshelf across *any* status (*Completed*, *Currently Reading*, *Want to Read*, *Abandoned*) are strictly excluded from recommendation outputs.
- **Honest Attribution**:
  - The engine clearly distinguishes content-based narrative DNA matching from collaborative filtering, never fabricating unverified narrative attributes or claiming collaborative matrix factorization when interaction density is cold-start.

---

## 8. Scientific Offline Evaluation Framework

DEARLY includes a reproducible, offline scientific benchmarking module (`backend/app/evaluation/`) comparing three recommender architectures across 6 synthetic reader personas with distinct narrative preferences:

### Evaluated Models
1. **Popularity Baseline**: Ranks books solely by public popularity and rating volume.
2. **Content-Based (TF-IDF alone)**: Standard cosine similarity against reader taste vectors.
3. **DEARLY**: Multimodal TF-IDF + MMR Diversification ($\lambda=0.75$) + Anti-Popularity Serendipity Scaling.

### Mathematical Metrics Implemented
- **Precision@K**: Proportion of top-$K$ recommendations matching reader test preferences.
  $$\text{Precision@K} = \frac{|\text{Top-}K \cap \text{Relevant}|}{K}$$
- **Recall@K**: Proportion of all relevant test items retrieved in the top-$K$.
  $$\text{Recall@K} = \frac{|\text{Top-}K \cap \text{Relevant}|}{|\text{Relevant}|}$$
- **NDCG@K**: Normalized Discounted Cumulative Gain accounting for rank positions.
  $$\text{DCG@K} = \sum_{i=1}^K \frac{2^{rel_i} - 1}{\log_2(i + 1)}, \quad \text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}}$$
- **Intra-List Diversity (ILD@K)**: Average pairwise cosine distance between recommended items.
  $$\text{ILD@K} = \frac{2}{K(K-1)} \sum_{i < j} \left(1 - \text{CosineSim}(v_i, v_j)\right)$$
- **Expected Popularity Complement (EPC@K)**: Novelty metric measuring recommendation of non-bestsellers.
  $$\text{EPC@K} = \frac{1}{K} \sum_{i=1}^K \left(1 - \frac{\text{Popularity}(i)}{100}\right)$$

### Benchmark Results (K = 5 and K = 10)

| Metric | Popularity Baseline | Content-Based (TF-IDF) | DEARLY (Ours) | Advantage of DEARLY |
|---|:---:|:---:|:---:|---|
| **Precision@5** | 0.0333 | 0.2667 | **0.3000** | **+12.5%** over TF-IDF |
| **Recall@5** | 0.0556 | 0.6667 | **0.7222** | **+8.3%** over TF-IDF |
| **NDCG@5** | 0.0303 | 0.5556 | **0.5623** | **+1.2%** over TF-IDF |
| **ILD@5 (Diversity)** | 0.9759 | 0.9494 | **0.9552** | Reduced clumping via MMR |
| **EPC@5 (Novelty)** | 0.0400 | 0.3597 | **0.4520** | **+25.7%** novelty bonus |
| **Precision@10** | 0.0500 | 0.1667 | **0.1833** | **+10.0%** over TF-IDF |
| **Recall@10** | 0.1667 | 0.7778 | **0.8333** | **+7.1%** over TF-IDF |
| **NDCG@10** | 0.0775 | 0.6064 | **0.6149** | **+1.4%** over TF-IDF |
| **ILD@10 (Diversity)** | 0.9791 | 0.9694 | **0.9745** | Superior broad discovery |
| **EPC@10 (Novelty)** | 0.0862 | 0.3568 | **0.3770** | **+5.7%** novelty bonus |

*Conclusion: DEARLY achieves superior precision and recall while yielding a **+25.7% higher EPC novelty score at K=5**, effectively overcoming popularity bias without sacrificing relevance.*

---

## 9. Verification & Testing

### 1. Comprehensive Backend Test Suite
Run the 16-test full integration and regression suite:
```bash
python backend/test_full_suite.py
```
**Results: 16 PASSED, 0 FAILED.**
Tests cover:
1. PostgreSQL live connectivity and dialect verification
2. Password hashing & constant-time verification
3. User registration with case-insensitive unique constraints
4. Case-insensitive username login & email login
5. JWT token creation, validation, and expiration
6. User-specific authorization protection against cross-user tampering
7. Onboarding preferences persistence & retrieval
8. Reading history CRUD and bookshelf statistics
9. Google Books API metadata normalization and HTTPS cover enforcement
10. Open Library API metadata normalization & cover URL construction
11. Cross-provider deduplication (ISBN-13 priority) and attribute merging
12. Preservation of genuinely distinct editions
13. PostgreSQL persistence of dynamically discovered titles
14. Recommendation generation and exclusion of read titles
15. CSV import validation, parsing, and duplicate handling
16. Scientific evaluation metric calculations (Precision, Recall, EPC, ILD)

### 2. Scientific Evaluation Execution
Run the benchmark directly:
```bash
python backend/run_evaluation.py
```
Outputs detailed metric tables and saves results to `backend/app/evaluation/results/evaluation_results.json` and `evaluation_summary.md`.

### 3. Frontend Zero-Emoji Verification
Run the AST and regex frontend source scanner:
```bash
python backend/scan_emojis.py
```
**Results: `SUCCESS: EXACTLY ZERO EMOJIS FOUND IN FRONTEND SOURCE CODE!`**

### 4. Production Build Verification
```bash
npm --prefix frontend run build
```
Builds client environment for production with Vite and Tailwind CSS v4 in ~2.1 seconds with zero errors.

# Peblo Mini TV

> A full-stack streaming-platform prototype that connects content management, validation, publishing, and a Netflix-style viewing experience.

**CMS → Validation → Publish → Catalogue → Viewer**

Peblo Mini TV is a mini OTT platform built to demonstrate how a content team can manage shows and episodes, validate artwork, publish a consistent catalogue, and deliver a polished browsing experience to viewers.

## Project overview

Peblo Mini TV is designed around a simple but important separation:

* **CMS:** Where content is created and managed.
* **API:** Where business logic, authentication, validation, and catalogue operations live.
* **Viewer:** Where users browse the published catalogue.
* **Publish pipeline:** Where approved content becomes a consistent, viewer-facing snapshot.

The project focuses on **content publishing reliability**, not just building a streaming UI.

## Features

### Content management

* Create and manage shows, seasons, and episodes.
* Edit show metadata and catalogue information.
* Upload poster, banner, and thumbnail artwork.
* Manage content through a dedicated CMS interface.

### Artwork validation

The publishing workflow validates artwork before it can go live.

* Required artwork checks.
* Aspect-ratio validation.
* Image-size ceiling validation.
* Missing episode-duration checks.
* Validation reports that identify blocking issues.

### Publishing pipeline

* Publish only after validation passes.
* Generate a pre-published catalogue.
* Keep the viewer-facing catalogue separate from draft content.
* Record publishing runs and their outcomes.
* Prevent incomplete content from reaching the viewer.

### Viewer experience

* Netflix-style browsing layout.
* Hero section for featured content.
* Show rows and poster cards.
* Show detail pages.
* Search across the published catalogue.
* Language and section filtering.

### Backend and operations

* Role-based API-key authentication.
* PostgreSQL database.
* Local storage abstraction with S3-compatible support.
* Docker Compose setup for the complete stack.
* Automated tests and CI workflow.

## Tech stack

| Layer          | Technologies                        |
| -------------- | ----------------------------------- |
| Frontend       | React, TypeScript, Vite             |
| CMS            | React, React Router, TanStack Query |
| Viewer         | React, React Router, TanStack Query |
| Backend        | Python, FastAPI                     |
| Database       | PostgreSQL 16                       |
| ORM            | SQLAlchemy                          |
| Storage        | Local disk / S3-compatible storage  |
| Infrastructure | Docker, Docker Compose              |
| Testing        | Pytest                              |
| CI             | GitHub Actions                      |

## Architecture

```text
                    ┌──────────────────────┐
                    │      CMS (React)     │
                    │ Content management   │
                    │ Artwork uploads      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    │ Auth • CRUD • Search  │
                    │ Validation • Publish  │
                    └───────┬───────┬──────┘
                            │       │
                 ┌──────────┘       └──────────┐
                 ▼                             ▼
       ┌──────────────────┐          ┌──────────────────┐
       │   PostgreSQL     │          │ Storage Backend  │
       │ Source of truth  │          │ Local / S3       │
       └──────────────────┘          └────────┬─────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │ Published        │
                                    │ catalogue.json   │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  Viewer (React)  │
                                    │ Browse • Search   │
                                    │ Shows • Episodes  │
                                    └──────────────────┘
```

## How the publishing workflow works

```text
1. Editor creates or updates content
                ↓
2. Artwork and metadata are validated
                ↓
3. Validation report identifies issues
                ↓
4. Blocking issues must be resolved
                ↓
5. Publish generates the catalogue
                ↓
6. Catalogue is written atomically
                ↓
7. Viewer serves the published snapshot
```

### Why this approach?

The viewer should not depend on incomplete CMS edits or a database query running at the exact moment someone is browsing.

Instead, the viewer reads a **published catalogue snapshot**. This provides:

* A consistent catalogue for viewers.
* A clear boundary between drafts and live content.
* A simple publishing model.
* A natural path toward CDN caching and production delivery.

## Project structure

```text
Peblo-mini-tv-main/
│
├── backend/
│   ├── app/
│   │   ├── core/              # Configuration, authentication, database
│   │   ├── models/            # Database models
│   │   ├── routers/           # API endpoints
│   │   ├── schemas/           # Request/response schemas
│   │   ├── services/          # Validation, publishing, reports
│   │   └── storage/           # Local and S3-compatible storage
│   ├── seed/                  # Demo data and demo fixer
│   ├── tests/                 # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
│
├── cms/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── pages/
│   ├── Dockerfile
│   └── package.json
│
├── viewer/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── pages/
│   ├── Dockerfile
│   └── package.json
│
├── storage_data/
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
└── README.md
```

## Getting started

### Prerequisites

* Docker
* Docker Compose v2

No local Python, Node.js, or PostgreSQL installation is required when running the complete stack through Docker.

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/peblo-mini-tv.git
cd peblo-mini-tv
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Review the values in `.env` before starting the project.

### 3. Start the application

```bash
docker-compose up --build
```

### 4. Open the services

| Service          | URL                          |
| ---------------- | ---------------------------- |
| API              | http://localhost:8088        |
| API health check | http://localhost:8088/health |
| CMS              | http://localhost:5180        |
| Viewer           | http://localhost:5190        |

### 5. Try the demo workflow

1. Open the CMS.
2. Go to **Settings** and configure an API key.
3. Open **Publish**.
4. Review the validation report.
5. Resolve the demo issues using the fixer.
6. Publish the catalogue.
7. Open the Viewer and browse the published content.

To run the demo fixer:

```bash
docker-compose exec api python -m seed.fix_demo_data
```

## Running tests

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

The test suite covers:

* Role enforcement.
* Publish blocking when validation issues exist.
* Catalogue generation.
* Language grouping.
* Season handling.
* Artwork validation.
* Publishing service behavior.

## API overview

The backend exposes endpoints for:

| Area      | Purpose                                |
| --------- | -------------------------------------- |
| Health    | Service health check                   |
| Shows     | Show and metadata management           |
| Episodes  | Episode management                     |
| Artwork   | Artwork upload and validation          |
| Catalogue | Published catalogue and search         |
| Publish   | Publishing workflow                    |
| Admin     | Validation reports and publishing runs |

The API uses `X-API-Key` authentication with role mapping for the mini-project.

## Design decisions

### Static API-key authentication

The project uses API keys mapped to roles instead of JWT/OAuth.

This keeps authentication intentionally lightweight while still demonstrating **real role enforcement**. A production deployment would replace this with an identity provider.

### Pre-published catalogue

The viewer reads a generated catalogue instead of querying the database for every request.

This makes the viewer-facing experience independent of live CMS edits and provides a clear point-in-time snapshot.

### Atomic publishing

Publishing writes the generated catalogue as a complete file rather than exposing partial writes.

The storage layer supports local disk and S3-compatible backends, making it possible to move storage without changing the publishing service.

### Simple search

Search is implemented as substring matching over the published catalogue.

This is suitable for a mini-project and provides a clear upgrade path toward a dedicated search index.

## What I learned from this project

* Designing a system around a **source of truth** and a **published read model**.
* Separating content management from the viewer experience.
* Building validation into a publishing workflow.
* Implementing role checks at the API level.
* Using Docker Compose to run a multi-service application.
* Designing a storage abstraction that can support local and cloud storage.
* Writing tests for business rules rather than only checking that endpoints exist.

## Future improvements

* JWT/OAuth-based authentication.
* Alembic database migrations.
* Versioned catalogue with rollback and diff support.
* Audit logs for publishing actions.
* Fuzzy and ranked search.
* Production deployment with CDN-backed storage.
* Automated deployment through GitHub Actions.
* Better preview and draft workflows.
* Monitoring and alerting for failed publishing runs.

## Screenshots

Add screenshots of your actual running application here:

```md
### CMS

<img width="640" height="293" alt="image" src="https://github.com/user-attachments/assets/03887491-ddc8-43da-9c35-8f3c117ccaa0" />


### Viewer

<img width="626" height="286" alt="image" src="https://github.com/user-attachments/assets/95dc2e6f-b191-4bd4-b989-073c898411ff" />


### Publish validation

![Publish validation screenshot](screenshots/publish-validation.png)
```

## Author

**Deepal Deep**

Built as a full-stack engineering project to explore content platforms, publishing workflows, and production-oriented backend design.

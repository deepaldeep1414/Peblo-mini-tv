# Peblo TV Mini

A small streaming catalogue platform with a CMS for managing shows, a publishing pipeline for validating and releasing content, and a Netflix-style viewer for browsing the published catalogue.

## Live Demo

> **Live demo:** https://peblo-viewer-e6zc.onrender.com
>
> **CMS:** https://peblo-cms-2uzk.onrender.com

The viewer is public. The CMS requires an API key.

### CMS

<img width="638" height="295" alt="image" src="https://github.com/user-attachments/assets/e745cf2a-269d-4209-bc5b-bb42168813ac" />



### Viewer
<img width="624" height="286" alt="image" src="https://github.com/user-attachments/assets/f30bd70a-fe85-4930-80a9-2834a4c02376" />


<img width="631" height="295" alt="image" src="https://github.com/user-attachments/assets/22adc82e-49e7-41eb-b915-b67debb451a1" />




### Publish validation
<img width="638" height="295" alt="image" src="https://github.com/user-attachments/assets/898c6fd2-4f21-4fe6-99f0-4436d9801c85" />


## What it does

Peblo TV Mini separates content management from the published viewing experience.

* **CMS:** Create and manage shows, seasons, episodes, and artwork.
* **Publishing:** Validate catalogue data and block publishing when required content is missing or invalid.
* **Viewer:** Browse published shows, open show details, and search the catalogue.
* **API:** Handles authentication, catalogue operations, artwork validation, and publishing.
* **Storage:** Supports local storage and an S3-compatible storage backend.

## How it works

```text
CMS
 │
 │ Manage shows, episodes & artwork
 ▼
FastAPI
 │
 │ Validate catalogue
 ▼
Publish pipeline
 │
 │ Build & atomically write catalogue
 ▼
Published catalogue
 │
 ▼
Viewer
```

The viewer reads from the published catalogue rather than directly from the CMS database. This keeps the viewing experience separate from the content management workflow.

## Tech stack

| Layer            | Technology                         |
| ---------------- | ---------------------------------- |
| Frontend         | React, TypeScript, Vite            |
| Backend          | Python, FastAPI                    |
| Database         | PostgreSQL                         |
| ORM              | SQLAlchemy                         |
| Storage          | Local disk / S3-compatible storage |
| Containerization | Docker, Docker Compose             |
| Testing          | Pytest                             |

## Project structure

```text
Peblo-mini-tv-main/
├── backend/       # FastAPI API, models, services, storage & tests
├── cms/           # Content management interface
├── viewer/        # Public streaming catalogue
├── storage_data/  # Local artwork storage
├── docker-compose.yml
└── .env.example
```

## Getting started

### Prerequisites

* Docker
* Docker Compose

No local Python, Node.js, or PostgreSQL installation is required when running the full stack.

### Run locally

```bash
cp .env.example .env
docker-compose up --build
```

Once the containers are running:

| Service          | URL                          |
| ---------------- | ---------------------------- |
| Viewer           | http://localhost:5190        |
| CMS              | http://localhost:5180        |
| API              | http://localhost:8088        |
| API health check | http://localhost:8088/health |

### First-time setup

1. Open the CMS.
2. Go to **Settings** and add the API key from your `.env` file.
3. Open **Publish** to review the catalogue validation report.
4. Fix any blocking issues.
5. Publish the catalogue.
6. Open the Viewer to browse the published shows.

The project includes seeded demo data, including a show with deliberate validation issues, so the publishing workflow can be tested locally.

## Running tests

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

The test suite covers role enforcement, publishing rules, catalogue grouping, season handling, and artwork validation.

## Key implementation decisions

### Separate CMS and Viewer

The CMS is responsible for managing content, while the Viewer consumes the published catalogue. This keeps the two experiences independent and makes the publishing boundary explicit.

### Validation before publishing

Publishing is blocked when required catalogue data is invalid. This prevents incomplete shows or episodes from reaching the public catalogue.

### Atomic catalogue publishing

The publishing service builds the catalogue and writes it as a complete file. Local storage uses an atomic file replacement, while the S3-compatible backend supports a staging-and-copy approach.

### Storage abstraction

Storage is isolated behind a common interface, allowing the project to use local disk during development and an S3-compatible backend such as Cloudflare R2 or MinIO.

### Simple API-key authentication

The project uses a lightweight API-key-to-role mapping instead of a full authentication system. This keeps the implementation focused on the CMS and publishing workflow.

## Future improvements

* Add a full user authentication system.
* Add database migrations with Alembic.
* Add background publishing jobs.
* Add a stuck-publish-run recovery mechanism.
* Move search to a database query or dedicated search index.
* Add automated deployment and production monitoring.

## License

This project is for learning and demonstration purposes.

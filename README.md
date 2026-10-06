# Medical AI Platform (Phase 1 MVP)

This is the backend implementation for Phase 1 of the Medical AI Platform.

## Architecture & Tech Stack

* **Language**: Python 3.11+
* **Framework**: FastAPI
* **Database**: PostgreSQL (Neon serverless) via SQLAlchemy 2.0 & Alembic
* **Authentication**: JWT, bcrypt
* **AI Integration**: OpenAI / Groq via abstraction layer
* **File Processing**: PyMuPDF for native PDF extraction, Tesseract for OCR of scanned pages and images.
* **Storage**: Local encrypted file system (Fernet symmetric encryption). Abstracted to be easily swapped with S3.
* **Background Tasks**: Database-backed worker queue (`app/workers/worker.py`) running in the FastAPI lifespan.

## Discrepancies and Design Decisions

As instructed, where the frontend contract conflicted with the spec, the frontend contract was preferred:

1. **API Prefix**: The backend serves API at `/api/v1/*` instead of `/api/*` to match the frontend `baseURL` setting in `axios.create`.
2. **UUIDs vs Integers**: The frontend models assumed integer IDs for `user.id`, `patient.id`, `case.id`, `document.id`, `team.id`, and `extracted_item.id`. Therefore, auto-incrementing integers were used for these entities. `organization_id` was kept as a UUID.
3. **Pydantic V2 & MongoDB**: Removed legacy MongoDB schema elements (`PyObjectId`, `ConfigDict.arbitrary_types_allowed`, etc.) and replaced them with robust SQL-backed schemas.
4. **Data Isolation**: All resources strictly require an `org_id` match. Cross-tenant leakage is prevented at the route handler level and verified in `tests/test_api.py`.
5. **AI Extraction**: Replaced raw prompt strings with structured JSON (`response_format={ "type": "json_object" }`) using Pydantic models for stable parsing.

## Running Locally

1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in credentials:
   ```bash
   cp .env.example .env
   ```

3. Generate a database migration and run it:
   ```bash
   alembic upgrade head
   ```

4. Seed the database with sample data:
   ```bash
   python seed.py
   ```

5. Start the server (worker will start automatically):
   ```bash
   uvicorn app.main:app --reload
   ```

## Running Tests

Run the test suite using pytest (uses an in-memory SQLite database):
```bash
pytest tests/test_api.py -v
```

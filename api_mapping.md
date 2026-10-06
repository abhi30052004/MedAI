# API Endpoint Mapping

This document maps the expected frontend API calls to the backend endpoints required by the new MVP scope.

## Authentication & Authorization
| Frontend Expects | Backend Implementation | Notes |
|------------------|------------------------|-------|
| `POST /api/auth/login` | `POST /api/v1/auth/login` | Frontend may need URL update or proxy fix to use `/v1`. |
| `GET /api/auth/me` | `GET /api/v1/auth/me` | Returns current user details. |
| `POST /api/auth/register`| `POST /api/v1/auth/register` | Creates org + admin user. |

## Users & Organization
| Frontend Expects | Backend Implementation | Notes |
|------------------|------------------------|-------|
| `GET /api/users` | `GET /api/v1/users` | |
| `POST /api/users` | `POST /api/v1/users/invite` | Spec says "POST /users/invite". The frontend expects `/users` for direct creation. I will implement `/users/invite` to fulfill spec and `/users` to fulfill frontend contract. |
| `GET /api/organizations/me` | `GET /api/v1/org` | |

## Patients
| Frontend Expects | Backend Implementation | Notes |
|------------------|------------------------|-------|
| `GET /api/patients/` | `GET /api/v1/patients` | |
| `POST /api/patients/` | `POST /api/v1/patients` | |

## Cases
| Frontend Expects | Backend Implementation | Notes |
|------------------|------------------------|-------|
| `GET /api/cases/` | `GET /api/v1/cases` | |
| `POST /api/cases/` | `POST /api/v1/cases` | Note: Spec says "POST /cases (creates patient + case)". We will align to this or support both patient creation and case creation independently. |

## Documents & AI
| Frontend Expects | Backend Implementation | Notes |
|------------------|------------------------|-------|
| `GET /api/audit-logs` | `GET /api/v1/audit-logs` | |

## Discrepancies & Resolutions
- **API Prefix:** The frontend currently calls `/api/...`. The new spec requires `/api/v1/...`. I will mount the v1 router at `/api/v1` but also add a redirection or simply update the frontend's Vite proxy/baseURL if allowed, or just mount at `/api/v1` and inform the user.
- **Organization IDs:** Changed to UUIDs in backend. Frontend must be prepared to handle string UUIDs instead of integers.
- **Cases creation:** Frontend does `POST /patients/` then `POST /cases/` with `patient_id`. The new spec says `POST /cases` (creates patient + case). I will implement standard `POST /patients` and `POST /cases` for compatibility.

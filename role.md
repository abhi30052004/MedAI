# MedAI – Complete RBAC, Organization, Patient/Case, Document & AI MVP Implementation

You are working on an existing **MedAI medical case management application**.

Your task is to **inspect the existing codebase first**, understand the current architecture and implementation, and then implement/update the system according to the requirements below.

Do NOT blindly rewrite the application.

Preserve existing working functionality wherever possible and make changes incrementally.

---

# 1. PRIMARY OBJECTIVE

Implement a production-ready MVP with:

1. User & Organization Management
2. Role-Based Access Control (RBAC)
3. Organization-level data isolation
4. Patient Management
5. Medical Case Management
6. Medical Document Upload & Management
7. OCR / Document Text Extraction
8. AI Medical Analysis
9. Structured AI Case Summary
10. Audit Logs
11. Secure API authorization
12. Proper frontend role-based UI visibility
13. Backend enforcement of every permission

The backend must always be the final authority for authorization.

Frontend restrictions alone are NOT sufficient.

---

# 2. EXISTING ROLES

The application has exactly four primary roles:

```text
admin
doctor
staff
insurance_reviewer
```

Do not create unnecessary additional roles unless the existing architecture absolutely requires them.

---

# 3. ORGANIZATION-LEVEL DATA ISOLATION

Every user belongs to an organization.

User model must contain:

```text
id
org_id
name
email
password_hash / authentication reference
role
is_active
created_at
updated_at
```

All organization-owned entities must contain:

```text
org_id
```

At minimum:

* users
* teams
* patients
* cases
* documents
* AI analyses
* audit logs

Every API request must ensure that the requested resource belongs to the authenticated user's `org_id`.

Example:

```text
User org_id = ORG_A

User requests:

GET /cases/123

If case 123 belongs to ORG_A:
    allow according to role

If case 123 belongs to ORG_B:
    return 404 or appropriate authorization error

Never expose ORG_B data.
```

Do not rely only on a frontend filter such as:

```text
WHERE org_id = current_org
```

Authorization must be enforced in backend service/repository/database queries.

---

# 4. RBAC PERMISSION MATRIX

Implement the following exact permissions.

| Feature               | Admin | Doctor | Staff | Insurance Reviewer   |
| --------------------- | ----- | ------ | ----- | -------------------- |
| View patients         | YES   | YES    | YES   | Based on case access |
| Create patients       | YES   | YES    | YES   | NO                   |
| Edit patients         | YES   | YES    | NO    | NO                   |
| View cases            | YES   | YES    | YES   | YES                  |
| Create cases          | YES   | YES    | YES   | NO                   |
| Edit case details     | YES   | YES    | NO    | NO                   |
| Change case status    | YES   | YES    | NO    | NO                   |
| Upload documents      | YES   | YES    | YES   | NO                   |
| View documents        | YES   | YES    | YES   | YES                  |
| Download documents    | YES   | YES    | YES   | YES                  |
| OCR processing        | YES   | YES    | YES   | NO                   |
| Trigger AI analysis   | YES   | YES    | NO    | NO                   |
| View AI analysis      | YES   | YES    | YES   | YES                  |
| User management       | YES   | NO     | NO    | NO                   |
| Team management       | YES   | NO     | NO    | NO                   |
| Organization settings | YES   | NO     | NO    | NO                   |
| Audit logs            | YES   | NO     | NO    | NO                   |

Important:

### Admin

Admin inherits the general operational permissions of Doctor and Staff.

Admin can:

* create/update users
* activate/deactivate users
* assign roles
* create/update teams
* view audit logs
* manage organization settings
* create/view/edit patients
* create/edit cases
* change case status
* upload documents
* trigger OCR
* trigger AI analysis
* view/download documents
* view AI analysis

### Doctor

Doctor can:

* create/view patients
* edit patient information
* create cases
* edit case details
* update case status
* upload documents
* process documents/OCR
* trigger AI analysis
* view AI analysis
* view/download documents
* view case history

Doctor CANNOT:

* manage users
* manage teams
* manage organization settings
* view organization-wide audit logs

### Staff

Staff can:

* create patients
* view patients
* create cases
* view cases
* upload documents
* process uploaded documents/OCR
* view documents
* download documents
* view AI analysis results

Staff CANNOT:

* trigger AI analysis
* edit medical case details
* change case status
* make clinical decisions
* manage users
* manage teams
* access organization settings
* access organization-wide audit logs

### Insurance Reviewer

Insurance Reviewer is strictly read-only.

Can:

* view permitted cases
* view patient/case information required for review
* view AI analysis
* view structured case summaries
* view documents
* download documents

Cannot:

* create patients
* edit patients
* create cases
* edit cases
* change case status
* upload documents
* trigger OCR
* trigger AI analysis
* modify AI analysis
* manage users
* manage teams
* access administrative functions

---

# 5. BACKEND RBAC IMPLEMENTATION

Inspect the existing:

```text
app/api/deps.py
```

and existing authentication implementation.

Maintain:

```python
get_current_user()
```

for authentication.

Improve or implement:

```python
require_roles(*roles)
```

Example:

```python
Depends(require_roles("admin", "doctor"))
```

should allow only:

```text
admin
doctor
```

Example:

```python
Depends(require_roles("admin"))
```

should allow only:

```text
admin
```

Do NOT implement authorization only in frontend code.

Every protected endpoint must have backend authorization.

---

# 6. RESOURCE-LEVEL AUTHORIZATION

Role checking alone is NOT sufficient.

Every resource request must also validate:

```text
authenticated user
+
active user
+
organization ownership
+
role permission
+
resource permission
```

Example:

```python
case = get_case(case_id)

if case.org_id != current_user.org_id:
    raise HTTPException(status_code=404)
```

Then check role.

Do not allow a Doctor from Organization A to access a Case from Organization B.

The same rule applies to:

* patients
* cases
* documents
* analyses
* users
* teams
* audit logs

---

# 7. USER MANAGEMENT

Implement/update:

```text
POST   /users
GET    /users
GET    /users/{id}
PUT    /users/{id}
PATCH  /users/{id}/status
DELETE /users/{id}   (only if existing architecture requires deletion)
```

Only Admin can manage users.

Admin should be able to:

* create users
* assign role
* assign team
* activate/deactivate users
* update user information
* view users belonging only to their organization

Prevent Admin from creating a user under another organization.

The `org_id` should preferably be derived from the authenticated Admin instead of trusting a client-provided `org_id`.

---

# 8. TEAM MANAGEMENT

Implement/update:

```text
POST /teams
GET /teams
GET /teams/{id}
PUT /teams/{id}
```

Only Admin can create/update teams.

Teams must belong to the authenticated Admin's organization.

Users can only be assigned to teams belonging to the same organization.

---

# 9. PATIENT MANAGEMENT

Implement/update:

```text
POST /patients
GET /patients
GET /patients/{id}
PUT /patients/{id}
```

Patient fields should support:

```text
id
org_id
patient_identifier
first_name
last_name
date_of_birth
gender
contact_information
medical_history
allergies
current_medications
created_by
created_at
updated_at
```

Avoid storing unnecessary sensitive information.

Permissions:

```text
Admin:
create/view/edit

Doctor:
create/view/edit

Staff:
create/view

Insurance Reviewer:
read-only where permitted
```

All patient queries must be organization-scoped.

---

# 10. CASE MANAGEMENT

Implement/update:

```text
POST /cases
GET /cases
GET /cases/{id}
PUT /cases/{id}
PUT /cases/{id}/status
```

Case should support:

```text
id
org_id
patient_id
case_number
title
description
symptoms
diagnoses
medical_history
previous_treatments
procedures
medications
status
created_by
assigned_doctor
created_at
updated_at
```

Suggested statuses:

```text
draft
open
under_review
ai_analyzed
completed
closed
```

Do not allow arbitrary status values.

Permissions:

```text
Admin:
full access

Doctor:
create/edit/status/update

Staff:
create/view only

Insurance Reviewer:
view only
```

Staff must NOT be able to:

```text
PUT /cases/{id}
PUT /cases/{id}/status
```

---

# 11. MEDICAL DOCUMENT MANAGEMENT

Implement/update:

```text
POST /cases/{id}/documents
GET /cases/{id}/documents
GET /documents/{id}
GET /documents/{id}/download
DELETE /documents/{id}
```

Allowed document types should include:

```text
PDF
PNG
JPG
JPEG
DOC/DOCX if supported
```

Document metadata:

```text
id
org_id
case_id
patient_id
filename
content_type
file_size
storage_path / storage_key
uploaded_by
uploaded_at
ocr_status
processing_status
```

Validate:

* file type
* file size
* file integrity
* case ownership
* organization ownership

Never trust a client-provided:

```text
org_id
patient_id
case ownership
```

Resolve ownership from the authenticated case/resource.

---

# 12. OCR / DOCUMENT EXTRACTION

After document upload, support:

```text
uploaded
processing
completed
failed
```

OCR should extract text from supported documents/images.

Create a processing flow:

```text
Upload Document
        ↓
Validate File
        ↓
Store File
        ↓
Create Document Record
        ↓
OCR / Text Extraction
        ↓
Extracted Text
        ↓
Store Processing Result
```

Do not block the entire API request for long-running processing if the current architecture supports background jobs.

If background processing already exists, reuse it.

---

# 13. AI MEDICAL ANALYSIS

Implement/update:

```text
POST /cases/{id}/analyze
GET  /cases/{id}/analysis
```

Only:

```text
admin
doctor
```

can trigger analysis.

These roles can view analysis:

```text
admin
doctor
staff
insurance_reviewer
```

The AI analysis should process:

* patient information
* case information
* extracted document text
* relevant medical documents

Extract structured information such as:

```json
{
  "diagnoses": [],
  "symptoms": [],
  "medications": [],
  "procedures": [],
  "conditions": [],
  "clinical_findings": [],
  "missing_information": [],
  "important_information": [],
  "case_summary": ""
}
```

Do not allow the AI output to directly modify the official patient medical record without human review.

AI output should be stored separately from the authoritative medical record.

---

# 14. AI SAFETY / HUMAN REVIEW

The system must clearly treat AI output as:

```text
AI-generated analysis
```

not as an automatic medical decision.

The Doctor should be able to review AI results.

If the existing architecture supports it, add:

```text
review_status
reviewed_by
reviewed_at
```

Possible values:

```text
pending_review
reviewed
```

Do not present AI output as a confirmed diagnosis.

---

# 15. STRUCTURED CASE SUMMARY

AI should generate a readable structured summary containing:

```text
Patient Overview

Presenting Symptoms

Medical History

Diagnoses / Suspected Conditions

Medications

Procedures / Treatments

Important Clinical Findings

Missing Information

Relevant Documents

AI Summary

Review Status
```

The summary must be based only on available patient/case/document information.

Avoid inventing information.

If information is unavailable, return:

```text
Not available
```

or add it to:

```text
missing_information
```

---

# 16. AUDIT LOGGING

Implement organization-level audit logs.

Audit log should capture:

```text
id
org_id
user_id
user_role
action
resource_type
resource_id
timestamp
ip_address (if available)
metadata
```

Examples:

```text
USER_CREATED
USER_UPDATED
USER_DEACTIVATED

PATIENT_CREATED
PATIENT_UPDATED

CASE_CREATED
CASE_UPDATED
CASE_STATUS_CHANGED

DOCUMENT_UPLOADED
DOCUMENT_DOWNLOADED
DOCUMENT_DELETED

OCR_STARTED
OCR_COMPLETED
OCR_FAILED

AI_ANALYSIS_STARTED
AI_ANALYSIS_COMPLETED
```

Only Admin can access:

```text
GET /audit-logs
```

Audit logs must be organization-scoped.

Important security-sensitive actions should always generate audit events.

---

# 17. API RESPONSE SECURITY

Never return:

```text
password_hash
authentication secrets
API keys
internal storage credentials
other organization data
```

Use response schemas/DTOs to control returned fields.

Do not expose internal database objects directly if the framework currently allows it.

---

# 18. FRONTEND RBAC

Frontend must dynamically display features based on:

```text
current_user.role
```

However, frontend RBAC is only for UX.

Backend authorization remains mandatory.

### Admin UI

Show:

```text
Dashboard
Patients
Cases
Documents
AI Analysis
Users
Teams
Audit Logs
Organization Settings
```

### Doctor UI

Show:

```text
Dashboard
Patients
Cases
Documents
AI Analysis
```

Hide:

```text
Users
Teams
Audit Logs
Organization Settings
```

### Staff UI

Show:

```text
Dashboard
Patients
Cases
Documents
```

Hide/disable:

```text
AI Analyze button
Edit Case
Change Case Status
Users
Teams
Audit Logs
Organization Settings
```

Staff can view existing AI analysis results.

### Insurance Reviewer UI

Show:

```text
Dashboard
Cases
Case Details
Documents
AI Analysis / Summary
```

Hide:

```text
Create Patient
Create Case
Upload Document
AI Analyze
Edit Case
Change Status
Users
Teams
Audit Logs
Organization Settings
```

---

# 19. ROUTE GUARDS

Implement frontend route guards if the frontend architecture supports them.

Examples:

```text
/admin/users
/admin/teams
/admin/audit-logs
```

must only be accessible by Admin.

Doctor should receive:

```text
403 / Unauthorized
```

or be redirected appropriately.

Likewise:

```text
/cases/:id/analyze
```

must only be accessible to Admin and Doctor.

---

# 20. UI BUTTON PERMISSIONS

Do not simply hide buttons without backend protection.

Button visibility should follow permissions.

Examples:

```text
Create Patient:
Admin / Doctor / Staff

Edit Patient:
Admin / Doctor

Create Case:
Admin / Doctor / Staff

Edit Case:
Admin / Doctor

Change Status:
Admin / Doctor

Upload Document:
Admin / Doctor / Staff

Run AI Analysis:
Admin / Doctor

View AI Analysis:
Admin / Doctor / Staff / Insurance Reviewer
```

---

# 21. ERROR HANDLING

Use consistent HTTP responses.

Suggested behavior:

```text
401 = unauthenticated

403 = authenticated but insufficient permissions

404 = resource does not exist or is intentionally hidden because it belongs to another organization

422 = validation error
```

Do not leak information about resources belonging to other organizations.

---

# 22. DATABASE RELATIONSHIPS

Ensure proper relationships:

```text
Organization
    |
    ├── Users
    ├── Teams
    ├── Patients
    │      |
    │      └── Cases
    │              |
    │              ├── Documents
    │              └── AI Analyses
    |
    └── Audit Logs
```

A case belongs to one patient.

A patient belongs to one organization.

A document belongs to one case.

An AI analysis belongs to one case.

Every entity must maintain organization ownership where appropriate.

---

# 23. DATABASE MIGRATIONS

Inspect the existing database and migration system.

Do NOT manually destroy existing production data.

If new fields/tables are required:

* create migrations
* preserve existing records
* provide safe defaults
* make migrations reversible where practical

If the project currently uses:

```text
Alembic
```

use Alembic migrations.

If it uses another migration system, follow the existing architecture.

---

# 24. EXISTING CODE COMPATIBILITY

Before changing anything:

1. Inspect backend structure.
2. Inspect frontend structure.
3. Inspect database models.
4. Inspect authentication.
5. Inspect `app/api/deps.py`.
6. Inspect current user model.
7. Inspect current organization model.
8. Inspect patient/case/document models.
9. Inspect API routes.
10. Inspect frontend routes and components.
11. Inspect environment configuration.
12. Inspect existing AI/OCR implementation.

Reuse existing code where possible.

Do not duplicate functionality.

Do not introduce a second authentication system.

Do not introduce a second database layer.

Do not replace working components without a reason.

---

# 25. API DOCUMENTATION

After implementation, ensure the API documentation clearly shows:

```text
Authentication
Users
Teams
Patients
Cases
Documents
OCR
AI Analysis
Audit Logs
```

For every endpoint document:

* HTTP method
* path
* authentication requirement
* allowed roles
* request body
* response
* possible errors

---

# 26. TESTING REQUIREMENTS

Create/update automated tests for RBAC.

At minimum test:

### Admin

```text
Can create user
Can update user
Can create team
Can view audit logs
Can create patient
Can create case
Can edit case
Can upload document
Can trigger AI
```

### Doctor

```text
Can create patient
Can create case
Can edit case
Can change status
Can upload document
Can trigger AI

Cannot manage users
Cannot manage teams
Cannot view admin audit logs
```

### Staff

```text
Can create patient
Can create case
Can upload document
Can view AI analysis

Cannot edit case
Cannot change status
Cannot trigger AI
Cannot manage users
Cannot manage teams
```

### Insurance Reviewer

```text
Can view cases
Can view documents
Can download documents
Can view AI analysis

Cannot create patient
Cannot create case
Cannot edit case
Cannot upload document
Cannot trigger AI
Cannot manage users
Cannot manage teams
```

---

# 27. CROSS-ORGANIZATION SECURITY TESTS

This is mandatory.

Create tests proving:

```text
User from ORG_A cannot access ORG_B patient.

User from ORG_A cannot access ORG_B case.

User from ORG_A cannot access ORG_B document.

User from ORG_A cannot access ORG_B AI analysis.

User from ORG_A cannot access ORG_B users.

Admin from ORG_A cannot manage ORG_B users.

Admin from ORG_A cannot view ORG_B audit logs.
```

These tests are critical.

---

# 28. SECURITY REQUIREMENTS

Implement appropriate protections for:

* authentication
* authorization
* password storage
* token validation
* file upload validation
* file size limits
* MIME type validation
* organization isolation
* SQL/NoSQL injection protection
* path traversal protection
* API input validation
* sensitive data exposure
* audit logging

Never hardcode:

```text
API keys
JWT secrets
database passwords
OpenAI keys
cloud storage credentials
```

Use environment variables/secrets.

---

# 29. ENVIRONMENT CONFIGURATION

Inspect the existing `.env` and environment configuration.

Use environment variables for:

```text
DATABASE_URL
JWT_SECRET
OPENAI_API_KEY
AI_MODEL
STORAGE_CONFIGURATION
OCR_CONFIGURATION
```

Do not commit secrets.

If `.env.example` exists, update it with required variables but use placeholder values.

---

# 30. API PERMISSION MAP

Create a centralized permission structure if it fits the existing architecture.

For example:

```python
ROLE_PERMISSIONS = {
    "admin": [...],
    "doctor": [...],
    "staff": [...],
    "insurance_reviewer": [...]
}
```

Avoid scattering hardcoded role checks everywhere when a centralized permission system can be safely introduced.

However, maintain clear endpoint-level authorization.

---

# 31. IMPORTANT BUSINESS RULE

The following distinction is critical:

### Staff can upload and process documents.

But:

### Staff cannot trigger AI analysis.

Therefore:

```text
Staff
   ↓
Upload Document
   ↓
OCR / Extraction
   ↓
Extracted Information Available
   ↓
Doctor/Admin
   ↓
Trigger AI Analysis
```

Insurance Reviewer:

```text
Case
 ↓
Documents
 ↓
OCR / Extracted Data
 ↓
AI Analysis
 ↓
Read-only Review
```

---

# 32. AI ANALYSIS FLOW

Recommended flow:

```text
Doctor/Admin selects Case
        ↓
POST /cases/{case_id}/analyze
        ↓
Verify authentication
        ↓
Verify role
        ↓
Verify organization
        ↓
Load patient
        ↓
Load case
        ↓
Load case documents
        ↓
Load OCR extracted text
        ↓
Build AI analysis input
        ↓
Send to configured AI model
        ↓
Validate structured response
        ↓
Store AI analysis
        ↓
Create audit log
        ↓
Return analysis
```

---

# 33. DOCUMENT FLOW

```text
User
 ↓
Select Case
 ↓
Upload Document
 ↓
Backend Authentication
 ↓
Role Check
 ↓
Organization Check
 ↓
Case Ownership Check
 ↓
File Validation
 ↓
Storage
 ↓
Document DB Record
 ↓
OCR
 ↓
Extracted Text
 ↓
Processing Complete
```

---

# 34. CASE REVIEW FLOW

```text
Staff
 ↓
Create Patient
 ↓
Create Case
 ↓
Upload Medical Documents
 ↓
OCR
 ↓
Doctor/Admin
 ↓
Review Case
 ↓
Trigger AI Analysis
 ↓
AI Generates Structured Summary
 ↓
Doctor Reviews AI Result
 ↓
Case Status Updated
 ↓
Insurance Reviewer
 ↓
Read-Only Case Review
```

---

# 35. FRONTEND DASHBOARD

Create role-specific dashboards.

### Admin Dashboard

Show:

```text
Total Users
Total Patients
Active Cases
Completed Cases
AI Analyses
Recent Activity
```

### Doctor Dashboard

Show:

```text
My/Available Cases
Pending Reviews
Recent Patients
AI Analyses
Documents
```

### Staff Dashboard

Show:

```text
Patients
Cases
Documents
Processing Status
```

### Insurance Reviewer Dashboard

Show:

```text
Assigned/Available Cases
Cases Under Review
Documents
AI Summaries
```

Do not show administrative actions to unauthorized roles.

---

# 36. AUDIT LOG UI

Admin should have:

```text
Audit Logs
```

with:

```text
Timestamp
User
Role
Action
Resource
Resource ID
Status
Details
```

Add filtering where practical:

```text
Date
User
Action
Resource Type
```

Only Admin can access this page/API.

---

# 37. FINAL VALIDATION

After implementation, run:

```text
Backend tests
Frontend tests
Lint
Type checking
Database migration validation
API startup
Frontend startup
```

Then manually verify every role.

Create test users:

```text
admin@test.com
doctor@test.com
staff@test.com
reviewer@test.com
```

Create at least two organizations:

```text
ORG_A
ORG_B
```

Test cross-organization access.

---

# 38. DO NOT BREAK EXISTING FEATURES

Before finishing, verify that existing:

* authentication
* login
* registration/user creation
* patient functionality
* case functionality
* document upload
* OCR
* AI functionality
* frontend navigation

continue to work.

If an existing implementation differs from this specification, adapt it rather than creating duplicate functionality.

---

# 39. REQUIRED FINAL OUTPUT

After completing the implementation, provide a concise implementation report containing:

## A. Files Changed

List every important file changed.

Example:

```text
backend/
  app/api/deps.py
  app/api/routes/users.py
  app/api/routes/cases.py
  app/models/...
  app/schemas/...
  app/services/...
  tests/...

frontend/
  src/routes/...
  src/components/...
  src/services/...
```

## B. Database Changes

List:

* new tables
* new columns
* relationships
* migrations

## C. API Changes

List all new/updated endpoints and their allowed roles.

## D. RBAC Matrix

Provide the final permission matrix.

## E. Security

Explain:

* organization isolation
* role enforcement
* resource-level authorization
* file security
* audit logging

## F. Testing

Report:

```text
Tests passed
Tests failed
Remaining issues
```

## G. Environment Variables

List newly required environment variables.

## H. Manual Test Credentials

If test users are created, provide their roles and safe test credentials only.

Never expose real credentials or secrets.

---

# 40. MOST IMPORTANT IMPLEMENTATION RULES

Follow these rules throughout the implementation:

1. Backend authorization is mandatory.
2. Frontend authorization is only for UI/UX.
3. Every organization-owned resource must be organization-scoped.
4. Never trust client-provided `org_id`.
5. Never allow cross-organization resource access.
6. Insurance Reviewer is strictly read-only.
7. Staff cannot trigger AI analysis.
8. Staff cannot edit cases or change case status.
9. Only Admin can manage users and teams.
10. Only Admin can access organization-wide audit logs.
11. Only Admin and Doctor can trigger AI analysis.
12. AI output must not automatically become an official medical diagnosis.
13. Keep AI analysis separate from authoritative medical records.
14. Validate all uploaded files.
15. Never expose secrets.
16. Preserve existing functionality.
17. Use existing project architecture wherever possible.
18. Add tests for every role.
19. Add cross-organization security tests.
20. Do not finish until the complete MVP flow works end-to-end.

---

# START NOW

First inspect the complete existing codebase and identify:

1. Backend framework
2. Frontend framework
3. Database
4. Authentication mechanism
5. Existing RBAC implementation
6. Existing organization implementation
7. Existing patient/case/document models
8. Existing OCR implementation
9. Existing AI implementation
10. Existing API routes
11. Existing frontend routes/components
12. Existing tests

Then create an implementation plan based on the existing architecture.

After that, implement the changes required by this specification.

Do not ask me to manually implement individual pieces unless there is a genuine blocker.

Make the application work as a complete MVP from:

**Login → Organization → Patient → Case → Document Upload → OCR → AI Analysis → Doctor Review → Insurance Review → Audit Trail.**

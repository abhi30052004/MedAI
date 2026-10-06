# MedAI — Fix and Implement New Case Creation End-to-End

## Objective

The current **New Case / Create Case** option is not working correctly.

Inspect the existing frontend and backend first, identify why the New Case action/form/API is failing, and then implement a complete working case-creation workflow.

Do not create a duplicate case system.

Reuse the existing:

* React/Vite frontend
* FastAPI backend
* SQLAlchemy models
* PostgreSQL/Neon database
* Authentication
* RBAC
* Patient model
* Case model
* Document system
* AI analysis system
* Existing UI design system

The final workflow must work from the UI all the way to PostgreSQL.

---

# 1. IMPORTANT PRODUCT DECISION

The New Case form should be simple.

Do NOT ask staff to manually enter a complete medical history before uploading documents.

The initial case form should capture:

### Patient information

* First Name
* Last Name
* Date of Birth
* Gender
* Contact Number
* Patient Identifier / MRN if available

### Insurance

* Is insurance available?

  * Yes
  * No

If Yes:

* Insurance Provider
* Insurance Number / Policy Number

If No:

* Hide insurance provider
* Hide insurance number

### Case information

* Case Title
* Primary Disease / Condition
* Symptoms / Reason for Visit
* Previous Treatment / Medical History
* Additional Notes

### Assignment

* Doctor / Practitioner
* Insurance Reviewer, if insurance is available

Then:

```text
Create Case
```

The case is created first.

Documents are uploaded **after case creation**.

AI analysis happens after documents are processed.

---

# 2. IMPORTANT: PATIENT IS NOT A USER

Do not create a login for the patient.

The patient is a database record.

The user creating the case is:

```text
Staff
Doctor
or Admin
```

depending on RBAC.

---

# 3. CORRECT NEW CASE WORKFLOW

Implement this:

```text
Staff Login
      ↓
Cases
      ↓
+ New Case
      ↓
Patient Information
      ↓
Insurance Information
      ↓
Case Information
      ↓
Assignment
      ↓
Create Case
      ↓
Case Created
      ↓
Upload Medical Documents
      ↓
Document Processing
      ↓
OCR / Text Extraction
      ↓
Medical Information Extraction
      ↓
AI Analysis
      ↓
AI Summary
      ↓
Doctor / Insurance Reviewer Review
```

Do not try to run AI analysis before the case exists.

---

# 4. NEW CASE UI

Create a proper multi-section form.

Recommended UI:

```text
----------------------------------------------------
NEW CASE
Create a new patient case
----------------------------------------------------

PATIENT INFORMATION

First Name *
[________________]

Last Name *
[________________]

Date of Birth *
[________________]

Gender
[ Select Gender ▼ ]

Contact Number
[________________]

Patient ID / MRN
[________________]


----------------------------------------------------

INSURANCE INFORMATION

Is insurance available?

( ) Yes
( ) No

If Yes:

Insurance Provider *
[ Select Insurance Provider ▼ ]

Insurance Number / Policy Number *
[________________]


----------------------------------------------------

CASE INFORMATION

Case Title *
[________________]

Primary Disease / Condition
[________________]

Symptoms / Reason for Visit
[____________________________]
[____________________________]

Previous Treatment / Medical History
[____________________________]
[____________________________]

Additional Notes
[____________________________]


----------------------------------------------------

ASSIGNMENT

Doctor / Practitioner
[ Select Doctor ▼ ]

Insurance Reviewer
[ Select Reviewer ▼ ]

----------------------------------------------------

                    [Cancel] [Create Case]
----------------------------------------------------
```

Do not show Insurance Reviewer as required when:

```text
Insurance Available = No
```

If insurance is available, make Insurance Reviewer selection configurable according to the current assignment rules.

---

# 5. FIELD VALIDATION

Required fields:

```text
First Name
Last Name
Date of Birth
Case Title
```

If insurance is:

```text
Yes
```

then:

```text
Insurance Provider
Insurance Number
```

should be required.

If insurance is:

```text
No
```

then insurance fields must be:

```text
hidden
```

and should not be submitted.

---

# 6. DISEASE / CONDITION FIELD

Do not create an unnecessarily complicated disease database for the MVP.

Use:

```text
Primary Disease / Condition
```

as a searchable/selectable field if the existing backend supports it.

Otherwise use a text input.

Example:

```text
Diabetes
Hypertension
Cardiac condition
Fracture
Cancer
Respiratory condition
Infection
Other
```

If:

```text
Other
```

is selected, show:

```text
Specify condition
[________________]
```

The user should not be forced to select a diagnosis if it has not yet been clinically established.

Use wording:

```text
Primary Disease / Condition
```

rather than:

```text
Final Diagnosis
```

because the AI and clinical review may identify or change the diagnosis later.

---

# 7. SYMPTOMS / REASON FOR VISIT

Use a multiline field:

```text
Symptoms / Reason for Visit
```

Example:

```text
Patient reports persistent cough and shortness of breath for approximately two weeks.
```

This information can later be included in AI analysis.

Do not automatically convert this into a confirmed diagnosis.

---

# 8. PREVIOUS TREATMENT / MEDICAL HISTORY

Use:

```text
Previous Treatment / Medical History
```

as optional multiline text.

Example:

```text
Previously treated for hypertension.
Currently taking medication as reported by patient.
```

Do not label manually entered information as AI-generated.

---

# 9. ADDITIONAL NOTES

Allow Staff to add operational/context notes.

Example:

```text
Patient referred for further evaluation.
```

These are human-created notes.

Store the author.

---

# 10. INSURANCE UI BEHAVIOR

Use a proper conditional UI.

Initial:

```text
Insurance Available?

Yes     No
```

If:

```text
No
```

show:

```text
No insurance information required.
```

Hide:

```text
Insurance Provider
Insurance Number
Insurance Reviewer
```

If:

```text
Yes
```

show:

```text
Insurance Provider
Insurance Number
Insurance Reviewer
```

Do not send empty insurance fields unnecessarily.

---

# 11. INSURANCE PROVIDER

Do not hard-code a large list directly inside the React component.

Create a reusable configuration/constants source.

For example:

```text
Insurance Provider
    ↓
Select
```

Possible initial demo providers:

```text
Aetna
Blue Cross Blue Shield
Cigna
UnitedHealthcare
Humana
Kaiser Permanente
Other
```

But because this application may be used in India, inspect the existing product requirements before finalizing the provider list.

If the project is intended for Indian medical organizations, use an appropriate configurable provider list instead of assuming US insurers.

The database should ultimately allow the provider to be extended without rewriting the form.

---

# 12. DOCTOR DROPDOWN

The Doctor dropdown must come from the backend.

Do not hard-code doctors.

Call something equivalent to:

```http
GET /api/v1/users?role=doctor&is_active=true
```

or use the existing user endpoint with role filtering.

Display:

```text
Dr. Name
```

but submit:

```text
doctor/user UUID
```

Only users belonging to the current organization may appear.

---

# 13. INSURANCE REVIEWER DROPDOWN

If insurance is available, load:

```http
GET /api/v1/users?role=insurance_reviewer&is_active=true
```

Only organization users should appear.

Submit the reviewer ID.

Do not allow Staff to assign users outside the organization.

---

# 14. BACKEND CASE MODEL

Inspect the existing Case model.

Make sure it can store the required information.

The case should contain at minimum:

```text
id
organization_id
patient_id
title
status
symptoms
diagnoses
previous_treatments
assigned_to
created_by
archived
created_at
updated_at
```

Add missing fields only if the existing schema cannot represent the requirements.

For insurance, prefer structured fields where appropriate.

For example:

```text
insurance_available
insurance_provider
insurance_number
assigned_insurance_reviewer
```

If insurance information already belongs in a separate patient/insurance entity in the existing architecture, reuse that instead of duplicating it.

Do not create duplicate insurance tables unnecessarily.

---

# 15. PATIENT MODEL

Patient should contain:

```text
id
organization_id
first_name
last_name
dob
gender
contact
identifiers
medical_history
created_by
created_at
updated_at
```

The patient should remain reusable across cases.

Do not create a new patient record every time a case is created if the user selects an existing patient.

---

# 16. NEW CASE SHOULD SUPPORT TWO MODES

Implement:

### Mode A — Existing Patient

```text
Cases
 ↓
New Case
 ↓
Search Existing Patient
 ↓
Select Patient
 ↓
Case Information
 ↓
Create Case
```

### Mode B — New Patient

```text
Cases
 ↓
New Case
 ↓
Create New Patient
 ↓
Patient Information
 ↓
Case Information
 ↓
Create Case
```

Recommended UI:

```text
Patient

( ) Existing Patient
( ) New Patient
```

If Existing Patient:

```text
Search patient by:
Name / Patient ID / MRN
```

If New Patient:

show the patient fields.

This prevents duplicate patient records.

---

# 17. DUPLICATE PATIENT PROTECTION

Before creating a new patient, check for possible duplicates within the same organization using suitable fields such as:

```text
name
date_of_birth
patient identifier
```

Do not expose another organization's patient information.

If a possible duplicate exists:

```text
A similar patient already exists.
Would you like to use the existing patient?
```

Do not silently create duplicates.

---

# 18. CREATE CASE API

Use the existing API if it already satisfies this requirement.

Expected:

```http
POST /api/v1/cases
```

Request should contain appropriate structured data, for example:

```json
{
  "patient": {
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1985-04-12",
    "gender": "male",
    "contact": {
      "phone": "..."
    }
  },
  "title": "Hypertension Follow-up",
  "insurance_available": true,
  "insurance_provider": "Example Insurance",
  "insurance_number": "POL-12345",
  "symptoms": "Persistent headache",
  "previous_treatments": "Previously treated for hypertension.",
  "additional_notes": "Follow-up case.",
  "assigned_doctor_id": "UUID",
  "assigned_insurance_reviewer_id": "UUID"
}
```

Do not blindly copy this schema if the current backend uses separate patient and case endpoints. Adapt to the existing architecture.

---

# 19. TRANSACTIONAL CREATION

When creating a brand-new patient + case:

```text
BEGIN TRANSACTION
    ↓
Create Patient
    ↓
Create Case
    ↓
Create audit event
    ↓
COMMIT
```

If case creation fails:

```text
ROLLBACK
```

Do not leave orphan patient records.

If the existing architecture already has a service transaction, reuse it.

---

# 20. CASE STATUS

New case should start as:

```text
NEW
```

After document upload:

```text
DOCUMENTS_UPLOADED
```

During analysis:

```text
UNDER_ANALYSIS
```

After AI analysis:

```text
UNDER_REVIEW
```

After required human review:

```text
COMPLETED
```

Do not skip directly from:

```text
NEW
```

to:

```text
COMPLETED
```

---

# 21. AFTER CASE CREATION

Do NOT immediately force the user back to the case list.

Navigate to:

```text
/cases/{case_id}
```

Show:

```text
Case Created Successfully
```

Then display:

```text
PATIENT
John Doe
DOB
12 Apr 1985

CASE
Hypertension Follow-up

INSURANCE
Available
Example Insurance
Policy: ****2345

STATUS
NEW
```

Then:

```text
DOCUMENTS

[ + Upload Medical Documents ]
```

The next action should be obvious:

```text
Upload medical documents to start AI processing.
```

---

# 22. DOCUMENT UPLOAD AFTER CASE CREATION

Allow:

* PDF
* JPG
* PNG
* TIFF
* DOCX

Maximum:

```text
25 MB
```

per file by default.

After upload:

```text
UPLOADED
 ↓
PROCESSING
 ↓
READY
```

Show progress/status.

---

# 23. AI ANALYSIS TRIGGER

Do not run AI before documents are ready.

Once documents are ready:

```text
[ Analyze Case ]
```

or automatically analyze if:

```text
AUTO_ANALYZE=true
```

according to the existing configuration.

Flow:

```text
Documents READY
 ↓
Analyze
 ↓
UNDER_ANALYSIS
 ↓
AI Summary
 ↓
UNDER_REVIEW
```

---

# 24. AI SUMMARY CONTENT

The AI summary should contain:

```text
Clinical Findings
Diagnoses
Procedures
Medications
Symptoms
Conditions
Important Missing Information
Overall Case Summary
```

Every AI-generated item should contain:

```text
source document
page
snippet
confidence
review status
```

Display:

```text
AI Generated — Requires Human Review
```

---

# 25. DOCTOR REVIEW

Doctor opens:

```text
Case
 ↓
AI Summary
```

Doctor can:

```text
Confirm
Edit
Reject
```

each AI finding.

Doctor can also:

```text
Add Clinical Note
Approve Clinical Review
Reject Clinical Review
```

A rejected review requires a reason.

---

# 26. INSURANCE REVIEW

Insurance Reviewer opens the assigned case.

They can see:

```text
Patient
Case
Documents
AI Summary
Relevant Extracted Items
Doctor Review Status
```

They can:

```text
Add Insurance Note
Confirm permitted items
Edit permitted review information
Reject permitted items
Approve Insurance Review
Reject Insurance Review
```

Rejection requires a reason.

---

# 27. STAFF PERMISSIONS

Staff can:

```text
Create patient
Create case
Upload documents
Add case notes
View processing status
View completed AI summary
```

Staff cannot:

```text
Approve AI findings
Edit AI findings
Reject AI findings
Approve doctor review
Approve insurance review
Complete case
Manage users
```

Backend must enforce this.

---

# 28. ADMIN PERMISSIONS

Admin can:

```text
Create users
Manage users
View patients
View cases
View documents
View AI analysis
View reviews
View audit logs
```

Admin has organization-level access but should not be treated as a Doctor automatically.

---

# 29. AUDIT LOG

When case is created:

```text
CASE_CREATED
```

Record:

```text
user_id
organization_id
case_id
patient_id
timestamp
```

When document is uploaded:

```text
DOCUMENT_UPLOADED
```

When AI runs:

```text
ANALYSIS_STARTED
ANALYSIS_COMPLETED
```

When review happens:

```text
ITEM_CONFIRMED
ITEM_EDITED
ITEM_REJECTED
DOCTOR_REVIEW_APPROVED
DOCTOR_REVIEW_REJECTED
INSURANCE_REVIEW_APPROVED
INSURANCE_REVIEW_REJECTED
```

Never put medical text or PHI into audit metadata.

---

# 30. FRONTEND API DEBUGGING

The current "New Case" button is not working.

Trace the entire chain:

```text
Button
 ↓
Modal/Page
 ↓
Form submit
 ↓
Validation
 ↓
API function
 ↓
HTTP request
 ↓
FastAPI route
 ↓
Pydantic schema
 ↓
Service
 ↓
SQLAlchemy
 ↓
Neon PostgreSQL
 ↓
Response
 ↓
Frontend state
 ↓
Navigation
```

Find the actual failure.

Do not simply hide the error.

Check browser Network tab and backend logs.

Fix:

* incorrect endpoint
* incorrect HTTP method
* incorrect request body
* incorrect field names
* incorrect UUID handling
* authentication headers
* CORS
* Pydantic validation
* SQLAlchemy errors
* database constraints
* frontend state
* navigation after success

---

# 31. ERROR MESSAGES

Show useful frontend errors.

For example:

```text
401
Session expired. Please log in again.
```

```text
403
You do not have permission to create a case.
```

```text
422
Please check the highlighted fields.
```

```text
409
A similar patient already exists.
```

```text
500
Unable to create the case. Please try again.
```

Never display raw Python tracebacks to users.

---

# 32. LOADING STATE

When submitting:

```text
Creating case...
```

Disable:

```text
Create Case
```

to prevent duplicate submissions.

On success:

```text
Case created successfully.
```

Then navigate to the new case.

On failure:

```text
Create Case
```

becomes available again.

---

# 33. FORM STATE

Do not lose user-entered data when validation fails.

Use proper controlled/form state.

Validation should occur before the API request.

Highlight invalid fields.

---

# 34. SECURITY

Never trust:

```text
organization_id
created_by
```

from the frontend.

Backend derives:

```text
organization_id = current_user.organization_id
created_by = current_user.id
```

Do not allow Staff to submit arbitrary organization IDs.

Do not allow users to assign a Doctor/Reviewer from another organization.

---

# 35. DATABASE PERSISTENCE

After creating a case, verify directly that:

```text
patients
cases
audit_logs
```

contain the expected records.

If insurance is available, verify insurance information is persisted correctly.

Refresh the browser and verify the case still exists.

Log out and log back in.

Verify the authorized users can still see the case.

---

# 36. TEST THESE EXACT CASES

## Test 1 — New patient without insurance

```text
First Name: John
Last Name: Doe
DOB: 1990-01-01
Insurance: No
Case Title: General Consultation
Condition: Other
Symptoms: Headache
```

Expected:

```text
Patient created
Case created
Status = NEW
No insurance fields stored
```

---

## Test 2 — New patient with insurance

```text
First Name: Jane
Last Name: Smith
DOB: 1985-06-10
Insurance: Yes
Provider: Example Provider
Policy: POL123456
Case: Hypertension Follow-up
```

Expected:

```text
Patient created
Case created
Insurance persisted
Assigned Doctor persisted
Assigned Reviewer persisted if selected
Status = NEW
```

---

## Test 3 — Existing patient

Search for:

```text
Jane Smith
```

Select existing patient.

Create another case.

Expected:

```text
No duplicate patient
New case linked to existing patient
```

---

## Test 4 — Staff permission

Staff:

```text
Create Patient       PASS
Create Case          PASS
Upload Document      PASS
Add Note             PASS
Approve AI           FAIL / FORBIDDEN
Edit AI Finding      FAIL / FORBIDDEN
Complete Case        FAIL / FORBIDDEN
```

---

## Test 5 — Doctor permission

Doctor:

```text
View Case            PASS
Run Analysis         PASS
Confirm Item         PASS
Edit Item            PASS
Reject Item          PASS
Add Note             PASS
Approve Review       PASS
```

---

## Test 6 — Insurance Reviewer

Insurance Reviewer:

```text
View Assigned Case       PASS
View Documents           PASS
View AI Summary          PASS
Add Review Note          PASS
Review permitted items  PASS
Approve Review           PASS
```

---

# 37. FINAL END-TO-END TEST

Run this exact sequence:

```text
ADMIN
 ↓
Create Staff
Create Doctor
Create Insurance Reviewer
 ↓
STAFF LOGIN
 ↓
Cases
 ↓
New Case
 ↓
New Patient
 ↓
Enter Name
DOB
Gender
Insurance
Insurance Provider
Insurance Number
Disease/Condition
Symptoms
Previous Treatment
Notes
Doctor
Insurance Reviewer
 ↓
Create Case
 ↓
CASE CREATED
 ↓
Upload PDF
 ↓
Upload scanned medical image
 ↓
OCR
 ↓
Extraction
 ↓
Documents READY
 ↓
AI Analysis
 ↓
AI Summary Generated
 ↓
UNDER_REVIEW
 ↓
DOCTOR LOGIN
 ↓
Review AI Summary
 ↓
Confirm/Edit/Reject
 ↓
Add Clinical Note
 ↓
Approve Doctor Review
 ↓
INSURANCE REVIEWER LOGIN
 ↓
Open Assigned Case
 ↓
Review AI Summary
 ↓
Add Insurance Note
 ↓
Approve Insurance Review
 ↓
SYSTEM CHECKS REQUIRED REVIEWS
 ↓
COMPLETED
 ↓
AUDIT LOG VERIFIED
```

---

# 38. ACCEPTANCE CRITERIA

The task is complete only when:

* [ ] New Case button works
* [ ] New Case page/modal opens
* [ ] Form validation works
* [ ] Insurance Yes/No conditional fields work
* [ ] Insurance Provider dropdown works
* [ ] Insurance Number works
* [ ] Disease/Condition works
* [ ] Symptoms works
* [ ] Previous Treatment works
* [ ] Additional Notes works
* [ ] Doctor dropdown loads real users
* [ ] Insurance Reviewer dropdown loads real users
* [ ] Existing Patient search works
* [ ] New Patient creation works
* [ ] Duplicate patient handling works
* [ ] Case creation persists to Neon
* [ ] Case appears immediately after creation
* [ ] Case survives page refresh
* [ ] Document upload works
* [ ] OCR works
* [ ] Extraction works
* [ ] AI analysis works
* [ ] AI Summary appears
* [ ] Doctor can review
* [ ] Doctor can add notes
* [ ] Insurance Reviewer can review
* [ ] Insurance Reviewer can add notes
* [ ] Staff cannot approve AI
* [ ] Staff cannot complete case
* [ ] RBAC is enforced by backend
* [ ] Organization isolation works
* [ ] Audit logs are generated
* [ ] Case completion rules work
* [ ] No fake/mock production data remains in this flow
* [ ] No MongoDB/Motor is used in the active execution path

---

# 39. FINAL REPORT

After implementation, provide:

```text
NEW CASE UI                  PASS/FAIL
PATIENT CREATION             PASS/FAIL
EXISTING PATIENT              PASS/FAIL
INSURANCE YES/NO              PASS/FAIL
INSURANCE PROVIDER             PASS/FAIL
CASE CREATION API             PASS/FAIL
NEON PERSISTENCE              PASS/FAIL
DOCTOR ASSIGNMENT             PASS/FAIL
REVIEWER ASSIGNMENT            PASS/FAIL
DOCUMENT UPLOAD               PASS/FAIL
OCR                           PASS/FAIL
AI EXTRACTION                 PASS/FAIL
AI SUMMARY                    PASS/FAIL
DOCTOR REVIEW                 PASS/FAIL
INSURANCE REVIEW              PASS/FAIL
STAFF RBAC                    PASS/FAIL
CASE COMPLETION               PASS/FAIL
AUDIT LOG                     PASS/FAIL
END-TO-END                    PASS/FAIL
```

If something could not actually be tested, explicitly mark:

```text
NOT TESTED
```

Do not claim PASS without testing.

The final goal is a real working flow:

```text
CREATE PATIENT
      ↓
CREATE CASE
      ↓
UPLOAD DOCUMENTS
      ↓
AI PROCESSING
      ↓
AI SUMMARY
      ↓
DOCTOR REVIEW
      +
INSURANCE REVIEW
      ↓
APPROVAL
      ↓
CASE COMPLETED
```

No part of this workflow should depend on hardcoded frontend mock data.

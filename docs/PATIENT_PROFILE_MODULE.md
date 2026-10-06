# Patient Onboarding & Profile Module

## New patient registration
New patients must complete an essential onboarding profile before entering the patient workspace:
- Identity: full name, date of birth, age, gender, blood group, phone
- Body profile: height and weight
- Medical history: allergies, existing conditions, current medications, previous surgeries/hospitalizations, family medical history
- Emergency readiness: emergency contact and address
- Account: email and password
- Confirmation checkbox

Registration creates a patient account and a linked patient record in SQLite for the local academic prototype.

## Profile editing
Patients can open **My Profile** from the top navigation and update their identity, body profile, medical history and emergency information. Changes are persisted to the database and an audit entry is created.

## Safety
This is an academic prototype. It does not provide medical diagnosis or replace clinician review. Real production deployment would require proper authentication, authorization, encryption, consent management, audit controls and clinical validation.

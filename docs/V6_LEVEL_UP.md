# NEXUS CARE v6 — Level-Up Feature Set

## Multimodal clinical intelligence
The prototype combines reported symptoms, structured patient profile context, simulated vitals, and Guardian Vision signals into an explainable workflow. It is intentionally framed as triage decision support, not diagnosis.

## Dynamic interview
The patient can enter symptoms naturally, use quick scenario prompts, and optionally use browser speech recognition. NLP extracts symptom concepts, negation, severity, and duration.

## Explainability
Every triage response exposes ESI, risk, confidence, contributing reasons, and ranked possible conditions.

## Simulation Lab
Clinicians can change age, oxygen saturation, and symptom severity and observe the educational risk-fusion result. This is a simulation, not a clinical recommendation.

## Hospital command center
The clinician workspace provides a prioritized queue, emergency counts, hospital network, FHIR explorer, and clinician ESI override.

## Patient intelligence
The patient workspace includes profile editing, longitudinal timeline, privacy/safety center, AI intake, Guardian Vision, emergency workflow, and FHIR export.

## ML
The included XGBoost model is trained from synthetic/generated symptom profiles for academic demonstration. The disease labels are possible-condition categories and should not be interpreted as medically validated diagnoses.

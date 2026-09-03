Create and write a complete README.md file for the AASHRAY AI/ML module.

The file should be professional and suitable for a Smart India Hackathon 2026 project. Use clean Markdown formatting with headings, bullet points, code blocks, and tables where useful.

Use the following exact project information:

# AASHRAY — AI/ML Module

AI/ML and geospatial risk-analysis module for the AASHRAY multi-hazard disaster risk platform.

## Overview

This module processes geospatial and historical hazard data to generate village-level disaster risk information.

Current pilot implementations cover:

- Landslide susceptibility
- Flood hazard
- Coastal erosion/proximity
- Cyclone hazard
- Rainfall hazard
- Multi-hazard risk fusion

## Study Areas

### Wayanad, Kerala

Landslide susceptibility and dynamic rainfall-risk analysis using:

- Digital Elevation Model (DEM)
- Elevation
- Slope
- Aspect
- Topographic Wetness Index (TWI)
- Historical landslide inventory
- IMD gridded rainfall

The landslide susceptibility model uses Random Forest.

### Kendrapara, Odisha

Village-level multi-hazard analysis using:

- Coastal erosion baseline
- Shoreline proximity proxy
- Historical flood hazard
- Historical cyclone tracks
- IMD rainfall
- Multi-hazard fusion

The Kendrapara pipeline currently produces risk scores for 808 coastal-belt villages.

## Architecture

Use this architecture diagram:

Official / Historical Data
          ↓
   Data Preprocessing
          ↓
    Feature Engineering
          ↓
   Hazard-specific Models
          ↓
   Multi-Hazard Fusion
          ↓
 Village-level Risk Score
          ↓
      FastAPI Layer
          ↓
 AASHRAY Backend / Dashboard

## Main Components

The source structure is:

src/
├── api/
├── features/
├── hazards/
├── models/
├── output/
├── preprocessing/
└── validation/

Explain each directory briefly.

### API

File:

src/api/kendrapara_api.py

Explain that it provides village-level risk information and statistics through FastAPI.

### Models

Directory:

src/models/

Mention that it contains:

- Landslide susceptibility model
- Dynamic rainfall risk engine
- Village risk engine
- Multi-hazard fusion

### Hazard Modules

Directory:

src/hazards/

Mention that it contains hazard-specific processing for:

- Coastal hazards
- Floods
- Cyclones

## Trained Model

The trained landslide susceptibility Random Forest model is:

models/aashray_susceptibility_rf.joblib

Mention that this is the trained Random Forest model used for landslide susceptibility analysis.

## Data

Explain that raw datasets are intentionally excluded from Git using .gitignore.

Mention that processed CSV outputs included in the repository are lightweight demonstration and integration datasets.

Mention that large raster, NetCDF, PDF, ZIP and raw geospatial datasets should be obtained from their respective official sources rather than stored in Git.

## Important Data Limitations

Include these limitations clearly and honestly:

- The Kendrapara coastal erosion baseline is based on district-level NCCR shoreline statistics.
- Shoreline proximity is currently a spatial proxy based on the coastal-village boundary and is not an official measured shoreline.
- Flood hazard coverage is based on the villages available in the official Odisha Flood Hazard Atlas.
- Cyclone hazard is a historical proximity/intensity proxy based on IMD best-track data.
- Rainfall hazard scores are modelled indicators and are not official IMD hazard classifications.

Explain that these limitations are intentionally documented so that proxy indicators are not represented as direct observations.

## Multi-Hazard Fusion

Add a section explaining that the Kendrapara multi-hazard model combines:

- Coastal hazard
- Flood hazard
- Cyclone hazard
- Rainfall hazard

The fusion is availability-aware, meaning that if a particular hazard is unavailable for a village, the available hazard weights are renormalized instead of treating missing data as zero risk.

The current Kendrapara fusion uses these nominal weights:

- Coastal: 30%
- Flood: 25%
- Cyclone: 25%
- Rainfall: 20%

The output is a village-level multi-hazard risk score and risk category.

## Current Kendrapara Results

Include these validated results:

- Total coastal-belt villages: 808
- Villages with all 4 hazards: 785
- Villages with 3 available hazards: 23
- Multi-hazard score minimum: 0.2899
- Multi-hazard score mean: 0.4864
- Multi-hazard score maximum: 0.7545
- MODERATE: 544 villages
- HIGH: 262 villages
- VERY HIGH: 2 villages
- LOW: 0 villages

Make it clear that these are pilot/model outputs and not official government risk classifications.

## Wayanad Landslide Model Results

Include:

- Training samples: 195
- Test samples: 65
- Positive landslide samples: 65
- Background/negative samples: 195
- Accuracy: 0.7538
- ROC-AUC: 0.8253

Feature importance:

- Elevation: 0.3850
- TWI: 0.2219
- Slope: 0.2082
- Aspect: 0.1849

Mention that the model is a pilot susceptibility model and should not be interpreted as an official government susceptibility classification.

## API Endpoints

Document these FastAPI endpoints:

GET /
GET /api/villages
GET /api/village/{vlcode}
GET /api/statistics
GET /api/top-risk
GET /api/map

Explain each endpoint briefly.

Mention that the API is intended to provide structured AI/ML outputs to the AASHRAY backend and dashboard.

## Integration

Explain that the AI/ML module is designed to expose structured village-level risk information to the AASHRAY backend.

The frontend/dashboard is maintained separately by the frontend team.

The Java backend is maintained separately by the backend team.

Do not claim that the frontend is directly connected to this FastAPI service unless the repository actually contains such integration.

## Data Sources

Create a section describing the main official/credible data sources used:

- IMD — India Meteorological Department
- KSDMA — Kerala State Disaster Management Authority
- OSDMA — Odisha State Disaster Management Authority
- NRSC/ISRO — National Remote Sensing Centre / Indian Space Research Organisation
- NCCR — National Centre for Coastal Research
- NWIC — National Water Informatics Centre
- SAC/ISRO — Space Applications Centre / ISRO

Explain briefly what each source contributed.

## Development Environment

Mention:

- Python 3.11
- FastAPI
- Uvicorn
- Pandas
- NumPy
- GeoPandas
- Rasterio
- Xarray
- Scikit-learn
- Joblib
- PyMuPDF
- Matplotlib

Do not invent a requirements.txt file because one is not currently present.

## Running the API

Show the command:

python -m uvicorn src.api.kendrapara_api:app --reload

Mention that the API runs locally on:

http://127.0.0.1:8000

Do not include clickable URLs or external links.

## Project Structure

Show a clean project tree similar to:

ai-ml/
├── configs/
├── data/
│   └── processed/
├── models/
├── notebooks/
├── src/
│   ├── api/
│   ├── features/
│   ├── hazards/
│   ├── models/
│   ├── output/
│   ├── preprocessing/
│   └── validation/
├── tests/
├── data_registry.csv
├── .gitignore
└── README.md

## Reproducibility

Explain that the repository intentionally excludes large raw datasets and generated raster files.

Explain that the data_registry.csv file records information about datasets used by the project.

Explain that official source datasets should be downloaded separately when reproducing the pipeline.

## Validation

Mention that the project contains validation scripts for:

- Coastal features
- Kendrapara flood hazard
- Kendrapara multi-hazard fusion
- Kendrapara four-hazard fusion
- Wayanad multi-hazard raster
- Landslide susceptibility model

Explain that validation checks include:

- Required columns
- Missing village identifiers
- Duplicate village codes
- CRS consistency
- Geometry validity
- Hazard score ranges
- Fusion calculations
- Output consistency

## Limitations and Future Improvements

Add a professional section explaining future improvements such as:

- Replace coastal proximity proxy with official high-resolution shoreline geometry.
- Add village-level measured shoreline-change rates.
- Improve flood spatial coverage where source data is unavailable.
- Add more years of rainfall data.
- Incorporate real-time rainfall feeds.
- Incorporate real-time cyclone warnings.
- Add more historical landslide observations.
- Improve model calibration with larger datasets.
- Add uncertainty estimation.
- Integrate the AI/ML service with the Java backend.
- Connect the validated backend API with the existing frontend dashboard.

Clearly distinguish current implementation from future work.

## Security and Repository Practices

Mention:

- Raw datasets are excluded from Git.
- Python virtual environments are excluded.
- Large raster and geospatial files are excluded.
- API credentials and secrets must never be committed.
- Official datasets should be downloaded from their authoritative sources.

## Hackathon Context

Add:

Project: AASHRAY
Hackathon: Smart India Hackathon 2026
Module: AI/ML and Geospatial Risk Analysis

End with a short professional statement describing AASHRAY as a multi-hazard disaster risk platform intended to support data-driven disaster preparedness and decision-making.

IMPORTANT:
- Write the complete README.md.
- Do not add fictional features.
- Do not claim that proxy datasets are official village-level measurements.
- Do not claim real-time integration unless it actually exists.
- Keep the tone professional and suitable for judges, developers, and technical reviewers.
- Make the Markdown visually clean and easy to read.
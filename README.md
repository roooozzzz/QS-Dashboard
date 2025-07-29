# QS World University Rankings Dashboard

A comprehensive dashboard for exploring QS World University Rankings data from 2022 to 2026.

## Features

- **Interactive Dashboard**: Built with Streamlit for easy data exploration
- **Multi-year Data**: Covers QS rankings from 2022 to 2026
- **Advanced Filtering**: Filter by year, region, country, and indicators
- **Smart Search**: Fuzzy search for universities with autocomplete
- **Comprehensive Metrics**: All 10 QS indicators with both Score and Rank data
- **Regional Analysis**: Universities categorized by 5 regions (Africa, Americas, Asia, Europe, Oceania)

## Data Coverage

- **Years**: 2022-2026
- **Indicators**: 
  - Academic Reputation (AR)
  - Employer Reputation (ER)
  - Faculty Student Ratio (FSR)
  - Citations per Faculty (CPF)
  - International Faculty Ratio (IFR)
  - International Students Ratio (ISR)
  - International Students Diversity (ISD)
  - International Research Network (IRN)
  - Employment Outcomes (EO)
  - Sustainability (SUS)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the dashboard:
   ```bash
   streamlit run dashboard.py
   ```

## Deployment

This dashboard is designed to be deployed on Streamlit Cloud. Simply connect your GitHub repository to Streamlit Cloud for automatic deployment.

## Data Source

QS World University Rankings data from 2022-2026, processed and stored in SQLite database format. 
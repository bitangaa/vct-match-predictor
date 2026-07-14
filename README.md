# VCT Match Predictor

A machine learning application that predicts the outcomes of official Valorant Champions Tour (VCT) matches using historical team and player performance data. The project automatically collects match statistics from VLR.gg, engineers predictive features, and estimates each team's probability of winning before a match.

---

## Overview

This project combines web scraping, data engineering, and supervised machine learning to model competitive Valorant matches. Historical VCT data is collected and transformed into a structured dataset containing team, player, and map-level statistics. These features are then used to train classification models that estimate pre-match win probabilities.

The goal of the project is to demonstrate an end-to-end machine learning pipeline, from data acquisition to prediction.

---

## Features

- Automated scraping of official VCT match, team, and player statistics from VLR.gg
- Historical dataset generation for model training
- Feature engineering using team, player, and map performance metrics
- Machine learning models for match outcome prediction
- Probability-based predictions rather than binary classifications
- Modular pipeline for updating data and retraining models

---

## Data Pipeline

### Data Collection

The application collects historical VCT data directly from VLR.gg, including:

- Match results
- Team statistics
- Player statistics
- Map performance
- Event information

The scraping pipeline automatically parses and structures raw HTML into machine-readable datasets.

### Feature Engineering

Features are generated from historical performance, including:

- Recent team win rate
- Map-specific win percentages
- Average player ACS
- Kill/Death ratio
- ADR (Average Damage per Round)
- KAST
- Headshot percentage
- Opponent strength
- Rolling team performance metrics

Additional features can be incorporated as new statistics become available.

---

## Machine Learning

Historical match data is used to train supervised classification models that estimate the probability of each team winning a match.

The training pipeline includes:

- Data preprocessing
- Missing value handling
- Feature normalization
- Train/test splitting
- Model evaluation
- Probability calibration

Model performance is evaluated using standard classification metrics such as:

- Accuracy
- ROC-AUC
- Log Loss
- Precision
- Recall

---

## Example Prediction

```
Match
------
Sentinels vs Gen.G

Predicted Win Probability

Sentinels    64.3%
Gen.G        35.7%
```

---

## Project Structure

```
vct-match-predictor/
│
├── data/              # Raw and processed datasets
├── scraping/          # Web scraping utilities
├── preprocessing/     # Data cleaning and feature engineering
├── models/            # Model training and saved models
├── prediction/        # Match prediction pipeline
├── notebooks/         # Exploratory analysis
├── app/               # Optional web interface
└── README.md
```

---

## Technologies

- Python
- Pandas
- NumPy
- scikit-learn
- Requests
- BeautifulSoup
- Selenium
- Matplotlib
- Jupyter Notebook

---

## Future Improvements

- Incorporate live roster changes
- Player rating system using Elo or Glicko
- Ensemble modeling
- Automated daily data updates
- Interactive dashboard for match predictions
- Explainable AI visualizations using SHAP values

---

## License

This project is intended for educational and portfolio purposes.

VLR.gg owns the underlying match data. This project is not affiliated with Riot Games or VLR.gg.

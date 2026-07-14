# 🔮 VCT Match Predictor

A machine learning-powered tool that predicts match outcomes for official **Valorant Champions Tour (VCT)** games. It uses real-time team and player statistics scraped from [vlr.gg](https://www.vlr.gg/) to estimate **win probabilities** before each match.

---

## 📊 Features

- ✅ Scrapes **team** and **player** performance data from VCT matches on vlr.gg  
- ✅ Parses map history, recent match results, player K/D, ACS, headshot %, and more  
- ✅ Uses a trained ML model to predict **win probability** for each team  
- ✅ Outputs predictions via terminal or as a web dashboard (optional)  
- ✅ Configurable match preview (past N games, event filters, etc.)

---

## 🧠 How It Works

1. **Data Scraping**  
   Pulls structured team & player statistics from [vlr.gg](https://www.vlr.gg/), using custom scrapers powered by `requests`, `BeautifulSoup`, or `Selenium`.

2. **Feature Engineering**  
   Aggregates relevant match features:
   - Win rate (last N games)
   - Map win percentages
   - Player form (ACS, ADR, KAST)
   - Team Elo (optional)
   - Opponent strength

3. **Prediction Model**  
   A machine learning model (e.g., logistic regression, XGBoost, or a neural net) is trained on historical matches to predict win probabilities.

4. **Match Output**  
   Displays team names, stats preview, and predicted win probability (e.g., `Team A: 63% | Team B: 37%`).

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/vct-match-predictor.git
cd vct-match-predictor

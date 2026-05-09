# 🌱 AquaSmart — Intelligent Irrigation System

AquaSmart is an AI-powered smart irrigation forecasting application designed to help farmers optimize water usage and improve crop yields. By combining real-time weather data with machine learning predictions, AquaSmart provides actionable insights on when to irrigate, how much water to use, and when to skip watering to conserve resources.

## ✨ Features

- **🔮 AI Prediction Engine:** Uses a custom Logistic Regression model trained on real agricultural data to predict irrigation needs based on soil nutrients (N, P, K), pH, temperature, humidity, and rainfall.
- **🌤️ Live Weather Integration:** Automatically fetches real-time weather and 3-day historical rainfall data for your specific GPS location or selected city using the Open-Meteo API.
- **🗺️ Interactive Regional Map:** A fully interactive Leaflet.js map displaying major agricultural zones across India with customized localized advice.
- **🤖 Smart AI Assistant:** A built-in chatbot that provides instant answers regarding specific crop water requirements, seasonal advice (like monsoon tips), and soil management.
- **📅 Crop Calendar:** Dynamic monthly irrigation planning based on specific crop life cycles and seasonal changes (Kharif, Rabi, Zaid).
- **💧 Water Savings Calculator:** Tracks potential water and cost savings compared to traditional manual irrigation methods.

## 🚀 Tech Stack

- **Backend:** Python, Flask
- **Machine Learning:** Scikit-Learn (Logistic Regression), Pandas, NumPy
- **Frontend:** Vanilla HTML, CSS, JavaScript
- **Mapping:** Leaflet.js
- **Charts:** Chart.js
- **Icons:** Lucide Icons

## ⚙️ Local Development

To run this project locally on your machine:

1. **Clone the repository**
   ```bash
   git clone https://github.com/akshaynelgundh2007-png/aquasmart.git
   cd aquasmart
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask application**
   ```bash
   python app.py
   ```

4. **Open in browser**
   Navigate to `http://localhost:5000`

## 🧠 Machine Learning Model

The core prediction engine uses a **Logistic Regression** model trained to 87.95% accuracy. 

To retrain the model locally or generate a new dataset:
```bash
# Generate the dataset using real Kaggle crop data
python generate_dataset.py

# Train the model and update the weights
python train_model.py
```

## 🌐 Deployment

This application is configured for easy deployment on **Render** using Gunicorn as the WSGI HTTP server.
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

## 📄 License

This project was developed for educational purposes and agricultural optimization.

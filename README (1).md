# 🚂 MBTA Commuter Rail Tracker

A live map of MBTA commuter rail train positions, built with Python and Streamlit.

---

## Setup (run locally first)

### 1. Get a free MBTA API key
Go to https://api-v3.mbta.com/register and create a free account.
Copy your API key.

### 2. Add your key to the app
Open `app.py` and find this line near the top:
```python
API_KEY = "YOUR_API_KEY_HERE"
```
Replace `YOUR_API_KEY_HERE` with your actual key.

### 3. Install dependencies
Make sure you have Python 3.9+ installed, then run:
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```
Your browser will open automatically at http://localhost:8501

---

## Deploy to Streamlit Cloud (free, accessible on your phone)

1. Push this folder to a GitHub repository
   - Create a free account at https://github.com if you don't have one
   - Create a new repository and upload these files

2. Go to https://streamlit.io/cloud and sign in with GitHub

3. Click **"New app"** → select your repository → set Main file = `app.py`

4. Before deploying, add your API key as a **Secret** (don't put real keys in GitHub!):
   - In the Streamlit Cloud dashboard, go to your app → Settings → Secrets
   - Add:
     ```
     MBTA_API_KEY = "your_actual_key_here"
     ```
   - Then update `app.py` to read it:
     ```python
     import os
     API_KEY = st.secrets.get("MBTA_API_KEY", os.getenv("MBTA_API_KEY", ""))
     ```

5. Click **Deploy** — you'll get a public URL in about 60 seconds

6. Open that URL on your iPhone → tap the Share button → "Add to Home Screen"
   Now it lives on your home screen like a real app! 🎉

---

## How the code works

```
app.py
│
├── get_trains()        # Calls MBTA API, returns JSON data for all active trains
├── get_stops()         # Fetches stop names so popups say "South Station" not "place-sstat"
├── build_map()         # Creates a Folium map and drops a pin for each train
│
└── UI section          # Streamlit widgets: title, sidebar filter, metrics, map
```

The app re-fetches data every 20 seconds automatically via `time.sleep(20)` + `st.rerun()`.

---

## Customization ideas
- Change the map tile style (try `"OpenStreetMap"` or `"CartoDB dark_matter"` in `build_map()`)
- Add a train list below the map showing all trains in a table
- Color each line differently instead of all blue
- Add alerts for delays using the MBTA `/alerts` endpoint

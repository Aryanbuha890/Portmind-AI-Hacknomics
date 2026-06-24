import os
import requests
from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# Load env variables from .env
load_dotenv()

# Import ML predict and SimPy simulation logic from subpackages
from prediction.predict import predict_scenario, predict_vessel_etas, generate_ai_report, compute_kpis
from prediction.simulator import run_monte_carlo_simulation
from doc_ai.doc_ai_parser import extract_text_from_file, parse_document_by_template

app = FastAPI(title="PortMind AI — Port Operations Intelligence API")

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────
# Input Schemas
# ──────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    wind: float
    visibility: float
    precip: float
    temp: float
    vessels: int
    yard: float
    berths: int
    days: int

class WeatherRequest(BaseModel):
    city: str
    vessels: int
    yard: float

class PredictRequest(BaseModel):
    wind_speed: float
    visibility: float
    precipitation: float
    temperature: float
    vessel_queue: int
    yard_occupancy: float
    is_holiday: int = 0


# ──────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────

@app.post("/api/simulate")
async def simulate(req: SimulateRequest):
    """Run full ML + SimPy Monte Carlo simulation with custom parameters."""
    try:
        results = run_monte_carlo_simulation(
            wind_speed=req.wind,
            visibility=req.visibility,
            precipitation=req.precip,
            temperature=req.temp,
            vessel_queue=req.vessels,
            yard_occupancy=req.yard,
            num_berths=req.berths,
            sim_duration_days=req.days
        )
        return {"status": "success", "result": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict")
async def predict(req: PredictRequest):
    """
    Fast ML prediction endpoint.
    Returns: operational predictions + vessel ETAs + AI report + KPIs.
    """
    try:
        # 1. Run ML predictions for the scenario
        predictions = predict_scenario(
            wind_speed=req.wind_speed,
            visibility=req.visibility,
            precipitation=req.precipitation,
            temperature=req.temperature,
            vessel_queue=req.vessel_queue,
            yard_occupancy=req.yard_occupancy,
            is_holiday=req.is_holiday
        )

        # 2. Predict ETA delays for demo vessel fleet
        vessels = predict_vessel_etas(
            wind_speed=req.wind_speed,
            visibility=req.visibility,
            precipitation=req.precipitation,
            temperature=req.temperature,
            vessel_queue=req.vessel_queue,
            yard_occupancy=req.yard_occupancy,
            is_holiday=req.is_holiday
        )

        # 3. Build weather params dict for report
        weather_params = {
            'wind_speed': req.wind_speed,
            'visibility': req.visibility,
            'precipitation': req.precipitation,
            'temperature': req.temperature,
        }

        # 4. Generate AI analysis report (Gemini or fallback)
        ai_report = generate_ai_report(predictions, weather_params, vessels)

        # 5. Compute KPIs
        kpis = compute_kpis(predictions, vessels)

        return {
            "status": "success",
            "predictions": predictions,
            "vessels": vessels,
            "ai_report": ai_report,
            "kpis": kpis,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/weather")
async def weather(req: WeatherRequest):
    """Fetch real-time weather and return ML predictions."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        # Fallback to Rotterdam default metrics if API Key is not found
        default_weather = {
            "wind_speed": 4.2,
            "visibility": 10000.0,
            "precipitation": 0.0,
            "temperature": 16.5,
            "city": req.city,
            "is_fallback": True,
            "warning": "OPENWEATHER_API_KEY not configured"
        }
        try:
            preds = predict_scenario(4.2, 10000.0, 0.0, 16.5, req.vessels, req.yard, 0)
            return {"status": "success", "weather": default_weather, "predictions": preds}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fallbacks prediction failed: {str(e)}")
            
    url = f"http://api.openweathermap.org/data/2.5/weather?q={req.city}&appid={api_key}&units=metric"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        wind_speed = float(data['wind']['speed'])
        visibility = float(data.get('visibility', 10000.0))
        precipitation = float(data.get('rain', {}).get('1h', 0.0))
        temperature = float(data['main']['temp'])
        
        weather_data = {
            "wind_speed": wind_speed,
            "visibility": visibility,
            "precipitation": precipitation,
            "temperature": temperature,
            "city": req.city,
            "is_fallback": False
        }
        
        preds = predict_scenario(wind_speed, visibility, precipitation, temperature, req.vessels, req.yard, 0)
        return {"status": "success", "weather": weather_data, "predictions": preds}
    except Exception as e:
        # Fallback if API fails or network fails
        default_weather = {
            "wind_speed": 4.2,
            "visibility": 10000.0,
            "precipitation": 0.0,
            "temperature": 16.5,
            "city": req.city,
            "is_fallback": True,
            "error": str(e)
        }
        try:
            preds = predict_scenario(4.2, 10000.0, 0.0, 16.5, req.vessels, req.yard, 0)
            return {"status": "success", "weather": default_weather, "predictions": preds}
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"API error: {str(e)}. Fallbacks failed: {str(e2)}")

@app.post("/api/docs-ai/parse")
async def parse_document(
    file: UploadFile,
    template_id: str = Form("TMP-001")
):
    """
    Parse an uploaded manifest PDF or TXT file using local DPD-NEE NLP model.
    """
    try:
        file_bytes = await file.read()
        filename = file.filename or "document.txt"
        extracted_text = extract_text_from_file(file_bytes, filename)
        parsed_fields = parse_document_by_template(extracted_text, template_id)
        return {
            "status": "success",
            "filename": filename,
            "template_id": template_id,
            "fields": parsed_fields
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {str(e)}")

if __name__ == '__main__':
    # Run server locally on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

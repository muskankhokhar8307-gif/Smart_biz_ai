"""Transparent baseline forecasting; no model is presented as certainty."""
import numpy as np
import pandas as pd
from analytics import monthly_sales


def forecast_next_month(db):
    monthly = monthly_sales(db)
    if monthly.empty:
        return {
            "status": "insufficient_data", "message": "No completed sales are available for forecasting.",
            "prediction": None, "lower": None, "upper": None, "months_used": 0,
        }
    values = monthly["revenue"].astype(float).to_numpy()
    if len(values) < 3:
        return {
            "status": "insufficient_data",
            "message": "At least three months of sales history are recommended before displaying a forecast.",
            "prediction": None, "lower": None, "upper": None, "months_used": len(values),
        }
    # Baseline: mean of up to the latest 3 observed months.
    window = values[-3:]
    prediction = max(0.0, float(np.mean(window)))
    # Descriptive range from recent variability; not a formal confidence interval.
    spread = float(np.std(window, ddof=1)) if len(window) > 1 else 0.0
    lower = max(0.0, prediction - spread)
    upper = prediction + spread
    last_month = str(monthly.iloc[-1]["month"])
    next_period = (pd.Period(last_month, freq="M") + 1).strftime("%Y-%m")
    return {
        "status": "ok", "method": "Mean of the latest three observed months",
        "forecast_month": next_period, "prediction": round(prediction, 2),
        "lower": round(lower, 2), "upper": round(upper, 2),
        "months_used": len(values),
        "message": "Baseline estimate only; the range describes recent variability and is not a formal confidence interval.",
    }

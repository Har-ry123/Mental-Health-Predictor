from __future__ import annotations

import io
import csv
import random
from typing import Literal, List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse


router = APIRouter(prefix="/eeg", tags=["eeg"])


NUM_FEATURES = 1024


TargetType = Literal[
    "depression",
    "severity",
    "anxiety",
    "stress",
    "ptsd",
    "ocd",
    "adhd",
    "burnout",
    "insomnia",
    "wellbeing",
]


def _predict_stub(features: list[float], target: TargetType) -> dict:
    # Simple placeholder model: mean-based heuristic
    avg = sum(features) / max(len(features), 1)
    if target == "depression":
        probability = max(0.0, min(1.0, (avg + 1.0) / 2.0))
        label = "Depressed" if probability >= 0.5 else "Not Depressed"
        return {"label": label, "probability": round(probability, 3)}
    elif target == "severity":
        # Map average to 0-10 severity scale
        severity = int(max(0, min(10, round((avg + 1.0) * 5))))
        return {"severity": severity}
    elif target == "anxiety":
        # Probability skewed by variance
        mean = avg
        var = sum((x - mean) ** 2 for x in features) / max(len(features), 1)
        score = min(1.0, (var / 5.0))  # heuristic scaling
        label = "Anxious" if score >= 0.5 else "Calm"
        return {"label": label, "probability": round(score, 3)}
    elif target == "stress":
        # Map absolute mean to a 0-100 stress score
        stress = int(max(0, min(100, round(abs(avg) * 100))))
        return {"stress": stress}
    elif target == "ptsd":
        score = max(0.0, min(1.0, abs(avg)))
        return {"label": "PTSD Risk" if score >= 0.5 else "Low Risk", "probability": round(score, 3)}
    elif target == "ocd":
        score = max(0.0, min(1.0, (avg + 1) / 2))
        return {"label": "OCD Traits" if score >= 0.5 else "Low Traits", "probability": round(score, 3)}
    elif target == "adhd":
        score = max(0.0, min(1.0, (sum(x for x in features if x > 0) / max(len(features), 1))))
        return {"label": "ADHD Traits" if score >= 0.5 else "Low Traits", "probability": round(score, 3)}
    elif target == "burnout":
        level = int(max(0, min(100, round((abs(avg) * 100)))))
        return {"burnout": level}
    elif target == "insomnia":
        score = max(0, min(10, round((1 - avg) * 5 + 5)))
        return {"insomnia": score}
    else:  # wellbeing
        score = int(max(0, min(100, round((avg + 1) * 50))))
        return {"wellbeing": score}


def _sample_csv_stream() -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf)
    header = [f"f{i}" for i in range(NUM_FEATURES)]
    writer.writerow(header)
    # Generate 5 random rows in [-1, 1]
    for _ in range(5):
        row = [round(random.uniform(-1.0, 1.0), 4) for _ in range(NUM_FEATURES)]
        writer.writerow(row)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_eeg.csv"},
    )


@router.get("/sample.csv")
def generate_sample_csv() -> StreamingResponse:
    return _sample_csv_stream()


@router.get("/sample")
def generate_sample_csv_alt() -> StreamingResponse:
    return _sample_csv_stream()


@router.post("/predict/{target}")
async def predict(
    target: TargetType,
    file: UploadFile = File(...),
) -> JSONResponse:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    content = (await file.read()).decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV is empty")

    # Skip header if looks like header
    data_rows = rows[1:] if rows and any(isinstance(v, str) for v in rows[0]) else rows
    if not data_rows:
        raise HTTPException(status_code=400, detail="CSV has no data rows")

    # Use the first row only for prediction
    try:
        features = [float(x) for x in data_rows[0][:NUM_FEATURES]]
    except ValueError:
        raise HTTPException(status_code=400, detail="CSV contains non-numeric values")
    if len(features) < NUM_FEATURES:
        raise HTTPException(status_code=400, detail=f"Expected {NUM_FEATURES} features, got {len(features)}")

    result = _predict_stub(features, target)
    return JSONResponse({"target": target, "result": result})


@router.post("/predict/batch/{target}")
async def predict_batch(
    target: TargetType,
    file: UploadFile = File(...),
) -> JSONResponse:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    content = (await file.read()).decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV is empty")

    data_rows = rows[1:] if rows and any(isinstance(v, str) for v in rows[0]) else rows
    results: List[dict] = []
    for row in data_rows:
        try:
            feats = [float(x) for x in row[:NUM_FEATURES]]
        except ValueError:
            continue
        if len(feats) < NUM_FEATURES:
            continue
        results.append(_predict_stub(feats, target))

    summary = {}
    if target in {"depression", "anxiety", "ptsd", "ocd", "adhd"}:
        probs = [r["probability"] for r in results if "probability" in r]
        if probs:
            summary = {"mean_probability": round(sum(probs) / len(probs), 3)}
    elif target == "severity":
        vals = [r["severity"] for r in results if "severity" in r]
        if vals:
            summary = {
                "mean": round(sum(vals) / len(vals), 2),
                "min": min(vals),
                "max": max(vals),
            }
    elif target in {"stress", "burnout", "wellbeing"}:
        key = "stress" if target == "stress" else ("burnout" if target == "burnout" else "wellbeing")
        vals = [r[key] for r in results if key in r]
        if vals:
            summary = {
                "mean": round(sum(vals) / len(vals), 2),
                "min": min(vals),
                "max": max(vals),
            }
    elif target == "insomnia":
        vals = [r["insomnia"] for r in results if "insomnia" in r]
        if vals:
            summary = {
                "mean": round(sum(vals) / len(vals), 2),
                "min": min(vals),
                "max": max(vals),
            }

    return JSONResponse({"target": target, "count": len(results), "results": results[:200], "summary": summary})



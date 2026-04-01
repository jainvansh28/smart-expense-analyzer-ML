# ML Services Port Conflict - Fixed ✅

## Problem

Both ML services were trying to run on port 8001, causing a port conflict:
- ML Prediction Service: Port 8001
- ML Anomaly Detection Service: Port 8001 ❌ (Conflict!)

## Solution

Changed ML Anomaly Detection Service to port 8002.

## Port Allocation

```
┌─────────────────────────────────────────────────────┐
│                  Service Ports                       │
├─────────────────────────────────────────────────────┤
│  Spring Boot Backend          → Port 8080           │
│  ML Prediction Service        → Port 8001           │
│  ML Anomaly Detection Service → Port 8002  ← NEW    │
│  Frontend (React)             → Port 3000           │
└─────────────────────────────────────────────────────┘
```

## Changes Made

### 1. ML Anomaly Service (Python)
**File**: `ml-service/ml_anomaly_service.py`

**Changed**:
```python
# Before
uvicorn.run(app, host="0.0.0.0", port=8001)

# After
uvicorn.run(app, host="0.0.0.0", port=8002)
```

Also updated startup message:
```python
print("Listening on: http://localhost:8002")
```

### 2. Backend Configuration
**File**: `backend/src/main/resources/application.properties`

**Changed**:
```properties
# Before
ml.anomaly.service.url=http://localhost:8001

# After
ml.anomaly.service.url=http://localhost:8002
```

### 3. ML Anomaly Client (Java)
**File**: `backend/src/main/java/com/expenseanalyzer/service/MLAnomalyClient.java`

**Changed**:
```java
// Before
@Value("${ml.anomaly.service.url:http://localhost:8001}")

// After
@Value("${ml.anomaly.service.url:http://localhost:8002}")
```

### 4. Test Script
**File**: `ml-service/test_anomaly_service.py`

**Changed**:
```python
# Before
BASE_URL = "http://localhost:8001"

# After
BASE_URL = "http://localhost:8002"
```

### 5. Start Scripts
**Files**: 
- `ml-service/start_anomaly_service.bat`
- `ml-service/start_anomaly_service.sh`

**Changed**:
```bash
# Before
echo "Service will run on: http://localhost:8001"

# After
echo "Service will run on: http://localhost:8002"
```

## Files Modified

1. ✅ `ml-service/ml_anomaly_service.py` - Port changed to 8002
2. ✅ `backend/src/main/resources/application.properties` - URL updated
3. ✅ `backend/src/main/java/com/expenseanalyzer/service/MLAnomalyClient.java` - Default port updated
4. ✅ `ml-service/test_anomaly_service.py` - Test URL updated
5. ✅ `ml-service/start_anomaly_service.bat` - Port message updated
6. ✅ `ml-service/start_anomaly_service.sh` - Port message updated

## Files NOT Modified (As Required)

- ✅ ML Prediction Service (still on port 8001)
- ✅ ML models unchanged
- ✅ Frontend UI unchanged
- ✅ Prediction logic unchanged

## Verification

### Backend Compilation
```
[INFO] BUILD SUCCESS
[INFO] Total time:  9.084 s
```

### Service URLs

| Service | URL | Status |
|---------|-----|--------|
| Backend | http://localhost:8080 | ✅ |
| ML Prediction | http://localhost:8001 | ✅ |
| ML Anomaly | http://localhost:8002 | ✅ NEW |
| Frontend | http://localhost:3000 | ✅ |

## How to Run Both Services

### Terminal 1: ML Prediction Service
```bash
cd ml-service
python ml_prediction_service.py
```
Output: `Listening on: http://localhost:8001`

### Terminal 2: ML Anomaly Service
```bash
cd ml-service
python ml_anomaly_service.py
```
Output: `Listening on: http://localhost:8002`

### Terminal 3: Backend
```bash
cd backend
mvn spring-boot:run
```
Output: `Started on port 8080`

### Terminal 4: Frontend
```bash
cd frontend
npm start
```
Output: `Running on port 3000`

## Testing

### Test ML Prediction Service (Port 8001)
```bash
curl http://localhost:8001/health
```

### Test ML Anomaly Service (Port 8002)
```bash
curl http://localhost:8002/health
```

### Test Backend Integration
```bash
# Add an expense - should call anomaly service on port 8002
curl -X POST http://localhost:8080/api/expense/add \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "category": "Food", "date": "2026-03-08"}'
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                          │
│                  (Port 3000)                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│              Spring Boot Backend                     │
│                  (Port 8080)                         │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  ExpenseService                              │  │
│  │       ↓                                      │  │
│  │  MLAnomalyClient                             │  │
│  │       ↓                                      │  │
│  │  Calls: http://localhost:8002/ml/detect-... │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  PredictionController                        │  │
│  │       ↓                                      │  │
│  │  MLPredictionClient                          │  │
│  │       ↓                                      │  │
│  │  Calls: http://localhost:8001/ml/predict    │  │
│  └──────────────────────────────────────────────┘  │
└─────────────┬──────────────────┬───────────────────┘
              │                  │
              ↓                  ↓
┌──────────────────────┐  ┌──────────────────────┐
│  ML Anomaly Service  │  │  ML Prediction Svc   │
│    (Port 8002)       │  │    (Port 8001)       │
│                      │  │                      │
│  /ml/detect-anomaly  │  │  /ml/predict         │
│  /ml/anomaly-info    │  │  /ml/predict-info    │
│  /health             │  │  /health             │
└──────────────────────┘  └──────────────────────┘
```

## Benefits

1. **No Port Conflicts**: Both ML services can run simultaneously
2. **Clear Separation**: Each service has its own dedicated port
3. **Easy Debugging**: Can test each service independently
4. **Scalability**: Services can be deployed separately if needed
5. **Maintainability**: Clear port allocation makes troubleshooting easier

## Configuration Summary

### application.properties
```properties
# Backend
server.port=8080

# ML Services
ml.service.url=http://localhost:8000          # Legacy (not used)
ml.prediction.service.url=http://localhost:8001
ml.anomaly.service.url=http://localhost:8002
```

### Service Startup Commands

```bash
# ML Prediction (Port 8001)
python ml_prediction_service.py

# ML Anomaly (Port 8002)
python ml_anomaly_service.py

# Or use quick start
./start_anomaly_service.sh  # Starts on port 8002
```

## Troubleshooting

### Port Already in Use

If you see:
```
OSError: [Errno 98] Address already in use
```

**Solution**:
1. Check what's running on the port:
   ```bash
   # Windows
   netstat -ano | findstr :8002
   
   # Linux/Mac
   lsof -i :8002
   ```

2. Kill the process or use a different port

### Service Not Reachable

**Check**:
1. Is service running? `curl http://localhost:8002/health`
2. Correct port in application.properties?
3. Firewall blocking the port?

### Backend Can't Connect to ML Service

**Check**:
1. ML service is running on port 8002
2. application.properties has correct URL
3. Backend logs show correct URL being called

## Status: FIXED ✅

All port conflicts resolved:
- ✅ ML Prediction Service: Port 8001
- ✅ ML Anomaly Service: Port 8002
- ✅ Backend compiles successfully
- ✅ No conflicts
- ✅ Both services can run together

## Next Steps

1. **Start ML Prediction Service**:
   ```bash
   cd ml-service
   python ml_prediction_service.py
   ```

2. **Start ML Anomaly Service**:
   ```bash
   cd ml-service
   python ml_anomaly_service.py
   ```

3. **Start Backend**:
   ```bash
   cd backend
   mvn spring-boot:run
   ```

4. **Start Frontend**:
   ```bash
   cd frontend
   npm start
   ```

All services will now run without conflicts! 🎉

package com.expenseanalyzer.controller;

import com.expenseanalyzer.model.Prediction;
import com.expenseanalyzer.service.PredictionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/prediction")
public class PredictionController {
    
    private static final Logger logger = LoggerFactory.getLogger(PredictionController.class);
    
    @Autowired
    private PredictionService predictionService;
    
    @Autowired
    private com.expenseanalyzer.service.MLPredictionClient mlPredictionClient;
    
    @GetMapping("/next-month")
    public ResponseEntity<?> getNextMonthPrediction(Authentication authentication) {
        try {
            if (authentication == null || authentication.getPrincipal() == null) {
                logger.error("Authentication is null or principal is null");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(createErrorResponse("User not authenticated"));
            }
            
            Long userId = (Long) authentication.getPrincipal();
            logger.info("=== Controller: Generating prediction for user ID: {} ===", userId);
            
            Map<String, Object> prediction = predictionService.predictNextMonth(userId);
            
            logger.info("=== Controller: Prediction generated successfully ===");
            logger.info("Total Predicted Expense: {}", prediction.get("totalPredictedExpense"));
            logger.info("Category Predictions Count: {}", 
                prediction.get("categoryPredictions") != null ? 
                ((java.util.List<?>) prediction.get("categoryPredictions")).size() : 0);
            
            return ResponseEntity.ok(prediction);
            
        } catch (Exception e) {
            logger.error("=== Controller: EXCEPTION in prediction generation ===");
            logger.error("Exception type: {}", e.getClass().getName());
            logger.error("Exception message: {}", e.getMessage());
            logger.error("Stack trace:", e);
            
            // Return error response but don't hide the real error
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", "Prediction generation failed: " + e.getMessage());
            errorResponse.put("totalPredictedExpense", 0.0);
            errorResponse.put("predictedExpense", 0.0);
            errorResponse.put("categoryPredictions", new java.util.ArrayList<>());
            errorResponse.put("overspendingRiskPercentage", 0);
            errorResponse.put("savingsPrediction", 0.0);
            errorResponse.put("insight", "Unable to generate prediction. Error: " + e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
    
    @GetMapping("/latest")
    public ResponseEntity<?> getLatestPrediction(Authentication authentication) {
        try {
            if (authentication == null || authentication.getPrincipal() == null) {
                logger.error("Authentication is null or principal is null");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(createErrorResponse("User not authenticated"));
            }
            
            Long userId = (Long) authentication.getPrincipal();
            logger.info("Fetching latest prediction for user ID: {}", userId);
            
            Prediction prediction = predictionService.getLatestPrediction(userId);
            
            if (prediction == null) {
                logger.info("No prediction found for user {}", userId);
                return ResponseEntity.ok(createDefaultPrediction("No predictions available yet"));
            }
            
            return ResponseEntity.ok(prediction);
            
        } catch (Exception e) {
            logger.error("Error fetching latest prediction: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.OK)
                .body(createDefaultPrediction(e.getMessage()));
        }
    }
    
    private Map<String, Object> createErrorResponse(String message) {
        Map<String, Object> response = new HashMap<>();
        response.put("error", message);
        return response;
    }
    
    private Map<String, Object> createDefaultPrediction(String message) {
        Map<String, Object> response = new HashMap<>();
        response.put("totalPredictedExpense", 0.0);
        response.put("predictedExpense", 0.0);
        response.put("categoryPredictions", new java.util.ArrayList<>());
        response.put("overspendingRiskPercentage", 0);
        response.put("savingsPrediction", 0.0);
        response.put("insight", "Start tracking your expenses to get personalized predictions.");
        response.put("message", message);
        return response;
    }
    
    /**
     * ML-based prediction endpoint
     * Uses trained ML model for more accurate predictions
     */
    @GetMapping("/ml-next-month")
    public ResponseEntity<?> getMLNextMonthPrediction(Authentication authentication) {
        try {
            if (authentication == null || authentication.getPrincipal() == null) {
                logger.error("Authentication is null or principal is null");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(createErrorResponse("User not authenticated"));
            }
            
            Long userId = (Long) authentication.getPrincipal();
            logger.info("=== ML Prediction: Generating ML-based prediction for user ID: {} ===", userId);
            
            // Check if ML service is available
            if (!mlPredictionClient.isMLServiceAvailable()) {
                logger.warn("ML service is not available, returning error");
                Map<String, Object> errorResponse = createDefaultPrediction("ML service is not available");
                errorResponse.put("ml_service_available", false);
                return ResponseEntity.ok(errorResponse);
            }
            
            // Get ML prediction
            Map<String, Object> mlPrediction = mlPredictionClient.getMLPrediction(userId);
            
            if (mlPrediction.get("success") == Boolean.TRUE) {
                logger.info("=== ML Prediction: Success ===");
                logger.info("Total Predicted Expense: {}", mlPrediction.get("total_predicted_expense"));
                logger.info("Prediction Confidence: {}", mlPrediction.get("prediction_confidence"));
                
                mlPrediction.put("ml_service_available", true);
                return ResponseEntity.ok(mlPrediction);
            } else {
                logger.warn("ML prediction failed: {}", mlPrediction.get("error"));
                mlPrediction.put("ml_service_available", true);
                return ResponseEntity.ok(mlPrediction);
            }
            
        } catch (Exception e) {
            logger.error("=== ML Prediction: EXCEPTION ===");
            logger.error("Exception message: {}", e.getMessage());
            logger.error("Stack trace:", e);
            
            Map<String, Object> errorResponse = createDefaultPrediction("ML prediction failed: " + e.getMessage());
            errorResponse.put("ml_service_available", false);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
    
    /**
     * Get ML service status and information
     */
    @GetMapping("/ml-service-info")
    public ResponseEntity<?> getMLServiceInfo() {
        try {
            Map<String, Object> info = mlPredictionClient.getMLServiceInfo();
            info.put("available", mlPredictionClient.isMLServiceAvailable());
            return ResponseEntity.ok(info);
        } catch (Exception e) {
            logger.error("Error getting ML service info: {}", e.getMessage());
            Map<String, Object> errorInfo = new HashMap<>();
            errorInfo.put("available", false);
            errorInfo.put("error", e.getMessage());
            return ResponseEntity.ok(errorInfo);
        }
    }
}

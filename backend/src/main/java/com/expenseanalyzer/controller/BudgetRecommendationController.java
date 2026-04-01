package com.expenseanalyzer.controller;

import com.expenseanalyzer.service.MLBudgetRecommendationClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/ml")
@CrossOrigin(origins = "*")
public class BudgetRecommendationController {
    
    @Autowired
    private MLBudgetRecommendationClient mlBudgetClient;
    
    /**
     * Get ML-based budget recommendations for the authenticated user
     * 
     * @param authentication Spring Security authentication
     * @return Budget recommendations from ML service
     */
    @GetMapping("/budget-recommendation")
    public ResponseEntity<?> getBudgetRecommendations(Authentication authentication) {
        try {
            // Get user ID from authentication
            Long userId = Long.parseLong(authentication.getName());
            
            // Call ML service
            Map<String, Object> recommendations = mlBudgetClient.getBudgetRecommendations(userId);
            
            return ResponseEntity.ok(recommendations);
            
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "success", false,
                    "error", "Failed to get budget recommendations: " + e.getMessage()
                ));
        }
    }
    
    /**
     * Get ML budget model information
     * 
     * @return Model metadata
     */
    @GetMapping("/budget-model-info")
    public ResponseEntity<?> getModelInfo() {
        try {
            Map<String, Object> modelInfo = mlBudgetClient.getModelInfo();
            return ResponseEntity.ok(modelInfo);
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                .body(Map.of("error", "Failed to get model info: " + e.getMessage()));
        }
    }
    
    /**
     * Check if ML budget service is available
     * 
     * @return Service availability status
     */
    @GetMapping("/budget-service-status")
    public ResponseEntity<?> getServiceStatus() {
        boolean available = mlBudgetClient.isServiceAvailable();
        return ResponseEntity.ok(Map.of(
            "available", available,
            "service", "ML Budget Recommendation"
        ));
    }
}

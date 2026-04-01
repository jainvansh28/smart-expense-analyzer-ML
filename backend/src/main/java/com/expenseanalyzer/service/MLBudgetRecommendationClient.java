package com.expenseanalyzer.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;

@Service
public class MLBudgetRecommendationClient {
    
    private static final Logger logger = LoggerFactory.getLogger(MLBudgetRecommendationClient.class);
    
    @Value("${ml.budget.service.url:http://localhost:8003}")
    private String mlServiceUrl;
    
    private final RestTemplate restTemplate;
    
    public MLBudgetRecommendationClient() {
        this.restTemplate = new RestTemplate();
        this.restTemplate.getInterceptors().add((request, body, execution) -> {
            request.getHeaders().setContentType(MediaType.APPLICATION_JSON);
            return execution.execute(request, body);
        });
    }
    
    /**
     * Get ML-based budget recommendations for a user
     * 
     * @param userId User ID
     * @return Map containing budget recommendations
     */
    public Map<String, Object> getBudgetRecommendations(Long userId) {
        logger.info("=== ML Budget Recommendation API Call ===");
        logger.info("Calling ML service at: {}/ml/budget-recommendation", mlServiceUrl);
        logger.info("User ID: {}", userId);
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            // Prepare request body
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("user_id", userId);
            
            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            // Call ML service
            String url = mlServiceUrl + "/ml/budget-recommendation";
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> responseBody = response.getBody();
                
                result.put("success", responseBody.get("success"));
                result.put("userId", responseBody.get("user_id"));
                result.put("recommendedBudgets", responseBody.get("recommended_budgets"));
                result.put("totalRecommended", responseBody.get("total_recommended"));
                result.put("monthlyIncome", responseBody.get("monthly_income"));
                result.put("modelConfidence", responseBody.get("model_confidence"));
                result.put("insight", responseBody.get("insight"));
                result.put("mlServiceAvailable", true);
                
                logger.info("ML Budget Recommendations Retrieved Successfully");
                logger.info("Categories: {}", 
                    responseBody.get("recommended_budgets") != null ? 
                    ((java.util.List) responseBody.get("recommended_budgets")).size() : 0);
                logger.info("Total Recommended: {}", responseBody.get("total_recommended"));
                logger.info("Confidence: {}", responseBody.get("model_confidence"));
                
            } else {
                logger.warn("ML service returned non-success status: {}", response.getStatusCode());
                result.put("success", false);
                result.put("mlServiceAvailable", false);
                result.put("error", "ML service unavailable");
            }
            
        } catch (org.springframework.web.client.ResourceAccessException e) {
            logger.error("ML budget service connection failed: {}", e.getMessage());
            logger.info("ML budget service appears to be down.");
            result.put("success", false);
            result.put("mlServiceAvailable", false);
            result.put("error", "ML service not reachable");
            
        } catch (org.springframework.web.client.HttpClientErrorException e) {
            logger.error("ML budget service returned error: {} - {}", e.getStatusCode(), e.getMessage());
            result.put("success", false);
            result.put("mlServiceAvailable", true);
            result.put("error", e.getMessage());
            
        } catch (Exception e) {
            logger.error("Error calling ML budget recommendation service: {}", e.getMessage(), e);
            result.put("success", false);
            result.put("mlServiceAvailable", false);
            result.put("error", e.getMessage());
        }
        
        logger.info("=== ML Budget Recommendation Completed ===");
        return result;
    }
    
    /**
     * Check if ML budget service is available
     * 
     * @return true if service is reachable
     */
    public boolean isServiceAvailable() {
        try {
            String url = mlServiceUrl + "/health";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            logger.debug("ML budget service health check failed: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * Get ML model information
     * 
     * @return Map containing model metadata
     */
    public Map<String, Object> getModelInfo() {
        try {
            String url = mlServiceUrl + "/ml/budget-info";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                return response.getBody();
            }
        } catch (Exception e) {
            logger.error("Error fetching ML budget model info: {}", e.getMessage());
        }
        
        return new HashMap<>();
    }
}

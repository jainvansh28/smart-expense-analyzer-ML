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

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

@Service
public class MLAnomalyClient {
    
    private static final Logger logger = LoggerFactory.getLogger(MLAnomalyClient.class);
    
    @Value("${ml.anomaly.service.url:http://localhost:8002}")
    private String mlServiceUrl;
    
    private final RestTemplate restTemplate;
    
    public MLAnomalyClient() {
        this.restTemplate = new RestTemplate();
        // Set timeouts
        this.restTemplate.getInterceptors().add((request, body, execution) -> {
            request.getHeaders().setContentType(MediaType.APPLICATION_JSON);
            return execution.execute(request, body);
        });
    }
    
    /**
     * Detect anomaly using ML service
     * 
     * @param userId User ID
     * @param amount Expense amount
     * @param category Expense category
     * @param date Expense date
     * @return Map containing anomaly detection results
     */
    public Map<String, Object> detectAnomaly(Long userId, BigDecimal amount, String category, LocalDate date) {
        logger.info("=== ML Anomaly Detection API Call ===");
        logger.info("Calling ML service at: {}/ml/detect-anomaly", mlServiceUrl);
        logger.info("User ID: {}, Category: {}, Amount: ₹{}, Date: {}", userId, category, amount, date);
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            // Prepare request body
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("user_id", userId);
            requestBody.put("amount", amount.doubleValue());
            requestBody.put("category", category);
            requestBody.put("date", date.toString());
            
            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            // Call ML service
            String url = mlServiceUrl + "/ml/detect-anomaly";
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> responseBody = response.getBody();
                
                Boolean isAnomaly = (Boolean) responseBody.get("is_anomaly");
                String anomalyMessage = (String) responseBody.get("anomaly_message");
                String confidence = (String) responseBody.get("confidence");
                Object anomalyScoreObj = responseBody.get("anomaly_score");
                Map<String, Object> details = (Map<String, Object>) responseBody.get("details");
                
                result.put("isAnomaly", isAnomaly != null ? isAnomaly : false);
                result.put("anomalyMessage", anomalyMessage);
                result.put("confidence", confidence);
                result.put("anomalyScore", anomalyScoreObj);
                result.put("mlDetection", true);
                
                if (details != null) {
                    result.put("averageAmount", details.get("avg_amount"));
                    result.put("deviation", details.get("deviation"));
                    result.put("pctOfMonthly", details.get("pct_of_monthly"));
                }
                
                logger.info("ML Detection Result: {} (Confidence: {})", 
                    isAnomaly ? "ANOMALY" : "NORMAL", confidence);
                logger.info("Anomaly Score: {}", anomalyScoreObj);
                
                if (isAnomaly) {
                    logger.warn("ANOMALY DETECTED: {}", anomalyMessage);
                }
                
            } else {
                logger.warn("ML service returned non-success status: {}", response.getStatusCode());
                result.put("isAnomaly", false);
                result.put("mlDetection", false);
                result.put("error", "ML service unavailable");
            }
            
        } catch (org.springframework.web.client.ResourceAccessException e) {
            logger.error("ML service connection failed: {}", e.getMessage());
            logger.info("ML service appears to be down. Will use fallback detection.");
            result.put("isAnomaly", false);
            result.put("mlDetection", false);
            result.put("error", "ML service not reachable");
            
        } catch (Exception e) {
            logger.error("Error calling ML anomaly service: {}", e.getMessage(), e);
            result.put("isAnomaly", false);
            result.put("mlDetection", false);
            result.put("error", e.getMessage());
        }
        
        logger.info("=== ML Anomaly Detection Completed ===");
        return result;
    }
    
    /**
     * Check if ML anomaly service is available
     * 
     * @return true if service is reachable
     */
    public boolean isServiceAvailable() {
        try {
            String url = mlServiceUrl + "/health";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            logger.debug("ML anomaly service health check failed: {}", e.getMessage());
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
            String url = mlServiceUrl + "/ml/anomaly-info";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                return response.getBody();
            }
        } catch (Exception e) {
            logger.error("Error fetching ML model info: {}", e.getMessage());
        }
        
        return new HashMap<>();
    }
}

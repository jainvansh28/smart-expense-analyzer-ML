package com.expenseanalyzer.service;

import com.expenseanalyzer.model.Expense;
import com.expenseanalyzer.model.Income;
import com.expenseanalyzer.repository.ExpenseRepository;
import com.expenseanalyzer.repository.IncomeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class MLPredictionClient {
    
    private static final Logger logger = LoggerFactory.getLogger(MLPredictionClient.class);
    
    @Value("${ml.prediction.service.url:http://localhost:8001}")
    private String mlPredictionServiceUrl;
    
    @Autowired
    private ExpenseRepository expenseRepository;
    
    @Autowired
    private IncomeRepository incomeRepository;
    
    private final RestTemplate restTemplate;
    
    public MLPredictionClient(RestTemplateBuilder restTemplateBuilder) {
        this.restTemplate = restTemplateBuilder
                .setConnectTimeout(Duration.ofSeconds(5))
                .setReadTimeout(Duration.ofSeconds(10))
                .build();
    }
    
    /**
     * Get ML-based prediction for next month
     * Calls the ML service at http://localhost:8001/ml/predict
     */
    public Map<String, Object> getMLPrediction(Long userId) {
        logger.info("Fetching ML prediction for user: {}", userId);
        
        try {
            // Fetch user's expense history
            List<Expense> expenses = expenseRepository.findByUserIdOrderByDateDesc(userId);
            
            if (expenses.isEmpty()) {
                logger.warn("No expense data available for user: {}", userId);
                return createEmptyPrediction(userId, "No expense data available");
            }
            
            // Fetch user's income history
            List<Income> incomes = incomeRepository.findByUserIdOrderByDateDesc(userId);
            logger.info("=== INCOME DATA DEBUG for user {} ===", userId);
            logger.info("Found {} income records for user: {}", incomes.size(), userId);
            
            // Log income details for debugging
            for (Income income : incomes) {
                logger.info("Income: Date={}, Amount=₹{}, Type={}", 
                    income.getDate(), income.getAmount(), income.getType());
            }
            
            // Prepare request body
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("user_id", userId);
            requestBody.put("expenses", expenses.stream()
                    .map(e -> {
                        Map<String, Object> expenseMap = new HashMap<>();
                        expenseMap.put("amount", e.getAmount().doubleValue());
                        expenseMap.put("category", e.getCategory());
                        expenseMap.put("date", e.getDate().toString());
                        return expenseMap;
                    })
                    .collect(Collectors.toList()));
            
            // Add income data to request
            List<Map<String, Object>> incomeData = incomes.stream()
                    .map(i -> {
                        Map<String, Object> incomeMap = new HashMap<>();
                        incomeMap.put("amount", i.getAmount().doubleValue());
                        incomeMap.put("category", i.getType()); // Use getType() method
                        incomeMap.put("date", i.getDate().toString());
                        return incomeMap;
                    })
                    .collect(Collectors.toList());
            
            requestBody.put("incomes", incomeData);
            logger.info("Sending {} income records to ML service", incomeData.size());
            
            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            // Call ML service
            String url = mlPredictionServiceUrl + "/ml/predict";
            logger.info("Calling ML service at: {}", url);
            
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> mlResponse = response.getBody();
                logger.info("=== ML PREDICTION RESPONSE DEBUG ===");
                logger.info("ML prediction successful for user: {}", userId);
                logger.info("Predicted amount: ₹{}", mlResponse.get("total_predicted_expense"));
                logger.info("Average monthly income: ₹{}", mlResponse.get("avg_monthly_income"));
                logger.info("Income months analyzed: {}", mlResponse.get("income_months_analyzed"));
                logger.info("Predicted savings: ₹{}", mlResponse.get("predicted_savings"));
                
                // Add success flag
                mlResponse.put("success", true);
                mlResponse.put("source", "ml_service");
                
                return mlResponse;
            } else {
                logger.error("ML service returned non-success status: {}", response.getStatusCode());
                return createEmptyPrediction(userId, "ML service returned error");
            }
            
        } catch (RestClientException e) {
            logger.error("Failed to connect to ML service: {}", e.getMessage());
            return createEmptyPrediction(userId, "ML service unavailable: " + e.getMessage());
        } catch (Exception e) {
            logger.error("Error getting ML prediction: {}", e.getMessage(), e);
            return createEmptyPrediction(userId, "Prediction failed: " + e.getMessage());
        }
    }
    
    /**
     * Check if ML service is available
     */
    public boolean isMLServiceAvailable() {
        try {
            String url = mlPredictionServiceUrl + "/health";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            logger.warn("ML service health check failed: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * Get ML service information
     */
    public Map<String, Object> getMLServiceInfo() {
        try {
            String url = mlPredictionServiceUrl + "/model/info";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                return response.getBody();
            }
        } catch (Exception e) {
            logger.error("Failed to get ML service info: {}", e.getMessage());
        }
        
        Map<String, Object> errorInfo = new HashMap<>();
        errorInfo.put("status", "unavailable");
        errorInfo.put("message", "ML service not accessible");
        return errorInfo;
    }
    
    /**
     * Create empty prediction response when ML service fails
     */
    private Map<String, Object> createEmptyPrediction(Long userId, String errorMessage) {
        Map<String, Object> emptyPrediction = new HashMap<>();
        emptyPrediction.put("success", false);
        emptyPrediction.put("user_id", userId);
        emptyPrediction.put("total_predicted_expense", 0.0);
        emptyPrediction.put("category_predictions", List.of());
        emptyPrediction.put("prediction_confidence", "None");
        emptyPrediction.put("error", errorMessage);
        emptyPrediction.put("source", "ml_service");
        // Add null values for income-related fields to indicate unavailable
        emptyPrediction.put("avg_monthly_income", null);
        emptyPrediction.put("predicted_savings", null);
        emptyPrediction.put("income_months_analyzed", null);
        return emptyPrediction;
    }
}

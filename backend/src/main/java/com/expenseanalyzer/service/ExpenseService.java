package com.expenseanalyzer.service;

import com.expenseanalyzer.dto.ExpenseRequest;
import com.expenseanalyzer.model.Expense;
import com.expenseanalyzer.repository.ExpenseRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class ExpenseService {
    
    private static final Logger logger = LoggerFactory.getLogger(ExpenseService.class);
    
    @Autowired
    private ExpenseRepository expenseRepository;
    
    @Autowired
    private AnomalyDetectionService anomalyDetectionService;
    
    @Autowired
    private MLAnomalyClient mlAnomalyClient;
    
    @Transactional
    public Map<String, Object> addExpense(Long userId, ExpenseRequest request) {
        // Create and save expense
        Expense expense = new Expense();
        expense.setUserId(userId);
        expense.setAmount(request.getAmount());
        expense.setCategory(request.getCategory());
        expense.setDescription(request.getDescription());
        expense.setDate(request.getDate());
        
        // Try ML-based anomaly detection first
        Map<String, Object> anomalyResult = mlAnomalyClient.detectAnomaly(
            userId,
            request.getAmount(),
            request.getCategory(),
            request.getDate()
        );
        
        // Check if ML detection was successful
        Boolean mlDetection = (Boolean) anomalyResult.get("mlDetection");
        
        // If ML service failed or unavailable, fall back to rule-based detection
        if (mlDetection == null || !mlDetection) {
            logger.info("ML anomaly detection unavailable. Using rule-based fallback.");
            anomalyResult = anomalyDetectionService.detectAnomaly(
                userId, 
                request.getCategory(), 
                request.getAmount()
            );
            anomalyResult.put("detectionMethod", "rule-based");
        } else {
            anomalyResult.put("detectionMethod", "ml-based");
        }
        
        // Set anomaly fields on expense
        Boolean isAnomaly = (Boolean) anomalyResult.get("isAnomaly");
        expense.setIsAnomaly(isAnomaly != null ? isAnomaly : false);
        
        if (isAnomaly != null && isAnomaly) {
            String message = (String) anomalyResult.get("anomalyMessage");
            // Shorten message for database storage
            if (message != null && message.length() > 255) {
                message = message.substring(0, 252) + "...";
            }
            expense.setAnomalyMessage(message);
        }
        
        Expense savedExpense = expenseRepository.save(expense);
        
        // Build response
        Map<String, Object> response = new HashMap<>();
        response.put("expense", savedExpense);
        response.put("isAnomaly", anomalyResult.get("isAnomaly"));
        response.put("anomalyMessage", anomalyResult.get("anomalyMessage"));
        response.put("detectionMethod", anomalyResult.get("detectionMethod"));
        
        // Include ML-specific fields if available
        if (anomalyResult.containsKey("confidence")) {
            response.put("confidence", anomalyResult.get("confidence"));
            response.put("anomalyScore", anomalyResult.get("anomalyScore"));
        }
        
        // Include rule-based fields if available
        if (anomalyResult.containsKey("averageAmount")) {
            response.put("averageAmount", anomalyResult.get("averageAmount"));
            response.put("currentAmount", anomalyResult.get("currentAmount"));
            response.put("multiplier", anomalyResult.get("multiplier"));
        }
        
        return response;
    }
    
    @Transactional
    public Expense updateExpense(Long expenseId, Long userId, ExpenseRequest request) {
        Expense expense = expenseRepository.findById(expenseId)
                .orElseThrow(() -> new RuntimeException("Expense not found"));
        
        if (!expense.getUserId().equals(userId)) {
            throw new RuntimeException("Unauthorized");
        }
        
        expense.setAmount(request.getAmount());
        expense.setCategory(request.getCategory());
        expense.setDescription(request.getDescription());
        expense.setDate(request.getDate());
        
        return expenseRepository.save(expense);
    }
    
    @Transactional
    public void deleteExpense(Long expenseId, Long userId) {
        Expense expense = expenseRepository.findById(expenseId)
                .orElseThrow(() -> new RuntimeException("Expense not found"));
        
        if (!expense.getUserId().equals(userId)) {
            throw new RuntimeException("Unauthorized");
        }
        
        expenseRepository.delete(expense);
    }
    
    public List<Expense> getUserExpenses(Long userId) {
        return expenseRepository.findByUserIdOrderByDateDesc(userId);
    }
    
    public Expense getExpenseById(Long expenseId, Long userId) {
        Expense expense = expenseRepository.findById(expenseId)
                .orElseThrow(() -> new RuntimeException("Expense not found"));
        
        if (!expense.getUserId().equals(userId)) {
            throw new RuntimeException("Unauthorized");
        }
        
        return expense;
    }
    
    public List<Expense> searchExpenses(Long userId, String query) {
        List<Expense> allExpenses = expenseRepository.findByUserIdOrderByDateDesc(userId);
        if (query == null || query.trim().isEmpty()) {
            return allExpenses;
        }
        
        String lowerQuery = query.toLowerCase();
        return allExpenses.stream()
                .filter(e -> (e.getDescription() != null && 
                            e.getDescription().toLowerCase().contains(lowerQuery)) ||
                            e.getCategory().toLowerCase().contains(lowerQuery))
                .collect(Collectors.toList());
    }
    
    public List<Expense> filterExpenses(Long userId, Integer year, Integer month, 
                                        String category, LocalDate startDate, LocalDate endDate) {
        List<Expense> expenses;
        
        if (year != null && month != null) {
            expenses = expenseRepository.findByUserIdAndYearAndMonth(userId, year, month);
        } else if (startDate != null && endDate != null) {
            expenses = expenseRepository.findByUserIdAndDateBetweenOrderByDateDesc(
                userId, startDate, endDate);
        } else {
            expenses = expenseRepository.findByUserIdOrderByDateDesc(userId);
        }
        
        if (category != null && !category.isEmpty() && !category.equals("all")) {
            expenses = expenses.stream()
                    .filter(e -> e.getCategory().equals(category))
                    .collect(Collectors.toList());
        }
        
        return expenses;
    }
    
    @Transactional
    public Expense removeAnomaly(Long expenseId, Long userId) {
        Expense expense = expenseRepository.findById(expenseId)
                .orElseThrow(() -> new RuntimeException("Expense not found"));
        
        if (!expense.getUserId().equals(userId)) {
            throw new RuntimeException("Unauthorized");
        }
        
        expense.setIsAnomaly(false);
        expense.setAnomalyMessage(null);
        
        return expenseRepository.save(expense);
    }
}

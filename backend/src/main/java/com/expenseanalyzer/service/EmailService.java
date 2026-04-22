package com.expenseanalyzer.service;

import org.springframework.stereotype.Service;

/**
 * Email service stub — mail dependency removed in demo mode.
 * Kept so any legacy references compile without changes.
 */
@Service
public class EmailService {

    public void sendOtpEmail(String to, String otp) {
        // No-op: email sending is disabled in demo mode
    }
}

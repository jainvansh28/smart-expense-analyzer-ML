package com.expenseanalyzer.service;

import org.springframework.stereotype.Service;

/**
 * Email service stub — OTP/email verification is disabled in demo mode.
 * Kept to avoid breaking any remaining references at compile time.
 */
@Service
public class EmailService {
    
    public void sendOtpEmail(String to, String otp) {
        // No-op: email verification is disabled
        System.out.println("[Demo Mode] Email sending disabled. OTP for " + to + ": " + otp);
    }
}

package com.expenseanalyzer.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

@Service
public class EmailService {

    @Autowired
    private JavaMailSender mailSender;

    public void sendOtpEmail(String to, String otp) {
        try {
            SimpleMailMessage message = new SimpleMailMessage();
            message.setTo(to);
            message.setSubject("Smart Expense Analyzer – Email Verification OTP");
            message.setText(
                "Hello,\n\n" +
                "Your OTP for email verification is: " + otp + "\n\n" +
                "This OTP is valid for 5 minutes.\n\n" +
                "If you did not request this, please ignore this email.\n\n" +
                "– Smart Expense Analyzer Team"
            );
            mailSender.send(message);
            System.out.println("[EmailService] OTP sent to: " + to);
        } catch (Exception e) {
            System.err.println("[EmailService] Failed to send email to " + to + ": " + e.getMessage());
            // Re-throw so the controller can return a meaningful error
            throw new RuntimeException("Failed to send OTP email. Check SMTP configuration.");
        }
    }
}

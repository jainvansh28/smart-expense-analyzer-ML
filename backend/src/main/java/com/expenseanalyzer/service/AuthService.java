package com.expenseanalyzer.service;

import com.expenseanalyzer.dto.AuthResponse;
import com.expenseanalyzer.dto.LoginRequest;
import com.expenseanalyzer.dto.SignupRequest;
import com.expenseanalyzer.model.User;
import com.expenseanalyzer.repository.UserRepository;
import com.expenseanalyzer.security.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Random;

@Service
public class AuthService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private EmailService emailService;

    // ── Signup: save unverified user, generate OTP, send email ───────────────
    @Transactional
    public String signup(SignupRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            // If already registered but not verified, resend OTP
            User existing = userRepository.findByEmail(request.getEmail())
                    .orElseThrow(() -> new RuntimeException("Email already registered"));
            if (Boolean.TRUE.equals(existing.getIsVerified())) {
                throw new RuntimeException("Email already registered");
            }
            // Resend OTP for unverified account
            return generateAndSendOtp(existing);
        }

        User user = new User();
        user.setName(request.getName());
        user.setEmail(request.getEmail());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setIsVerified(false);

        user = userRepository.save(user);
        return generateAndSendOtp(user);
    }

    // ── Verify OTP ────────────────────────────────────────────────────────────
    @Transactional
    public AuthResponse verifyOtp(String email, String otp) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found"));

        if (user.getOtpCode() == null || !user.getOtpCode().equals(otp)) {
            throw new RuntimeException("Invalid OTP");
        }
        if (user.getOtpExpiry() == null || user.getOtpExpiry().isBefore(LocalDateTime.now())) {
            throw new RuntimeException("OTP has expired. Please sign up again to get a new OTP.");
        }

        // Mark verified and clear OTP fields
        user.setIsVerified(true);
        user.setOtpCode(null);
        user.setOtpExpiry(null);
        userRepository.save(user);

        String token = jwtUtil.generateToken(user.getEmail(), user.getId());
        return new AuthResponse(token, user.getId(), user.getName(), user.getEmail(),
                user.getCreatedAt(), user.getEmailNotifications(), user.getShowSensitiveInfo());
    }

    // ── Login: only verified users ────────────────────────────────────────────
    public AuthResponse login(LoginRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("Invalid credentials"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new RuntimeException("Invalid credentials");
        }
        if (!Boolean.TRUE.equals(user.getIsVerified())) {
            throw new RuntimeException("Please verify your email with the OTP before logging in.");
        }

        String token = jwtUtil.generateToken(user.getEmail(), user.getId());
        return new AuthResponse(token, user.getId(), user.getName(), user.getEmail(),
                user.getCreatedAt(), user.getEmailNotifications(), user.getShowSensitiveInfo());
    }

    // ── Helpers ───────────────────────────────────────────────────────────────
    private String generateAndSendOtp(User user) {
        String otp = String.valueOf(100000 + new Random().nextInt(900000));
        user.setOtpCode(otp);
        user.setOtpExpiry(LocalDateTime.now().plusMinutes(5));
        userRepository.save(user);
        emailService.sendOtpEmail(user.getEmail(), otp);
        return "OTP sent to " + user.getEmail() + ". Please verify within 5 minutes.";
    }
}

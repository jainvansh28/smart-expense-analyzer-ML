import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Mail, Lock, User, ArrowLeft, UserPlus, Shield, CheckCircle } from 'lucide-react';
import AnimatedBackground from '../components/AnimatedBackground';

const SignupPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  // step 1 = signup form, step 2 = OTP input
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  // ── Step 1: submit signup form ──────────────────────────────────────────────
  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await authAPI.signup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });
      setInfo(res.data.message || 'OTP sent to your email.');
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // ── Step 2: verify OTP ──────────────────────────────────────────────────────
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await authAPI.verifyOtp(formData.email, otp);
      login(
        { id: res.data.id, name: res.data.name, email: res.data.email },
        res.data.token
      );
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'OTP verification failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen premium-bg relative flex items-center justify-center p-6">
      <AnimatedBackground />

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card p-8 w-full max-w-md relative z-10"
      >
        {/* Back button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => (step === 2 ? setStep(1) : navigate('/'))}
          className="text-white mb-6 flex items-center gap-2 hover:text-cyan-300 transition"
        >
          <ArrowLeft size={20} /> {step === 2 ? 'Back to Signup' : 'Back'}
        </motion.button>

        {/* Header */}
        <div className="text-center mb-6">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
            className="inline-block mb-4"
          >
            {step === 1
              ? <UserPlus className="text-purple-400" size={48} />
              : <Shield className="text-cyan-400" size={48} />
            }
          </motion.div>
          <h2 className="text-4xl font-bold text-white mb-2">
            {step === 1 ? 'Create Account' : 'Verify Email'}
          </h2>
          <p className="text-gray-400">
            {step === 1
              ? 'Join us to start tracking your expenses'
              : `Enter the 6-digit OTP sent to ${formData.email}`}
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex justify-center gap-2 mb-6">
          {[1, 2].map((s) => (
            <div
              key={s}
              className={`h-2 rounded-full transition-all duration-300 ${
                s === step
                  ? 'w-12 bg-gradient-to-r from-cyan-500 to-purple-500'
                  : s < step
                  ? 'w-8 bg-green-500'
                  : 'w-8 bg-white/20'
              }`}
            />
          ))}
        </div>

        {/* Info message */}
        {info && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-500/20 border border-green-500/50 text-green-300 text-sm flex items-center gap-2 px-4 py-2 rounded-lg mb-4"
          >
            <CheckCircle size={16} /> {info}
          </motion.div>
        )}

        {/* Error message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-red-500/20 border border-red-500 text-white p-3 rounded-lg mb-4"
          >
            {error}
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {/* ── Step 1: Signup form ── */}
          {step === 1 && (
            <motion.form
              key="signup"
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              onSubmit={handleSignup}
              className="space-y-5"
            >
              <div>
                <label className="text-white block mb-2 font-semibold">Name</label>
                <div className="flex items-center bg-white/10 rounded-lg p-3 input-animated border border-purple-500/30">
                  <User size={20} className="text-purple-400 mr-2" />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="bg-transparent text-white outline-none w-full placeholder-gray-400"
                    placeholder="John Doe"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="text-white block mb-2 font-semibold">Email</label>
                <div className="flex items-center bg-white/10 rounded-lg p-3 input-animated border border-purple-500/30">
                  <Mail size={20} className="text-cyan-400 mr-2" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="bg-transparent text-white outline-none w-full placeholder-gray-400"
                    placeholder="your@email.com"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="text-white block mb-2 font-semibold">Password</label>
                <div className="flex items-center bg-white/10 rounded-lg p-3 input-animated border border-purple-500/30">
                  <Lock size={20} className="text-pink-400 mr-2" />
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="bg-transparent text-white outline-none w-full placeholder-gray-400"
                    placeholder="••••••••"
                    required
                    minLength="6"
                  />
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading}
                className="w-full btn-premium py-4 text-lg ripple disabled:opacity-50"
              >
                {loading ? 'Sending OTP...' : 'Sign Up & Send OTP'}
              </motion.button>
            </motion.form>
          )}

          {/* ── Step 2: OTP verification ── */}
          {step === 2 && (
            <motion.form
              key="otp"
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              onSubmit={handleVerifyOtp}
              className="space-y-5"
            >
              <div>
                <label className="text-white block mb-2 font-semibold">6-Digit OTP</label>
                <div className="flex items-center bg-white/10 rounded-lg p-3 input-animated border border-cyan-500/30">
                  <Shield size={20} className="text-cyan-400 mr-2" />
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="bg-transparent text-white outline-none w-full text-center text-2xl tracking-widest placeholder-gray-400"
                    placeholder="000000"
                    maxLength="6"
                    required
                  />
                </div>
                <p className="text-gray-400 text-xs mt-2 text-center">
                  OTP expires in 5 minutes. Check your inbox (and spam folder).
                </p>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading || otp.length !== 6}
                className="w-full btn-premium py-4 text-lg ripple disabled:opacity-50"
              >
                {loading ? 'Verifying...' : 'Verify OTP'}
              </motion.button>

              <button
                type="button"
                onClick={handleSignup}
                disabled={loading}
                className="w-full text-gray-400 hover:text-cyan-300 text-sm transition py-2"
              >
                Didn't receive it? Resend OTP
              </button>
            </motion.form>
          )}
        </AnimatePresence>

        <p className="text-gray-400 text-center mt-6">
          Already have an account?{' '}
          <button
            onClick={() => navigate('/login')}
            className="text-cyan-400 hover:text-cyan-300 font-semibold transition"
          >
            Login
          </button>
        </p>
      </motion.div>
    </div>
  );
};

export default SignupPage;

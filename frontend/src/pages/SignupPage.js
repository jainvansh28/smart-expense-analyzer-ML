import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Mail, Lock, User, ArrowLeft, UserPlus } from 'lucide-react';
import AnimatedBackground from '../components/AnimatedBackground';

const SignupPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await authAPI.signup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });
      login(
        { id: response.data.id, name: response.data.name, email: response.data.email },
        response.data.token
      );
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed. Please try again.');
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
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => navigate('/')}
          className="text-white mb-6 flex items-center gap-2 hover:text-cyan-300 transition"
        >
          <ArrowLeft size={20} /> Back
        </motion.button>

        <div className="text-center mb-6">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
            className="inline-block mb-4"
          >
            <UserPlus className="text-purple-400" size={48} />
          </motion.div>
          <h2 className="text-4xl font-bold text-white mb-2">Create Account</h2>
          <p className="text-gray-400">Join us to start tracking your expenses</p>
        </div>

        {/* Demo mode banner */}
        <div className="bg-yellow-500/20 border border-yellow-500/50 text-yellow-300 text-sm text-center px-4 py-2 rounded-lg mb-6">
          ⚠️ Demo Mode: Email verification disabled
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-red-500/20 border border-red-500 text-white p-3 rounded-lg mb-4"
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSignup} className="space-y-5">
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
            {loading ? 'Creating Account...' : 'Sign Up'}
          </motion.button>
        </form>

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

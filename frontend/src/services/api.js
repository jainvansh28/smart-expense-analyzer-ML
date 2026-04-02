import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 🔐 Add token automatically
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ================= AUTH =================
export const authAPI = {
  sendOtp: (email) => api.post('/auth/send-otp', { email }),
  verifyOtp: (email, otp) => api.post('/auth/verify-otp', { email, otp }),
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
};

// ================= EXPENSE =================
export const expenseAPI = {
  add: (data) => api.post('/expense/add', data),
  update: (id, data) => api.put(`/expense/update/${id}`, data),
  delete: (id) => api.delete(`/expense/delete/${id}`),
  list: () => api.get('/expense/list'),
  getById: (id) => api.get(`/expense/${id}`),
  search: (query) => api.get(`/expense/search?q=${encodeURIComponent(query)}`),
  filter: (params) => api.get('/expense/filter', { params }),
  removeAnomaly: (id) => api.put(`/expense/${id}/remove-anomaly`),
};

// ================= BUDGET =================
export const budgetAPI = {
  set: (data) => api.post('/budgets', data),
  list: (month, year) => {
    const params = {};
    if (month) params.month = month;
    if (year) params.year = year;
    return api.get('/budgets', { params });
  },
  getCurrentMonth: () => api.get('/budgets/current-month'),
  delete: (id) => api.delete(`/budgets/${id}`),
};

// ================= PLANNED =================
export const plannedExpenseAPI = {
  add: (data) => api.post('/planned-expenses', data),
  list: () => api.get('/planned-expenses'),
  getUpcoming: () => api.get('/planned-expenses/upcoming'),
  markPaid: (id) => api.patch(`/planned-expenses/${id}/mark-paid`),
  update: (id, data) => api.put(`/planned-expenses/${id}`, data),
  delete: (id) => api.delete(`/planned-expenses/${id}`),
};

// ================= GOALS =================
export const goalsAPI = {
  add: (data) => api.post('/goals', data),
  list: () => api.get('/goals'),
  getActive: () => api.get('/goals/active'),
  addProgress: (id, amount) => api.patch(`/goals/${id}/add-progress`, { amount }),
  update: (id, data) => api.put(`/goals/${id}`, data),
  delete: (id) => api.delete(`/goals/${id}`),
};

// ================= ANALYTICS =================
export const analyticsAPI = {
  getMonthly: (year, month) => {
    const params = {};
    if (year) params.year = year;
    if (month) params.month = month;
    return api.get('/analytics/monthly', { params });
  },
};

// ================= PREDICTION =================
export const predictionAPI = {
  getNextMonth: () => api.get('/prediction/next-month'),
  getLatest: () => api.get('/prediction/latest'),
  getMLNextMonth: () => api.get('/prediction/ml-next-month'),
  getMLServiceInfo: () => api.get('/prediction/ml-service-info'),
};

// ================= AI =================
export const aiAPI = {
  getBudgetWarning: () => api.get('/ai/budget-warning'),
};

// ================= INSIGHTS =================
export const insightsAPI = {
  getAll: () => api.get('/insights/all'),
  getMonthlyComparison: () => api.get('/insights/monthly-comparison'),
  getBudgetAlerts: () => api.get('/insights/budget-alerts'),
  getSuggestions: () => api.get('/insights/suggestions'),
  getBillReminders: () => api.get('/insights/bill-reminders'),
  getTopExpenses: () => api.get('/insights/top-expenses'),
  getHealthScore: () => api.get('/insights/health-score'),
  getSavingStreak: () => api.get('/insights/saving-streak'),
  getSpendingHeatmap: () => api.get('/insights/spending-heatmap'),
};

// ================= ML =================
export const mlBudgetAPI = {
  getRecommendations: () => api.get('/ml/budget-recommendation'),
  getModelInfo: () => api.get('/ml/budget-model-info'),
  getServiceStatus: () => api.get('/ml/budget-service-status'),
};

// ================= INCOME =================
export const incomeAPI = {
  add: (data) => api.post('/income/add', data),
  update: (id, data) => api.put(`/income/update/${id}`, data),
  delete: (id) => api.delete(`/income/delete/${id}`),
  list: () => api.get('/income/list'),
  getBalance: (year, month) => {
    const params = {};
    if (year) params.year = year;
    if (month) params.month = month;
    return api.get('/income/balance', { params });
  },
};

// ================= USER =================
export const userAPI = {
  getProfile: () => api.get('/user/profile'),
  changePassword: (data) => api.post('/user/change-password', data),
  updatePrivacySettings: (settings) => api.put('/user/privacy-settings', settings),
  exportCsv: () => api.get('/user/export-csv', { responseType: 'blob' }),
};

export default api;

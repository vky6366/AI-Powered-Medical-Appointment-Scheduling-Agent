import api from './client';

// --- REAL ENDPOINTS ---

export const googleAuth = (token) => api.post('/auth/google', { token });
export const completeProfile = (data) => api.post('/auth/complete-profile', data);

export const getMyAppointments = () => {
  return api.get('/appointments/me');
};

export const cancelAppointment = (id) => {
  return api.patch(`/appointments/${id}/cancel`);
};

export const getDoctors = () => {
  return api.get('/doctors');
};

export const getAvailableSlots = (doctor, date, duration_min = 30, step_min = 30) => {
  return api.get('/appointments/available', { params: { doctor, date, duration_min, step_min } });
};

export const bookAppointment = (data) => {
  return api.post('/appointments/book', data);
};

export const sendChat = (message, thread_id = null, selected_slot_id = null) => {
  return api.post('/chat', { message, thread_id, selected_slot_id });
};

export const checkHealth = () => api.get('/health');

import api from './client';

// Check if we are running in Demo Mode (using bypass token)
const isDemoMode = () => {
  const token = localStorage.getItem('token');
  return token === 'demo-jwt-token-xyz';
};

// --- REAL ENDPOINTS ---

export const googleAuth = (token) => api.post('/auth/google', { token });
export const completeProfile = (data) => api.post('/auth/complete-profile', data);

export const getMyAppointments = () => {
  if (isDemoMode()) {
    // Return mock appointments for Demo/Dev mode
    const mockAppointments = [
      {
        id: 101,
        doctor: 'Dr. Jane Smith',
        specialty: 'Cardiology',
        appointment_date: new Date().toISOString().split('T')[0],
        appointment_start: '10:00',
        appointment_end: '10:30',
        problem: 'Chest discomfort & rapid heart rate',
        status: 'scheduled',
      },
      {
        id: 102,
        doctor: 'Dr. Robert Chen',
        specialty: 'Pediatrics',
        appointment_date: new Date(Date.now() + 86400000 * 2).toISOString().split('T')[0],
        appointment_start: '14:30',
        appointment_end: '15:00',
        problem: 'Routine health checkup',
        status: 'confirmed',
      }
    ];
    return Promise.resolve({ data: { appointments: mockAppointments, total: mockAppointments.length } });
  }
  return api.get('/appointments/me');
};

export const cancelAppointment = (id) => {
  if (isDemoMode()) {
    return Promise.resolve({ data: { ok: true, message: 'Cancelled successfully.' } });
  }
  return api.patch(`/appointments/${id}/cancel`);
};

export const getDoctors = () => {
  if (isDemoMode()) {
    const mockDoctors = [
      { id: 1, name: 'Dr. Jane Smith', specialty: 'Cardiology', location: 'Wing A, 2nd Floor' },
      { id: 2, name: 'Dr. Robert Chen', specialty: 'Pediatrics', location: 'Wing B, 1st Floor' },
      { id: 3, name: 'Dr. Sarah Jenkins', specialty: 'Dermatology', location: 'Wing C, Ground Floor' },
    ];
    return Promise.resolve({ data: { doctors: mockDoctors } });
  }
  return api.get('/doctors');
};

export const getAvailableSlots = (doctor, date, duration_min = 30, step_min = 30) => {
  if (isDemoMode()) {
    const mockSlots = [
      { start: '09:00', end: '09:30' },
      { start: '10:00', end: '10:30' },
      { start: '11:30', end: '12:00' },
      { start: '14:00', end: '14:30' },
      { start: '15:30', end: '16:00' },
    ];
    return Promise.resolve({ data: { slots: mockSlots, doctor, date } });
  }
  return api.get('/appointments/available', { params: { doctor, date, duration_min, step_min } });
};

export const bookAppointment = (data) => {
  if (isDemoMode()) {
    return Promise.resolve({
      data: {
        status: 'ok',
        booking_id: `demo-booking-${Math.random().toString(36).substr(2, 9)}`,
        payload: data,
        email: { ok: true }
      }
    });
  }
  return api.post('/appointments/book', data);
};

export const sendChat = (message, thread_id = null, selected_slot_id = null) => {
  if (isDemoMode()) {
    // Custom simulated AI assistant logic for Demo/Dev mode
    const msg = message.toLowerCase();
    let reply = "";
    let slots = [];
    let nextStep = null;

    if (selected_slot_id) {
      return Promise.resolve({
        data: {
          message: `Great choice! I have booked your appointment for slot ID: ${selected_slot_id}. You will receive a confirmation email shortly.`,
          next_step: 'done',
          appointment_id: `demo-booking-${Math.random().toString(36).substr(2, 9)}`,
        }
      });
    }

    if (msg.includes('chest') || msg.includes('heart') || msg.includes('pain')) {
      reply = "That sounds like it could be a cardiology concern. I recommend scheduling an appointment with Dr. Jane Smith (Cardiology). Here are the available slots for today:";
      slots = [
        { slot_id: 'slot-1', start: new Date().setHours(10, 0, 0).valueOf() },
        { slot_id: 'slot-2', start: new Date().setHours(11, 30, 0).valueOf() },
        { slot_id: 'slot-3', start: new Date().setHours(14, 0, 0).valueOf() },
      ];
      nextStep = 'pick_slot';
    } else if (msg.includes('child') || msg.includes('kid') || msg.includes('pediatr')) {
      reply = "I recommend booking an appointment with Dr. Robert Chen (Pediatrics). Here are some upcoming slots:";
      slots = [
        { slot_id: 'slot-4', start: new Date().setHours(9, 0, 0).valueOf() },
        { slot_id: 'slot-5', start: new Date().setHours(15, 30, 0).valueOf() },
      ];
      nextStep = 'pick_slot';
    } else {
      reply = "I understand you have some symptoms. Let me connect you with Dr. Sarah Jenkins (General Medicine / Dermatology). Please select a convenient slot below:";
      slots = [
        { slot_id: 'slot-6', start: new Date().setHours(10, 30, 0).valueOf() },
        { slot_id: 'slot-7', start: new Date().setHours(16, 0, 0).valueOf() },
      ];
      nextStep = 'pick_slot';
    }

    return Promise.resolve({
      data: {
        message: reply,
        available_slots: slots,
        next_step: nextStep,
      }
    });
  }
  return api.post('/chat', { message, thread_id, selected_slot_id });
};

export const checkHealth = () => api.get('/health');

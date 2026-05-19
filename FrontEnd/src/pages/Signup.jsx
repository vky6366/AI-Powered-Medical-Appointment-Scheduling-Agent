import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, Activity, Phone } from 'lucide-react';

export default function Signup() {
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', password: '' });
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSignup = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => { setIsLoading(false); navigate('/login'); }, 1000);
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4 py-12 min-h-[calc(100vh-73px)]"
      style={{ background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)' }}>
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ backgroundColor: '#e0f2fe', color: '#0284c7' }}>
            <Activity size={32} />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Create an Account</h2>
          <p className="text-gray-500">Join AIHealthCare to schedule appointments</p>
        </div>

        <div className="card shadow-lg">
          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User size={18} className="text-gray-400" />
                </div>
                <input type="text" name="name" required className="input-field pl-10"
                  placeholder="John Doe" value={formData.name} onChange={handleChange} />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail size={18} className="text-gray-400" />
                </div>
                <input type="email" name="email" required className="input-field pl-10"
                  placeholder="john@example.com" value={formData.email} onChange={handleChange} />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Phone size={18} className="text-gray-400" />
                </div>
                <input type="tel" name="phone" className="input-field pl-10"
                  placeholder="+91 98765 43210" value={formData.phone} onChange={handleChange} />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock size={18} className="text-gray-400" />
                </div>
                <input type="password" name="password" required className="input-field pl-10"
                  placeholder="••••••••" value={formData.password} onChange={handleChange} />
              </div>
            </div>

            <button type="submit" disabled={isLoading}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-6">
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (<>Create Account <ArrowRight size={18} /></>)}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="font-medium" style={{ color: '#0284c7' }}>Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

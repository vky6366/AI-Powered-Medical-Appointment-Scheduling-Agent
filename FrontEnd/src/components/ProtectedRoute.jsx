import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

export function ProtectedRoute({ children }) {
  const { token, profileComplete } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  if (!profileComplete) return <Navigate to="/complete-profile" replace />;
  return children;
}

export function ProfileGuard({ children }) {
  const { token, profileComplete } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  if (profileComplete) return <Navigate to="/dashboard" replace />;
  return children;
}

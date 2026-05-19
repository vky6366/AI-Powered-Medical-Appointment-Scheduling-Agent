import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute, ProfileGuard } from './components/ProtectedRoute';
import Login from './pages/Login';
import CompleteProfile from './pages/CompleteProfile';
import Dashboard from './pages/Dashboard';

// Load Google OAuth script once
function GoogleScript() {
  return <script src="https://accounts.google.com/gsi/client" async defer />;
}

export default function App() {
  return (
    <AuthProvider>
      <GoogleScript />
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/complete-profile" element={
            <ProfileGuard><CompleteProfile /></ProfileGuard>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute><Dashboard /></ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

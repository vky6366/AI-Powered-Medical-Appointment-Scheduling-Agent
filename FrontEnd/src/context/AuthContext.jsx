import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [profileComplete, setProfileComplete] = useState(() => {
    return localStorage.getItem('profile_complete') === 'true';
  });

  const login = (accessToken, userData, isProfileComplete) => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('profile_complete', String(isProfileComplete));
    setToken(accessToken);
    setUser(userData);
    setProfileComplete(isProfileComplete);
  };

  const logout = () => {
    localStorage.clear();
    setToken(null);
    setUser(null);
    setProfileComplete(false);
  };

  const markProfileComplete = () => {
    localStorage.setItem('profile_complete', 'true');
    setProfileComplete(true);
  };

  return (
    <AuthContext.Provider value={{ user, token, profileComplete, login, logout, markProfileComplete }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

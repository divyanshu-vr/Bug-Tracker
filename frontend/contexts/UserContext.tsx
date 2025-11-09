/**
 * User Context Provider
 * 
 * Manages current user state and provides user selection functionality.
 * Stores selected user in React context for global access.
 * 
 * Requirements: 3.1, 3.4
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '@/utils/types';

interface UserContextType {
  currentUser: User | null;
  setCurrentUser: (user: User | null) => void;
  isLoading: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

interface UserProviderProps {
  children: React.ReactNode;
}

export const UserProvider: React.FC<UserProviderProps> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load user from localStorage on mount
    const storedUser = localStorage.getItem('bugtrackr_current_user');
    if (storedUser) {
      try {
        setCurrentUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Failed to parse stored user:', error);
        localStorage.removeItem('bugtrackr_current_user');
      }
    }
    setIsLoading(false);
  }, []);

  const handleSetCurrentUser = (user: User | null) => {
    setCurrentUser(user);
    if (user) {
      localStorage.setItem('bugtrackr_current_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('bugtrackr_current_user');
    }
  };

  return (
    <UserContext.Provider
      value={{
        currentUser,
        setCurrentUser: handleSetCurrentUser,
        isLoading,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

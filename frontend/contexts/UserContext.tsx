/**
 * User Context Provider
 * 
 * Manages current user state and provides user selection functionality.
 * Stores selected user in React context for global access.
 * 
 * Requirements: 3.1, 3.4
 */

import React, { createContext, useContext, useState } from 'react';
import { User } from '@/utils/types';

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
  // Lazy initialization: load from localStorage only once on mount
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    if (typeof window !== 'undefined') {
      const storedUser = localStorage.getItem('bugtrackr_current_user');
      if (storedUser) {
        try {
          return JSON.parse(storedUser);
        } catch (error) {
          console.error('Failed to parse stored user:', error);
          localStorage.removeItem('bugtrackr_current_user');
        }
      }
    }
    return null;
  });

  const isLoading = false; // No longer needed since we use lazy initialization

  const handleSetCurrentUser = (user: User | null) => {
    setCurrentUser(user);
    
    // Only access localStorage in browser environment
    if (typeof window !== 'undefined') {
      if (user) {
        localStorage.setItem('bugtrackr_current_user', JSON.stringify(user));
      } else {
        localStorage.removeItem('bugtrackr_current_user');
      }
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

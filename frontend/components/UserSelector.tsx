/**
 * UserSelector Component
 * 
 * Implements predefined user selection dropdown with role display.
 * Stores selected user in context for application-wide access.
 * 
 * Requirements: 3.1, 3.4
 */

import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useUser } from '@/contexts/UserContext';
import { User } from '@/utils/types';
import { getInitials } from '@/lib/utils';

interface UserSelectorProps {
  users: User[];
  onUserChange?: (user: User | null) => void;
  className?: string;
}



/**
 * Get badge variant based on user role
 */
const getRoleBadgeVariant = (role: string): "default" | "secondary" | "destructive" | "outline" => {
  switch (role.toLowerCase()) {
    case 'admin':
      return "destructive";
    case 'developer':
      return "default";
    case 'tester':
      return "secondary";
    default:
      return "outline";
  }
};

/**
 * Format role for display
 */
const formatRole = (role: string): string => {
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase();
};

export const UserSelector: React.FC<UserSelectorProps> = ({
  users,
  onUserChange,
  className,
}) => {
  const { currentUser, setCurrentUser } = useUser();

  // Derive selectedUserId from currentUser instead of syncing state
  const selectedUserId = currentUser?._id || '';

  const handleValueChange = (userId: string) => {
    const user = users.find(u => u._id === userId) || null;
    setCurrentUser(user);
    
    if (onUserChange) {
      onUserChange(user);
    }
  };

  return (
    <div className={className}>
      <Select value={selectedUserId} onValueChange={handleValueChange}>
        <SelectTrigger className="w-[240px]">
          <SelectValue placeholder="Select user">
            {currentUser && (
              <div className="flex items-center gap-2">
                <Avatar className="size-6">
                  <AvatarFallback className="text-xs">
                    {getInitials(currentUser.name)}
                  </AvatarFallback>
                </Avatar>
                <span className="font-medium">{currentUser.name}</span>
              </div>
            )}
          </SelectValue>
        </SelectTrigger>

        <SelectContent>
          {users.map((user) => (
            <SelectItem key={user._id} value={user._id}>
              <div className="flex items-center gap-2 w-full">
                <Avatar className="size-6">
                  <AvatarFallback className="text-xs">
                    {getInitials(user.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex flex-col flex-1 min-w-0">
                  <span className="font-medium truncate">{user.name}</span>
                  <span className="text-xs text-muted-foreground truncate">
                    {user.email}
                  </span>
                </div>
                <Badge
                  variant={getRoleBadgeVariant(user.role)}
                  className="ml-auto"
                >
                  {formatRole(user.role)}
                </Badge>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Display current user role */}
      {currentUser && (
        <div className="mt-2 text-sm text-muted-foreground">
          Logged in as{' '}
          <Badge variant={getRoleBadgeVariant(currentUser.role)} className="ml-1">
            {formatRole(currentUser.role)}
          </Badge>
        </div>
      )}
    </div>
  );
};

/**
 * TypeScript interfaces matching backend Pydantic models
 * These types ensure type safety for API communication
 */

// Enums matching backend
export enum BugStatus {
  OPEN = "Open",
  IN_PROGRESS = "In Progress",
  RESOLVED = "Resolved",
  CLOSED = "Closed",
}

export enum BugPriority {
  LOW = "Low",
  MEDIUM = "Medium",
  HIGH = "High",
  CRITICAL = "Critical",
}

export enum BugSeverity {
  MINOR = "Minor",
  MAJOR = "Major",
  BLOCKER = "Blocker",
}

export enum UserRole {
  TESTER = "tester",
  DEVELOPER = "developer",
  ADMIN = "admin",
}

// Core entity interfaces
export interface Bug {
  _id: string;
  title: string;
  description: string;
  projectId: string;
  reportedBy: string;
  assignedTo?: string;
  status: BugStatus;
  priority: BugPriority;
  severity: BugSeverity;
  tags: string[];
  validated: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Comment {
  _id: string;
  bugId: string;
  authorId: string;
  message: string;
  createdAt: string;
}

export interface Project {
  _id: string;
  name: string;
  description: string;
  createdBy: string;
  createdAt: string;
}

export interface User {
  _id: string;
  name: string;
  email: string;
  role: UserRole;
  createdAt: string;
}

export interface ActivityLog {
  _id: string;
  bugId: string;
  action: string;
  performedBy: string;
  timestamp: string;
}

// API Request types
export interface BugCreateRequest {
  title: string;
  description: string;
  projectId: string;
  reportedBy: string;
  priority: BugPriority;
  severity: BugSeverity;
}

export interface BugStatusUpdateRequest {
  status: BugStatus;
  userId: string;
  userRole: string;
}

export interface BugAssignRequest {
  assignedTo: string;
  assignedBy: string;
}

export interface CommentCreateRequest {
  bugId: string;
  authorId: string;
  message: string;
}

// API Response types
export interface BugResponse {
  _id: string;
  title: string;
  description: string;
  projectId: string;
  reportedBy: string;
  assignedTo?: string;
  status: string;
  priority: string;
  severity: string;
  tags: string[];
  validated: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CommentResponse {
  _id: string;
  bugId: string;
  authorId: string;
  message: string;
  createdAt: string;
}

export interface ProjectResponse {
  _id: string;
  name: string;
  description: string;
  createdBy: string;
  createdAt: string;
}

export interface BugWithCommentsResponse {
  bug: BugResponse;
  comments: CommentResponse[];
}

export interface StatusUpdateResponse {
  success: boolean;
  message: string;
  bug?: BugResponse;
}

export interface AssignmentResponse {
  success: boolean;
  message: string;
  bug?: BugResponse;
}

// Role-based permission helpers
export interface RolePermissions {
  canCreateBug: boolean;
  canValidateBug: boolean;
  canCloseBug: boolean;
  canAssignBug: boolean;
  canUpdateStatus: boolean;
  canComment: boolean;
}

export const getRolePermissions = (role: UserRole): RolePermissions => {
  switch (role) {
    case UserRole.TESTER:
      return {
        canCreateBug: true,
        canValidateBug: true,
        canCloseBug: true,
        canAssignBug: false,
        canUpdateStatus: false,
        canComment: true,
      };
    case UserRole.DEVELOPER:
      return {
        canCreateBug: true,
        canValidateBug: false,
        canCloseBug: false,
        canAssignBug: true,
        canUpdateStatus: true,
        canComment: true,
      };
    case UserRole.ADMIN:
      return {
        canCreateBug: true,
        canValidateBug: true,
        canCloseBug: true,
        canAssignBug: true,
        canUpdateStatus: true,
        canComment: true,
      };
    default:
      return {
        canCreateBug: false,
        canValidateBug: false,
        canCloseBug: false,
        canAssignBug: false,
        canUpdateStatus: false,
        canComment: false,
      };
  }
};

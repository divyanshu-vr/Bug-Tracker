/**
 * Axios API client configuration for BugTrackr backend
 * Handles request/response transformation, error handling, and interceptors
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import type {
  Bug,
  Comment,
  Project,
  User,
  BugCreateRequest,
  BugStatusUpdateRequest,
  BugAssignRequest,
  CommentCreateRequest,
  BugWithCommentsResponse,
  StatusUpdateResponse,
  AssignmentResponse,
  BugResponse,
  CommentResponse,
  ProjectResponse,
} from './types';

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Log request in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status);
    }
    return response;
  },
  (error: AxiosError<ApiErrorResponse>) => {
    // Handle errors
    const errorMessage = handleApiError(error);
    console.error('[API Response Error]', errorMessage);
    return Promise.reject(error);
  }
);

/**
 * API Error Response structure
 */
interface ApiErrorResponse {
  detail?: string | ValidationError[];
}

interface ValidationError {
  msg: string;
  loc: string[];
  type: string;
}

/**
 * Handle API errors and return user-friendly messages
 */
export const handleApiError = (error: AxiosError<ApiErrorResponse>): string => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        return data?.detail && typeof data.detail === 'string' 
          ? data.detail 
          : 'Invalid request. Please check your input.';
      case 401:
        return 'Unauthorized. Please log in again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return data?.detail && typeof data.detail === 'string'
          ? data.detail 
          : 'Resource not found.';
      case 422:
        // Validation error
        if (data?.detail && Array.isArray(data.detail)) {
          return data.detail.map((err) => err.msg).join(', ');
        }
        return 'Validation error. Please check your input.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return data?.detail && typeof data.detail === 'string'
          ? data.detail 
          : `Error: ${status}`;
    }
  } else if (error.request) {
    // Request made but no response
    return 'Network error. Please check your connection.';
  } else {
    // Error setting up request
    return error.message || 'An unexpected error occurred.';
  }
};

/**
 * Transform backend date strings to Date objects
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const transformDates = <T extends Record<string, any>>(data: T): T => {
  const dateFields = ['createdAt', 'updatedAt', 'timestamp'];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const transformed = { ...data } as Record<string, any>;

  dateFields.forEach(field => {
    if (transformed[field] && typeof transformed[field] === 'string') {
      transformed[field] = new Date(transformed[field]);
    }
  });
  return transformed as T;
};

// Bug API endpoints
export const bugApi = {
  /**
   * Get all bugs
   */
  getAll: async (): Promise<Bug[]> => {
    const response = await apiClient.get<Bug[]>('/api/bugs');
    return response.data.map(transformDates);
  },

  /**
   * Get bug by ID with comments
   */
  getById: async (id: string): Promise<BugWithCommentsResponse> => {
    const response = await apiClient.get<BugWithCommentsResponse>(`/api/bugs/${id}`);
    return {
      bug: transformDates(response.data.bug),
      comments: response.data.comments.map(transformDates),
    };
  },

  /**
   * Create new bug
   */
  create: async (data: BugCreateRequest): Promise<BugResponse> => {
    const response = await apiClient.post<BugResponse>('/api/bugs', data);
    return transformDates(response.data);
  },

  /**
   * Update bug status
   */
  updateStatus: async (id: string, data: BugStatusUpdateRequest): Promise<StatusUpdateResponse> => {
    const response = await apiClient.patch<StatusUpdateResponse>(`/api/bugs/${id}/status`, data);
    if (response.data.bug) {
      response.data.bug = transformDates(response.data.bug);
    }
    return response.data;
  },

  /**
   * Validate bug (tester only)
   */
  validate: async (id: string, userId: string): Promise<StatusUpdateResponse> => {
    const response = await apiClient.patch<StatusUpdateResponse>(`/api/bugs/${id}/validate`, { userId });
    if (response.data.bug) {
      response.data.bug = transformDates(response.data.bug);
    }
    return response.data;
  },

  /**
   * Assign bug to user
   */
  assign: async (id: string, data: BugAssignRequest): Promise<AssignmentResponse> => {
    const response = await apiClient.patch<AssignmentResponse>(`/api/bugs/${id}/assign`, data);
    if (response.data.bug) {
      response.data.bug = transformDates(response.data.bug);
    }
    return response.data;
  },
};

// Comment API endpoints
export const commentApi = {
  /**
   * Create new comment
   */
  create: async (data: CommentCreateRequest): Promise<CommentResponse> => {
    const response = await apiClient.post<CommentResponse>('/api/comments', data);
    return transformDates(response.data);
  },

  /**
   * Get comments for a bug
   */
  getByBugId: async (bugId: string): Promise<Comment[]> => {
    const response = await apiClient.get<Comment[]>(`/api/bugs/${bugId}/comments`);
    return response.data.map(transformDates);
  },
};

// Project API endpoints
export const projectApi = {
  /**
   * Get all projects
   */
  getAll: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/api/projects');
    return response.data.map(transformDates);
  },

  /**
   * Get project by ID
   */
  getById: async (id: string): Promise<ProjectResponse> => {
    const response = await apiClient.get<ProjectResponse>(`/api/projects/${id}`);
    return transformDates(response.data);
  },
};

// User API endpoints
export const userApi = {
  /**
   * Get all users
   */
  getAll: async (): Promise<User[]> => {
    const response = await apiClient.get<User[]>('/api/users');
    return response.data.map(transformDates);
  },

  /**
   * Get user by ID
   */
  getById: async (id: string): Promise<User> => {
    const response = await apiClient.get<User>(`/api/users/${id}`);
    return transformDates(response.data);
  },
};

// Export configured client for custom requests
export default apiClient;

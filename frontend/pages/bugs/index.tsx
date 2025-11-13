/**
 * Bug List Page
 * 
 * Displays all bugs with filtering by status and priority.
 * Provides navigation to bug details and creation pages.
 * 
 * Requirements: 2.1, 5.2
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { bugApi, userApi, projectApi } from '@/utils/apiClient';
import { Bug, BugStatus, BugPriority, User, Project } from '@/utils/types';
import { useUser } from '@/contexts/UserContext';
import { LoadingState } from '@/components/LoadingState';
import { ApiErrorFallback } from '@/components/ApiErrorFallback';

export default function BugsPage() {
  const router = useRouter();
  const { currentUser } = useUser();
  
  const [bugs, setBugs] = useState<Bug[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<Error | null>(null);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setLoadError(null);
    
    try {
      const [bugsData, usersData, projectsData] = await Promise.all([
        bugApi.getAll(),
        userApi.getAll(),
        projectApi.getAll(),
      ]);
      
      setBugs(bugsData);
      setUsers(usersData);
      setProjects(projectsData);
      
    } catch (err) {
      console.error('Failed to load bugs:', err);
      setLoadError(err as Error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDetails = (bugId: string) => {
    router.push(`/bugs/${bugId}`);
  };

  const handleCreateBug = () => {
    router.push('/bugs/new');
  };

  // Get user name by ID
  const getUserName = (userId: string): string => {
    const user = users.find(u => u._id === userId);
    return user?.name || 'Unknown User';
  };

  // Get project name by ID
  const getProjectName = (projectId: string): string => {
    const project = projects.find(p => p._id === projectId);
    return project?.name || 'Unknown Project';
  };

  // Get badge variant for priority
  const getPriorityBadgeVariant = (priority: BugPriority): "default" | "secondary" | "destructive" | "outline" => {
    switch (priority) {
      case BugPriority.CRITICAL:
        return "destructive";
      case BugPriority.HIGH:
        return "destructive";
      case BugPriority.MEDIUM:
        return "default";
      case BugPriority.LOW:
        return "secondary";
      default:
        return "outline";
    }
  };

  // Get badge variant for status
  const getStatusBadgeVariant = (status: BugStatus): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case BugStatus.OPEN:
        return "destructive";
      case BugStatus.IN_PROGRESS:
        return "default";
      case BugStatus.RESOLVED:
        return "secondary";
      case BugStatus.CLOSED:
        return "outline";
      default:
        return "outline";
    }
  };

  // Format relative time
  const formatRelativeTime = (date: string): string => {
    const now = new Date();
    const bugDate = new Date(date);
    const diffMs = now.getTime() - bugDate.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return diffMins <= 1 ? '1 minute ago' : `${diffMins} minutes ago`;
    } else if (diffHours < 24) {
      return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`;
    } else if (diffDays < 30) {
      return diffDays === 1 ? '1 day ago' : `${diffDays} days ago`;
    } else {
      return bugDate.toLocaleDateString();
    }
  };

  // Filter bugs based on selected filters
  const filteredBugs = bugs.filter(bug => {
    const matchesStatus = statusFilter === 'all' || bug.status === statusFilter;
    const matchesPriority = priorityFilter === 'all' || bug.priority === priorityFilter;
    const matchesSearch = searchQuery === '' || 
      bug.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      bug.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesStatus && matchesPriority && matchesSearch;
  });

  if (isLoading) {
    return <LoadingState message="Loading bugs..." fullScreen />;
  }

  if (loadError) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <ApiErrorFallback
            error={loadError}
            onRetry={loadData}
            title="Failed to load bugs"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">All Bugs</h1>
            <p className="text-muted-foreground mt-1">
              Manage and track all reported bugs
            </p>
          </div>
          {currentUser && (
            <Button onClick={handleCreateBug}>
              Create Bug
            </Button>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Input
            placeholder="Search bugs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="sm:max-w-xs"
          />
          
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="sm:w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value={BugStatus.OPEN}>{BugStatus.OPEN}</SelectItem>
              <SelectItem value={BugStatus.IN_PROGRESS}>{BugStatus.IN_PROGRESS}</SelectItem>
              <SelectItem value={BugStatus.RESOLVED}>{BugStatus.RESOLVED}</SelectItem>
              <SelectItem value={BugStatus.CLOSED}>{BugStatus.CLOSED}</SelectItem>
            </SelectContent>
          </Select>

          <Select value={priorityFilter} onValueChange={setPriorityFilter}>
            <SelectTrigger className="sm:w-[180px]">
              <SelectValue placeholder="Filter by priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priorities</SelectItem>
              <SelectItem value={BugPriority.CRITICAL}>{BugPriority.CRITICAL}</SelectItem>
              <SelectItem value={BugPriority.HIGH}>{BugPriority.HIGH}</SelectItem>
              <SelectItem value={BugPriority.MEDIUM}>{BugPriority.MEDIUM}</SelectItem>
              <SelectItem value={BugPriority.LOW}>{BugPriority.LOW}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Results count */}
        <div className="text-sm text-muted-foreground">
          Showing {filteredBugs.length} of {bugs.length} bugs
        </div>

        {/* Bug table */}
        {filteredBugs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <p className="text-muted-foreground">No bugs found</p>
            <Button variant="outline" onClick={handleCreateBug}>
              Create First Bug
            </Button>
          </div>
        ) : (
          <div className="bg-card rounded-lg border">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Title</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Project</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Priority</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Assignee</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-muted-foreground">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBugs.map((bug) => (
                    <tr 
                      key={bug._id} 
                      className="border-b last:border-b-0 hover:bg-muted/30 cursor-pointer transition-colors"
                      onClick={() => handleViewDetails(bug._id)}
                    >
                      <td className="px-6 py-4">
                        <div className="font-medium text-foreground">{bug.title}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-muted-foreground">{getProjectName(bug.projectId)}</span>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={getPriorityBadgeVariant(bug.priority)}>
                          {bug.priority}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={getStatusBadgeVariant(bug.status)}>
                          {bug.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {bug.assignedTo ? (
                            <>
                              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                                {getUserName(bug.assignedTo).charAt(0).toUpperCase()}
                              </div>
                              <span className="text-sm">{getUserName(bug.assignedTo)}</span>
                            </>
                          ) : (
                            <span className="text-sm text-muted-foreground">Unassigned</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {formatRelativeTime(bug.createdAt)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

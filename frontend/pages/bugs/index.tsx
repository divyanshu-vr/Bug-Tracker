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
import { BugCard } from '@/components/BugCard';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { bugApi, projectApi, userApi, commentApi } from '@/utils/apiClient';
import { Bug, BugStatus, BugPriority, Project, User } from '@/utils/types';
import { useUser } from '@/contexts/UserContext';

export default function BugsPage() {
  const router = useRouter();
  const { currentUser } = useUser();
  
  const [bugs, setBugs] = useState<Bug[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [commentCounts, setCommentCounts] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const [bugsData, projectsData, usersData] = await Promise.all([
        bugApi.getAll(),
        projectApi.getAll(),
        userApi.getAll(),
      ]);
      
      setBugs(bugsData);
      setProjects(projectsData);
      setUsers(usersData);
      
      // Load comment counts for each bug
      const counts: Record<string, number> = {};
      await Promise.all(
        bugsData.map(async (bug) => {
          try {
            const comments = await commentApi.getByBugId(bug._id);
            counts[bug._id] = comments.length;
          } catch (err) {
            counts[bug._id] = 0;
          }
        })
      );
      setCommentCounts(counts);
    } catch (err) {
      console.error('Failed to load bugs:', err);
      setError('Failed to load bugs. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusUpdate = async (bugId: string, newStatus: BugStatus) => {
    if (!currentUser) {
      alert('Please select a user first');
      return;
    }

    try {
      await bugApi.updateStatus(bugId, {
        status: newStatus,
        userId: currentUser._id,
        userRole: currentUser.role as any,
      });
      
      // Reload bugs to reflect changes
      await loadData();
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('Failed to update bug status');
    }
  };

  const handleViewDetails = (bugId: string) => {
    router.push(`/bugs/${bugId}`);
  };

  const handleCreateBug = () => {
    router.push('/bugs/new');
  };

  // Get project name by ID


  // Get user name by ID
  const getUserName = (userId: string): string => {
    const user = users.find(u => u._id === userId);
    return user?.name || 'Unknown User';
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
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground">Loading bugs...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <p className="text-destructive">{error}</p>
            <Button onClick={loadData}>Retry</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Bugs</h1>
            <p className="text-muted-foreground mt-1">
              Manage and track all reported bugs
            </p>
          </div>
          <Button onClick={handleCreateBug}>
            Create Bug
          </Button>
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

        {/* Bug list */}
        {filteredBugs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <p className="text-muted-foreground">No bugs found</p>
            <Button variant="outline" onClick={handleCreateBug}>
              Create First Bug
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredBugs.map((bug) => (
              <BugCard
                key={bug._id}
                bug={bug}
                commentCount={commentCounts[bug._id] || 0}
                assignedUserName={bug.assignedTo ? getUserName(bug.assignedTo) : undefined}
                onStatusUpdate={handleStatusUpdate}
                onViewDetails={handleViewDetails}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

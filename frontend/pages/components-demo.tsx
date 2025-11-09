/**
 * Component Demo Page
 * 
 * Showcases all core BugTrackr components with sample data
 */

'use client';

import React, { useState, useEffect } from 'react';
import { BugCard } from '@/components/BugCard';
import { CommentSection } from '@/components/CommentSection';
import { UserSelector } from '@/components/UserSelector';
import { Bug, Comment, User, BugStatus, BugPriority, BugSeverity } from '@/utils/types';
import { userApi } from '@/utils/apiClient';

const createSampleBugs = (users: User[]): Bug[] => {
  // Use real user IDs from Collection DB if available
  const userId2 = users[1]?._id || '2';
  const userId3 = users[2]?._id || '3';

  return [
    {
      _id: '1',
      title: 'Login button not responding on mobile',
      description: 'When users tap the login button on mobile devices, nothing happens. This issue only occurs on iOS Safari.',
      projectId: 'proj-1',
      reportedBy: userId3,
      assignedTo: userId2,
      status: BugStatus.OPEN,
      priority: BugPriority.HIGH,
      severity: BugSeverity.MAJOR,
      tags: ['mobile', 'ios', 'login'],
      validated: false,
      createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    },
    {
      _id: '2',
      title: 'Dashboard charts not loading',
      description: 'The analytics dashboard shows a loading spinner indefinitely. Console shows CORS errors.',
      projectId: 'proj-1',
      reportedBy: userId2,
      assignedTo: userId2,
      status: BugStatus.IN_PROGRESS,
      priority: BugPriority.CRITICAL,
      severity: BugSeverity.BLOCKER,
      tags: ['dashboard', 'charts', 'api'],
      validated: false,
      createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    },
    {
      _id: '3',
      title: 'Typo in welcome email',
      description: 'The welcome email has "Welcom" instead of "Welcome" in the subject line.',
      projectId: 'proj-1',
      reportedBy: userId3,
      status: BugStatus.RESOLVED,
      priority: BugPriority.LOW,
      severity: BugSeverity.MINOR,
      tags: ['email', 'typo'],
      validated: true,
      createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    },
  ];
};

const createSampleComments = (users: User[]): Comment[] => {
  const userId2 = users[1]?._id || '2';
  const userId3 = users[2]?._id || '3';

  return [
    {
      _id: 'c1',
      bugId: '1',
      authorId: userId2,
      message: 'I can reproduce this on my iPhone 13. Looks like a touch event handler issue.',
      createdAt: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
    },
    {
      _id: 'c2',
      bugId: '1',
      authorId: userId3,
      message: 'Also confirmed on iPad Pro. Android devices work fine.',
      createdAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    },
    {
      _id: 'c3',
      bugId: '1',
      authorId: userId2,
      message: 'Working on a fix. Will have it ready by EOD.',
      createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    },
  ];
};

export default function ComponentsDemo() {
  const [mounted, setMounted] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [sampleBugs, setSampleBugs] = useState<Bug[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  useEffect(() => {
    setMounted(true);
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const fetchedUsers = await userApi.getAll();
      setUsers(fetchedUsers);
      // Create sample bugs and comments with real user IDs
      setSampleBugs(createSampleBugs(fetchedUsers));
      setComments(createSampleComments(fetchedUsers));
      // Set first user as default
      if (fetchedUsers.length > 0) {
        setSelectedUser(fetchedUsers[0]);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setError('Failed to load users from backend');
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async (bugId: string, message: string) => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const newComment: Comment = {
      _id: `c${comments.length + 1}`,
      bugId,
      authorId: selectedUser?._id || '1',
      message,
      createdAt: new Date().toISOString(),
    };
    
    setComments([...comments, newComment]);
  };

  const handleStatusUpdate = (bugId: string, newStatus: BugStatus) => {
    console.log(`Updating bug ${bugId} to status: ${newStatus}`);
    alert(`Status updated to: ${newStatus}`);
  };

  const handleViewDetails = (bugId: string) => {
    console.log(`Viewing details for bug: ${bugId}`);
    alert(`Viewing bug details: ${bugId}`);
  };

  const getUserName = (userId: string): string => {
    return users.find(u => u._id === userId)?.name || 'Unknown User';
  };

  if (!mounted) {
    return null;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">Loading...</div>
          <p className="text-muted-foreground">Fetching users from backend</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2 text-destructive">Error</div>
          <p className="text-muted-foreground">{error}</p>
          <button
            onClick={fetchUsers}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Component Showcase</h1>
          <p className="text-muted-foreground">
            Preview of BugTrackr core components with sample data
          </p>
        </div>

        {/* User Selector Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">User Selector</h2>
          <div className="bg-card border rounded-xl p-6">
            {users.length > 0 ? (
              <UserSelector
                users={users}
                onUserChange={(user) => {
                  setSelectedUser(user);
                  console.log('Selected user:', user);
                }}
              />
            ) : (
              <p className="text-muted-foreground">No users found in Collection DB</p>
            )}
          </div>
        </section>

        {/* Bug Cards Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">Bug Cards</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {sampleBugs.map((bug) => (
              <BugCard
                key={bug._id}
                bug={bug}
                commentCount={bug._id === '1' ? comments.length : Math.floor(Math.random() * 5)}
                assignedUserName={
                  bug.assignedTo ? getUserName(bug.assignedTo) : undefined
                }
                onStatusUpdate={handleStatusUpdate}
                onViewDetails={handleViewDetails}
              />
            ))}
          </div>
        </section>

        {/* Comment Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">Comment Section</h2>
          <div className="max-w-3xl">
            <CommentSection
              bugId="1"
              comments={comments}
              currentUserId={selectedUser?._id || '1'}
              currentUserName={selectedUser?.name || 'Guest User'}
              onAddComment={handleAddComment}
              getUserName={getUserName}
            />
          </div>
        </section>

        {/* Component Info */}
        <section className="mt-12 p-6 bg-muted/50 rounded-xl">
          <h3 className="text-lg font-semibold mb-2">Component Features</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>✓ Built with ShadCN UI primitives</li>
            <li>✓ Fully typed with TypeScript</li>
            <li>✓ Apple-inspired minimalist design</li>
            <li>✓ Responsive and accessible</li>
            <li>✓ Dark mode support</li>
            <li>✓ Interactive with real-time updates</li>
          </ul>
        </section>
      </div>
    </div>
  );
}

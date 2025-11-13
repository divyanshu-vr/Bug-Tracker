import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useUser } from '@/contexts/UserContext';
import { bugApi, projectApi } from '@/utils/apiClient';
import { Bug, Project, BugStatus, BugPriority } from '@/utils/types';
import { AlertCircle, CheckCircle2, Clock, TrendingUp } from 'lucide-react';
import WelcomeScreen from '@/components/WelcomeScreen';

interface BugStatistics {
  total: number;
  open: number;
  inProgress: number;
  resolved: number;
  closed: number;
  critical: number;
  high: number;
}

export default function Home() {
  const router = useRouter();
  const { currentUser } = useUser();
  const [bugs, setBugs] = useState<Bug[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [statistics, setStatistics] = useState<BugStatistics>({
    total: 0,
    open: 0,
    inProgress: 0,
    resolved: 0,
    closed: 0,
    critical: 0,
    high: 0,
  });
  const [loading, setLoading] = useState(true);
  const [showWelcome, setShowWelcome] = useState(false);
  const [dataLoaded, setDataLoaded] = useState(false);

  // Show welcome screen only on first load of the session
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const hasSeenWelcome = sessionStorage.getItem('hasSeenWelcome');
      if (!hasSeenWelcome) {
        setShowWelcome(true);
        sessionStorage.setItem('hasSeenWelcome', 'true');
      }
    }
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [bugsData, projectsData] = await Promise.all([
          bugApi.getAll(),
          projectApi.getAll(),
        ]);
        
        setBugs(bugsData);
        setProjects(projectsData);
        
        // Calculate statistics
        const stats: BugStatistics = {
          total: bugsData.length,
          open: bugsData.filter(b => b.status === BugStatus.OPEN).length,
          inProgress: bugsData.filter(b => b.status === BugStatus.IN_PROGRESS).length,
          resolved: bugsData.filter(b => b.status === BugStatus.RESOLVED).length,
          closed: bugsData.filter(b => b.status === BugStatus.CLOSED).length,
          critical: bugsData.filter(b => b.priority === BugPriority.CRITICAL).length,
          high: bugsData.filter(b => b.priority === BugPriority.HIGH).length,
        };
        setStatistics(stats);
        setDataLoaded(true);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        setDataLoaded(true);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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

  const recentBugs = bugs
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 5);

  const getProjectName = (projectId: string): string => {
    const project = projects.find(p => p._id === projectId);
    return project?.name || 'Unknown Project';
  };

  const handleWelcomeComplete = () => {
    setShowWelcome(false);
  };

  return (
    <>
      {/* Always render the dashboard content */}
      <div className="p-8">
        <div className="max-w-7xl mx-auto space-y-8">

          {currentUser ? (
            <div>
              <h1 className="text-4xl font-bold tracking-tight">Welcome Back, {currentUser.name}</h1>
              <p className="text-muted-foreground mt-2">
                Heres the summary of the bug tracking activities so far.
              </p>
            </div>
          ) : (
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                Please select a user from the navigation to get started
              </p>
            </div>
          )}

        {/* Bug Statistics Dashboard */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Bug Statistics</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Bugs</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.total}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Across {projects.length} projects
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Open Bugs</CardTitle>
                <AlertCircle className="h-4 w-4 text-destructive" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.open}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {statistics.critical} critical, {statistics.high} high priority
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">In Progress</CardTitle>
                <Clock className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.inProgress}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Being worked on
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Resolved</CardTitle>
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.resolved + statistics.closed}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {statistics.resolved} awaiting validation
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Recent Bugs */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">Recent Bugs</h2>
            <Button variant="ghost" onClick={() => router.push('/bugs')}>
              View All
            </Button>
          </div>
          {recentBugs.length > 0 ? (
            <div className="space-y-3">
              {recentBugs.map((bug) => (
                <Card 
                  key={bug._id} 
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => router.push(`/bugs/${bug._id}`)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium">{bug.title}</h3>
                          <Badge variant={getStatusBadgeVariant(bug.status)}>
                            {bug.status}
                          </Badge>
                          <Badge variant={getPriorityBadgeVariant(bug.priority)}>
                            {bug.priority}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {bug.description}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span>{getProjectName(bug.projectId)}</span>
                          <span>•</span>
                          <span>{new Date(bug.createdAt).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                No bugs reported yet
              </CardContent>
            </Card>
          )}
        </div>

        {/* Quick Navigation */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Quick Actions</h2>
          <div className="grid gap-6 md:grid-cols-3">
            <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push('/bugs/new')}>
              <CardHeader>
                <CardTitle>Create Bug</CardTitle>
                <CardDescription>
                  Report a new bug or issue
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full">
                  New Bug Report
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push('/bugs')}>
              <CardHeader>
                <CardTitle>All Bugs</CardTitle>
                <CardDescription>
                  View and manage all reported bugs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full">
                  View All Bugs
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push('/projects')}>
              <CardHeader>
                <CardTitle>Projects</CardTitle>
                <CardDescription>
                  Browse bugs organized by project
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full">
                  View Projects
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
        </div>
      </div>
      
      {/* Show welcome screen overlay */}
      {showWelcome && <WelcomeScreen onComplete={handleWelcomeComplete} isDataLoaded={dataLoaded} />}
    </>
  );
}

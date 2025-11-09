# Core Frontend Components

This directory contains the core UI components for the BugTrackr application, built with ShadCN UI and following Apple-inspired minimalist design principles.

## Components

### BugCard
Displays bug summary information with status and priority indicators.

**Features:**
- Status and priority badges with color coding
- Quick action buttons for status updates
- Comment count display
- Assignment information with avatar
- Validated indicator

**Usage:**
```tsx
import { BugCard } from '@/components';

<BugCard
  bug={bugData}
  commentCount={5}
  assignedUserName="John Doe"
  onStatusUpdate={(bugId, newStatus) => handleStatusUpdate(bugId, newStatus)}
  onViewDetails={(bugId) => router.push(`/bugs/${bugId}`)}
/>
```

### CommentSection
Renders chronological comment threads with author information.

**Features:**
- Scrollable comment thread
- Chronological ordering (oldest first)
- Relative time display
- Comment creation form with validation
- Author avatars and names

**Usage:**
```tsx
import { CommentSection } from '@/components';

<CommentSection
  bugId={bug._id}
  comments={comments}
  currentUserId={currentUser._id}
  currentUserName={currentUser.name}
  onAddComment={async (bugId, message) => {
    await commentApi.create({ bugId, authorId: currentUser._id, message });
  }}
  getUserName={(userId) => users.find(u => u._id === userId)?.name || 'Unknown'}
/>
```

### UserSelector
Implements predefined user selection dropdown with role display.

**Features:**
- User dropdown with avatars
- Role badges with color coding
- Persistent selection (localStorage)
- Current user role display
- Integration with UserContext

**Usage:**
```tsx
import { UserSelector } from '@/components';

<UserSelector
  users={allUsers}
  onUserChange={(user) => console.log('Selected user:', user)}
/>
```

## Context

### UserContext
Manages current user state globally across the application.

**Usage:**
```tsx
import { useUser } from '@/contexts/UserContext';

function MyComponent() {
  const { currentUser, setCurrentUser, isLoading } = useUser();
  
  if (isLoading) return <div>Loading...</div>;
  if (!currentUser) return <div>Please select a user</div>;
  
  return <div>Welcome, {currentUser.name}!</div>;
}
```

## ShadCN UI Components

The following ShadCN UI primitives are available in `components/ui/`:
- Avatar
- Badge
- Button
- Card
- ScrollArea
- Select
- Textarea

## Design Principles

- **Minimalist**: Clean, Apple-inspired aesthetic with generous white space
- **Type-safe**: Full TypeScript support with strict mode
- **Accessible**: ARIA-compliant components
- **Responsive**: Mobile-first design approach
- **Consistent**: Unified color palette and spacing system

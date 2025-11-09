/**
 * CommentSection Component
 * 
 * Renders chronological comment threads with author information.
 * Implements comment creation form and displays author data from Collection DB.
 * 
 * Requirements: 4.3, 4.4
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Comment } from '@/utils/types';
import { getInitials } from '@/lib/utils';

interface CommentSectionProps {
  bugId: string;
  comments: Comment[];
  currentUserId: string;
  currentUserName: string;
  onAddComment: (bugId: string, message: string) => Promise<void>;
  getUserName?: (userId: string) => string;
}



/**
 * Format date to relative time
 */
const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  });
};

export const CommentSection: React.FC<CommentSectionProps> = ({
  bugId,
  comments,
  currentUserId,
  currentUserName,
  onAddComment,
  getUserName = () => 'Unknown User',
}) => {
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newComment.trim()) return;

    setIsSubmitting(true);
    try {
      await onAddComment(bugId, newComment.trim());
      setNewComment('');
    } catch (error) {
      console.error('Failed to add comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Sort comments chronologically (oldest first)
  const sortedComments = [...comments].sort(
    (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Comments ({comments.length})
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Comment thread */}
        {sortedComments.length > 0 ? (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-4">
              {sortedComments.map((comment) => {
                const authorName = getUserName(comment.authorId);
                const isCurrentUser = comment.authorId === currentUserId;

                return (
                  <div
                    key={comment._id}
                    className="flex gap-3 pb-4 border-b last:border-b-0"
                  >
                    <Avatar className="size-8 mt-1">
                      <AvatarFallback className="text-xs">
                        {getInitials(authorName)}
                      </AvatarFallback>
                    </Avatar>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline gap-2 mb-1">
                        <span className="font-medium text-sm">
                          {authorName}
                          {isCurrentUser && (
                            <span className="text-muted-foreground font-normal ml-1">
                              (you)
                            </span>
                          )}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatRelativeTime(comment.createdAt)}
                        </span>
                      </div>
                      <p className="text-sm text-foreground whitespace-pre-wrap break-words">
                        {comment.message}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No comments yet. Be the first to comment!</p>
          </div>
        )}

        {/* Comment creation form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex gap-3">
            <Avatar className="size-8 mt-2">
              <AvatarFallback className="text-xs">
                {getInitials(currentUserName)}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1">
              <Textarea
                placeholder="Add a comment..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                disabled={isSubmitting}
                className="min-h-[80px] resize-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setNewComment('')}
              disabled={isSubmitting || !newComment.trim()}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={isSubmitting || !newComment.trim()}
            >
              {isSubmitting ? 'Posting...' : 'Post Comment'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

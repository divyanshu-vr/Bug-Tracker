import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Get initials from a name for avatar fallback
 * Handles edge cases like multiple spaces, leading/trailing spaces
 * 
 * @param name - Full name to extract initials from
 * @returns Up to 2 uppercase initials
 * 
 * @example
 * getInitials("John Doe") // "JD"
 * getInitials("Alice") // "AL"
 * getInitials("Bob  Smith") // "BS" (handles multiple spaces)
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .filter(part => part.length > 0)
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

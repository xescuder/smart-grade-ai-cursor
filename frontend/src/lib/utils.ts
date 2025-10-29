import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Get basic headers for API requests (no authentication needed for single-user app)
 */
export function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
  }
}

/**
 * Get headers for file upload requests
 */
export function getAuthHeadersForFileUpload(): Record<string, string> {
  return {}
}

/**
 * Check if user is authenticated (always true for single-user app)
 */
export function isAuthenticated(): boolean {
  return true
}
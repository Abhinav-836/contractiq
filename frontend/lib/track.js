import { track as vercelTrack } from "@vercel/analytics";

// Analytics must never break the app (ad-blockers, local dev).
export function track(event, props) {
  try {
    vercelTrack(event, props);
  } catch {
    /* ignore */
  }
}
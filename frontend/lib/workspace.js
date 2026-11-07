"use client";

import { useSyncExternalStore } from "react";

/*
 * The workspace the user is looking at, per tab (sessionStorage, like the
 * session itself). Sent to the API as X-Workspace-Id. When nothing is stored
 * the API uses the user's personal workspace.
 */
const KEY = "ciq_workspace";
const listeners = new Set();
const emit = () => listeners.forEach((l) => l());

export function getWorkspaceId() {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function setWorkspaceId(id) {
  try {
    if (id) sessionStorage.setItem(KEY, id);
    else sessionStorage.removeItem(KEY);
  } catch {
    /* storage blocked — falls back to the personal workspace */
  }
  emit();
}

const subscribe = (l) => {
  listeners.add(l);
  return () => listeners.delete(l);
};

/** The stored workspace id; null when none is stored (= personal workspace). */
export function useWorkspaceId() {
  return useSyncExternalStore(subscribe, getWorkspaceId, () => null);
}

export const ROLE_LABELS = { owner: "Owner", admin: "Admin", member: "Member", viewer: "Viewer" };

export const ROLE_HELP = {
  admin: "Can invite people, manage members and delete any contract.",
  member: "Can upload, re-run reviews and update obligations and alerts.",
  viewer: "Can read everything but can't change anything.",
};

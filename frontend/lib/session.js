"use client";

import { useSyncExternalStore } from "react";

/*
 * Signed-in session, kept in sessionStorage (per tab, cleared when the tab
 * closes) under the same keys as the old app so existing tabs stay signed in.
 */
const TOKEN_KEY = "ciq_token";
const USER_KEY = "ciq_user";

const listeners = new Set();
const emit = () => listeners.forEach((l) => l());

let cache = null; // { token, user } | null, memoised so snapshots are stable

function read() {
  if (typeof window === "undefined") return null;
  try {
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (!token) return null;
    const user = JSON.parse(sessionStorage.getItem(USER_KEY) || "null");
    return { token, user };
  } catch {
    return null;
  }
}

function snapshot() {
  const next = read();
  if (cache?.token !== next?.token || JSON.stringify(cache?.user) !== JSON.stringify(next?.user)) cache = next;
  return cache;
}

export function getToken() {
  return read()?.token || null;
}

export function saveSession(token, user) {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    /* storage blocked — the session lasts until reload */
  }
  emit();
}

export function clearSession() {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    sessionStorage.removeItem("auth-storage"); // old app's store
    sessionStorage.removeItem("ciq_workspace"); // selected workspace belongs to this account
  } catch {
    /* ignore */
  }
  emit();
}

const subscribe = (l) => {
  listeners.add(l);
  return () => listeners.delete(l);
};

/** undefined while hydrating on the client, null when signed out. */
export function useSession() {
  return useSyncExternalStore(subscribe, snapshot, () => undefined);
}
"use client";

import { useEffect, useRef, useState } from "react";

/*
 * Google's own "Sign in with Google" button (Google Identity Services).
 * Google shows the account picker; we get back an ID token (a signed JWT)
 * and hand it to onCredential, which posts it to the backend to check.
 * The button is drawn by Google's script, so it always looks the way
 * Google's brand rules require.
 */

const SCRIPT_SRC = "https://accounts.google.com/gsi/client";
let scriptPromise = null;

function loadScript() {
  if (typeof window === "undefined") return Promise.reject(new Error("no window"));
  if (window.google?.accounts?.id) return Promise.resolve();
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = SCRIPT_SRC;
      s.async = true;
      s.defer = true;
      s.onload = () => resolve();
      s.onerror = () => {
        scriptPromise = null; // allow a retry on the next render
        reject(new Error("Couldn't load Google sign-in"));
      };
      document.head.appendChild(s);
    });
  }
  return scriptPromise;
}

export default function GoogleButton({ clientId, text = "continue_with", onCredential, disabled }) {
  const box = useRef(null);
  const handler = useRef(onCredential);
  const [failed, setFailed] = useState(false);
  handler.current = onCredential;

  useEffect(() => {
    if (!clientId) return;
    let cancelled = false;
    loadScript()
      .then(() => {
        if (cancelled || !box.current) return;
        const g = window.google.accounts.id;
        g.initialize({
          client_id: clientId,
          callback: (resp) => resp?.credential && handler.current?.(resp.credential),
          ux_mode: "popup",
          auto_select: false,
          cancel_on_tap_outside: true,
        });
        box.current.innerHTML = "";
        g.renderButton(box.current, {
          type: "standard",
          theme: "outline",
          size: "large",
          text, // signin_with | signup_with | continue_with
          shape: "rectangular",
          logo_alignment: "center",
          // Google allows 200–400 px.
          width: Math.max(200, Math.min(400, Math.round(box.current.offsetWidth || 384))),
        });
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [clientId, text]);

  if (!clientId) return null;
  if (failed) {
    return <p className="text-center text-sm text-faint">Google sign-in couldn't load. Check your connection, or use your email below.</p>;
  }
  return (
    <div className={disabled ? "pointer-events-none opacity-60" : undefined} aria-busy={disabled || undefined}>
      {/* Google draws its button in here. min-h stops the page jumping while it loads. */}
      <div ref={box} className="flex min-h-[44px] w-full justify-center" />
    </div>
  );
}

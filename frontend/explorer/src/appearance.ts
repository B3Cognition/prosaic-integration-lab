export type Appearance = "system" | "light" | "dark";
export const APPEARANCE_KEY = "prosaic.explorer.appearance";

export function readAppearance(): Appearance {
  try {
    const value = window.localStorage.getItem(APPEARANCE_KEY);
    if (value === "light" || value === "dark") return value;
  } catch {
    // Storage can be unavailable in private or restricted browser sessions.
  }
  return "system";
}

export function applyAppearance(preference: Appearance, systemDark: boolean) {
  document.documentElement.dataset.theme =
    preference === "system" ? (systemDark ? "dark" : "light") : preference;
}

export function saveAppearance(preference: Appearance) {
  try {
    window.localStorage.setItem(APPEARANCE_KEY, preference);
  } catch {
    // Switching still works for this session when persistence is unavailable.
  }
}

/**
 * Ambient module declarations for Vite asset imports (the `?url` suffix).
 * The world folder keeps these local: nothing outside `apps/web/src/world/`
 * needs to import binary assets yet.
 */
declare module '*.glb?url' {
  const url: string;
  export default url;
}

declare module '*.svg?url' {
  const url: string;
  export default url;
}

declare module '*.json?url' {
  const url: string;
  export default url;
}

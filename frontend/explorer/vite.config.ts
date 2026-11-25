import { defineConfig } from "vite";
export default defineConfig({
  base: "/",
  build: {
    outDir: "../../lab_runner/explore/web",
    emptyOutDir: true,
    assetsInlineLimit: 0,
  },
});

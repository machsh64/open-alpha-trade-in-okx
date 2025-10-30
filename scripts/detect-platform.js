// scripts/detect-platform.js
const { execSync } = require("child_process");
const os = require("os");

const platform = os.platform();

try {
  if (platform === "win32") {
    console.log("🪟 Detected Windows, running backend with run_dev.bat ...");
    execSync('pnpm run dev:backend:win', { stdio: "inherit", shell: true });
  } else {
    console.log("Detected Linux/macOS, running backend with run_dev.sh ...");
    execSync('pnpm run dev:backend:unix', { stdio: "inherit", shell: true });
  }

  console.log("Starting frontend ...");
  execSync('pnpm run dev:frontend', { stdio: "inherit", shell: true });
} catch (err) {
  console.error("Failed to start project:", err.message);
  process.exit(1);
}

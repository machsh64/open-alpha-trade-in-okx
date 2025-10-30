// scripts/detect-platform.js
const { spawn } = require("child_process");
const os = require("os");
const path = require("path");

const platform = os.platform();
const projectRoot = path.resolve(__dirname, "..");

let backendCmd, backendArgs, frontendCmd, frontendArgs;

if (platform === "win32") {
  console.log("🪟 Detected Windows, starting backend and frontend in parallel...");
  const backendScript = path.join(projectRoot, "backend", "run_dev.bat");
  backendCmd = "cmd";
  backendArgs = ["/c", `"${backendScript}"`];
  frontendCmd = "cmd";
  frontendArgs = ["/c", "pnpm dev"];
} else {
  console.log("🐧 Detected Linux/macOS, starting backend and frontend in parallel...");
  const backendScript = path.join(projectRoot, "backend", "run_dev.sh");
  backendCmd = "bash";
  backendArgs = [backendScript];
  frontendCmd = "pnpm";
  frontendArgs = ["dev"];
}

// 启动后端（不阻塞）
const backend = spawn(backendCmd, backendArgs, {
  stdio: "inherit",
  shell: platform === "win32",
  detached: false,
  cwd: path.join(projectRoot, "backend")
});

// 启动前端（不阻塞）
console.log("🚀 Starting frontend ...");
const frontend = spawn(frontendCmd, frontendArgs, {
  stdio: "inherit",
  shell: false,
  detached: false,
  cwd: path.join(projectRoot, "frontend")
});

// 监听进程退出
backend.on("exit", (code) => {
  console.error(`❌ Backend exited with code ${code}`);
  frontend.kill();
  process.exit(code || 1);
});

frontend.on("exit", (code) => {
  console.error(`❌ Frontend exited with code ${code}`);
  backend.kill();
  process.exit(code || 1);
});

// 优雅退出
process.on("SIGINT", () => {
  console.log("\n🛑 Shutting down...");
  backend.kill();
  frontend.kill();
  process.exit(0);
});

process.on("SIGTERM", () => {
  backend.kill();
  frontend.kill();
  process.exit(0);
});

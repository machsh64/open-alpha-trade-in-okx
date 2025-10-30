const { execSync } = require("child_process");
const { existsSync } = require("fs");
const path = require("path");

const projectRoot = path.resolve("./");
const condaPython = path.join(projectRoot, ".conda", "python.exe");
const backendPath = path.join(projectRoot, "backend");

function run(cmd) {
  console.log(`> ${cmd}`);
  execSync(cmd, { stdio: "inherit", shell: true });
}

function detectConda() {
  try {
    execSync("conda --version", { stdio: "ignore", shell: true });
    return "conda";
  } catch {
    try {
      execSync("micromamba --version", { stdio: "ignore", shell: true });
      return "micromamba";
    } catch {
      return null;
    }
  }
}

try {
  console.log("🚀 Checking Python environment...");

  if (!existsSync(condaPython)) {
    const condaCmd = detectConda();

    if (!condaCmd) {
      console.error("Conda/Micromamba not found! Please install Miniconda first.");
      process.exit(1);
    }

    console.log(`Creating Python env with ${condaCmd} ...`);
    run(`${condaCmd} create -p ./.conda python=3.10 -y`);
    run(`"./.conda/python.exe" -m pip install -U pip uv`);
  }

  console.log("Found project Python at .conda/python.exe");
  console.log("Syncing backend dependencies...");
  run(`cd "${backendPath}" && "${condaPython}" -m uv sync`);

  console.log("Python dependencies synced successfully.");
} catch (err) {
  console.error("Failed to setup Python environment:");
  console.error(err.message);
  process.exit(1);
}

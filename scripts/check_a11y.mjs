import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const server = spawn(process.execPath, ['node_modules/http-server/bin/http-server',
  'public', '-p', '8080', '-s'], { stdio: 'inherit' });
let serverError;
server.on('error', (error) => { serverError = error; });

function waitForExit(child) {
  return new Promise((resolve) => child.once('exit', resolve));
}

async function waitForServer() {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    if (serverError) throw serverError;
    if (server.exitCode !== null) {
      throw new Error(`Static server exited with status ${server.exitCode}`);
    }
    try {
      const response = await fetch('http://127.0.0.1:8080/');
      if (response.ok) return;
    } catch {
      // The server is still starting.
    }
    await delay(250);
  }
  throw new Error('Static server did not become ready within 30 seconds');
}

try {
  await waitForServer();
  const audit = spawn(process.execPath, ['node_modules/pa11y-ci/bin/pa11y-ci.js'],
    { stdio: 'inherit' });
  audit.on('error', (error) => console.error(error));
  const exitCode = await waitForExit(audit);
  if (exitCode !== 0) process.exitCode = exitCode ?? 1;
} catch (error) {
  console.error(error);
  process.exitCode = 1;
} finally {
  if (server.pid && server.exitCode === null) {
    server.kill();
    await waitForExit(server);
  }
}

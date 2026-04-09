"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.DaemonManager = void 0;
const vscode = __importStar(require("vscode"));
const child_process = __importStar(require("child_process"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const fs = __importStar(require("fs"));
class DaemonManager {
    constructor() {
        this.port = 8443;
        this.outputChannel = vscode.window.createOutputChannel("DevReady Daemon");
    }
    async start() {
        // If daemon already reachable, don't spawn a new one
        if (await this.isReachable()) {
            this.outputChannel.appendLine("Daemon already running and reachable, skipping spawn.");
            return true;
        }
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspaceRoot) {
            vscode.window.showErrorMessage("DevReady: No workspace folder found.");
            return false;
        }
        const pythonPath = this.getPythonPath(workspaceRoot);
        this.outputChannel.appendLine(`Starting daemon using: ${pythonPath}`);
        try {
            this.daemonProcess = child_process.spawn(pythonPath, ["-m", "uvicorn", "devready.daemon.main:app", "--host", "127.0.0.1", "--port", this.port.toString()], {
                cwd: workspaceRoot,
                env: { ...process.env, PYTHONPATH: workspaceRoot }
            });
            this.daemonProcess.stdout?.on('data', (data) => {
                this.outputChannel.append(data.toString());
            });
            this.daemonProcess.stderr?.on('data', (data) => {
                this.outputChannel.append(data.toString());
            });
            this.daemonProcess.on('error', (err) => {
                this.outputChannel.appendLine(`Failed to start subprocess: ${err}`);
            });
            this.daemonProcess.on('close', (code) => {
                this.outputChannel.appendLine(`Daemon process exited with code ${code}`);
                this.daemonProcess = undefined;
            });
            // Polling for readiness
            this.outputChannel.appendLine("Waiting for daemon to become reachable...");
            for (let i = 0; i < 10; i++) {
                if (await this.isReachable()) {
                    this.outputChannel.appendLine(`Daemon successfully reached on port ${this.port} after ${i + 1} attempts.`);
                    return true;
                }
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            this.outputChannel.appendLine("Daemon failed to respond in time.");
            return false;
        }
        catch (error) {
            this.outputChannel.appendLine(`Error starting daemon: ${error}`);
            vscode.window.showErrorMessage(`DevReady: Failed to start daemon. ${error}`);
            return false;
        }
    }
    stop() {
        if (this.daemonProcess) {
            this.daemonProcess.kill();
            this.daemonProcess = undefined;
            this.outputChannel.appendLine("Daemon stopped.");
        }
    }
    getPythonPath(workspaceRoot) {
        const isWindows = os.platform() === 'win32';
        // 1. Try .venv
        const venvPath = path.join(workspaceRoot, '.venv', isWindows ? 'Scripts' : 'bin', isWindows ? 'python.exe' : 'python');
        if (fs.existsSync(venvPath)) {
            return venvPath;
        }
        // 2. Try 'py -3' fallback on Windows, then global 'python'
        if (isWindows) {
            try {
                child_process.execSync('py -3 --version', { stdio: 'ignore' });
                return 'py -3';
            }
            catch (e) {
                return 'python';
            }
        }
        return 'python3';
    }
    getBaseUrl() {
        return `http://127.0.0.1:${this.port}`;
    }
    isReachable() {
        return new Promise((resolve) => {
            const req = require('http').request({ hostname: '127.0.0.1', port: this.port, path: '/api/version', method: 'GET' }, (res) => {
                resolve(res.statusCode === 200);
                res.on('data', () => { }); // Consume data to satisfy parser
            });
            req.on('error', () => resolve(false));
            req.setTimeout(500, () => { req.destroy(); resolve(false); });
            req.end();
        });
    }
}
exports.DaemonManager = DaemonManager;
//# sourceMappingURL=DaemonManager.js.map
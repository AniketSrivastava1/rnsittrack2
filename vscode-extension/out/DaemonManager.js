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
class DaemonManager {
    constructor() {
        this.port = 8443;
        this.outputChannel = vscode.window.createOutputChannel("DevReady Daemon");
    }
    async start() {
        if (this.daemonProcess) {
            this.outputChannel.appendLine("Daemon is already running.");
            return true;
        }
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
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
            this.daemonProcess.on('close', (code) => {
                this.outputChannel.appendLine(`Daemon process exited with code ${code}`);
                this.daemonProcess = undefined;
            });
            // Wait a bit to ensure it starts
            await new Promise(resolve => setTimeout(resolve, 2000));
            return true;
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
        const venvPath = path.join(workspaceRoot, '.venv', isWindows ? 'Scripts' : 'bin', isWindows ? 'python.exe' : 'python');
        return venvPath; // Fallback logic can be added here
    }
    getBaseUrl() {
        return `http://127.0.0.1:${this.port}`;
    }
}
exports.DaemonManager = DaemonManager;
//# sourceMappingURL=DaemonManager.js.map
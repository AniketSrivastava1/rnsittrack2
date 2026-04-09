import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';

export class DaemonManager {
    private daemonProcess?: child_process.ChildProcess;
    private outputChannel: vscode.OutputChannel;
    private port: number = 8443;

    constructor() {
        this.outputChannel = vscode.window.createOutputChannel("DevReady Daemon");
    }

    public async start(): Promise<boolean> {
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
            this.daemonProcess = child_process.spawn(
                pythonPath,
                ["-m", "uvicorn", "devready.daemon.main:app", "--host", "127.0.0.1", "--port", this.port.toString()],
                {
                    cwd: workspaceRoot,
                    env: { ...process.env, PYTHONPATH: workspaceRoot }
                }
            );

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
                    this.outputChannel.appendLine(`Daemon successfully reached on port ${this.port} after ${i+1} attempts.`);
                    return true;
                }
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            this.outputChannel.appendLine("Daemon failed to respond in time.");
            return false;

        } catch (error) {
            this.outputChannel.appendLine(`Error starting daemon: ${error}`);
            vscode.window.showErrorMessage(`DevReady: Failed to start daemon. ${error}`);
            return false;
        }
    }

    public stop() {
        if (this.daemonProcess) {
            this.daemonProcess.kill();
            this.daemonProcess = undefined;
            this.outputChannel.appendLine("Daemon stopped.");
        }
    }

    private getPythonPath(workspaceRoot: string): string {
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
            } catch (e) {
                return 'python';
            }
        }
        
        return 'python3';
    }

    public getBaseUrl(): string {
        return `http://127.0.0.1:${this.port}`;
    }

    private isReachable(): Promise<boolean> {
        return new Promise((resolve) => {
            const req = require('http').request(
                { hostname: '127.0.0.1', port: this.port, path: '/api/version', method: 'GET' },
                (res: any) => { 
                    resolve(res.statusCode === 200); 
                    res.on('data', () => {}); // Consume data to satisfy parser
                }
            );
            req.on('error', () => resolve(false));
            req.setTimeout(500, () => { req.destroy(); resolve(false); });
            req.end();
        });
    }
}


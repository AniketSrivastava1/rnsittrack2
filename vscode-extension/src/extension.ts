import * as vscode from 'vscode';
import { DaemonManager } from './DaemonManager';
import { ArchitectClient } from './ArchitectClient';
import { DashboardViewProvider } from './DashboardView';

let daemonManager: DaemonManager;

export async function activate(context: vscode.ExtensionContext) {
    console.log('DevReady extension is now active');

    daemonManager = new DaemonManager();
    const architectClient = new ArchitectClient(daemonManager.getBaseUrl());
    
    // Start daemon on activation
    await daemonManager.start();

    // Register Dashboard Provider
    const dashboardProvider = new DashboardViewProvider(context.extensionUri, architectClient);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(DashboardViewProvider.viewType, dashboardProvider)
    );

    // Register Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('devready.scan', async () => {
            vscode.window.showInformationMessage('Starting DevReady Scan...');
            await dashboardProvider.refresh();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('devready.openDashboard', () => {
            vscode.commands.executeCommand('workbench.view.extension.devready-sidebar');
        })
    );
}

export function deactivate() {
    if (daemonManager) {
        daemonManager.stop();
    }
}

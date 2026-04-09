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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const DaemonManager_1 = require("./DaemonManager");
const ArchitectClient_1 = require("./ArchitectClient");
const DashboardView_1 = require("./DashboardView");
const ProjectRegistry_1 = require("./ProjectRegistry");
let daemonManager;
async function activate(context) {
    console.log('DevReady extension is now active');
    daemonManager = new DaemonManager_1.DaemonManager();
    const architectClient = new ArchitectClient_1.ArchitectClient(daemonManager.getBaseUrl());
    const registry = new ProjectRegistry_1.ProjectRegistry(context);
    // Start daemon on activation
    await daemonManager.start();
    // Register Dashboard Provider
    const dashboardProvider = new DashboardView_1.DashboardViewProvider(context.extensionUri, architectClient, registry);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider(DashboardView_1.DashboardViewProvider.viewType, dashboardProvider));
    // Register Commands
    context.subscriptions.push(vscode.commands.registerCommand('devready.scan', async () => {
        vscode.window.showInformationMessage('Starting DevReady Scan...');
        await dashboardProvider.refresh();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('devready.openDashboard', () => {
        vscode.commands.executeCommand('workbench.view.extension.devready-sidebar');
    }));
}
function deactivate() {
    if (daemonManager) {
        daemonManager.stop();
    }
}
//# sourceMappingURL=extension.js.map
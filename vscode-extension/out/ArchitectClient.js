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
exports.ArchitectClient = void 0;
const http = __importStar(require("http"));
class ArchitectClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    async scan(projectPath, scope = 'full') {
        return this.post('/api/v1/scan', { project_path: projectPath, scope });
    }
    async getLatestSnapshot(projectPath) {
        return this.get(`/api/v1/snapshots/latest?project_path=${encodeURIComponent(projectPath)}`);
    }
    async getVisualizationHtml(snapshotId) {
        const url = new URL(`/api/v1/visualize/dependencies/${snapshotId}`, this.baseUrl);
        return new Promise((resolve, reject) => {
            const req = http.get(url, (res) => {
                let body = '';
                res.on('data', (chunk) => body += chunk);
                res.on('end', () => resolve(body));
            });
            req.on('error', (err) => reject(err));
        });
    }
    async getTeamVisualizationHtml() {
        const url = new URL(`/api/v1/visualize/team`, this.baseUrl);
        return new Promise((resolve, reject) => {
            const req = http.get(url, (res) => {
                let body = '';
                res.on('data', (chunk) => body += chunk);
                res.on('end', () => resolve(body));
            });
            req.on('error', (err) => reject(err));
        });
    }
    async getFixRecommendations(snapshotId, _policy) {
        return this.get(`/api/v1/fixes?snapshot_id=${encodeURIComponent(snapshotId)}`);
    }
    async applyFix(recommendation) {
        return this.post('/api/v1/fixes/apply', recommendation);
    }
    get(path) {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseUrl);
            const options = {
                method: 'GET',
            };
            const req = http.request(url, options, (res) => {
                let body = '';
                res.on('data', (chunk) => body += chunk);
                res.on('end', () => {
                    if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                        resolve(JSON.parse(body));
                    }
                    else if (res.statusCode === 404) {
                        resolve(null);
                    }
                    else {
                        reject(new Error(`API Error: ${res.statusCode} - ${body}`));
                    }
                });
            });
            req.on('error', (err) => reject(err));
            req.end();
        });
    }
    post(path, data) {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseUrl);
            const body = JSON.stringify(data);
            console.log('[DevReady] POST', url.href, body);
            const options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(body),
                }
            };
            const req = http.request(url, options, (res) => {
                let raw = '';
                res.on('data', (chunk) => raw += chunk);
                res.on('end', () => {
                    console.log('[DevReady] POST', url.href, '->', res.statusCode, raw.slice(0, 200));
                    if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                        resolve(JSON.parse(raw));
                    }
                    else {
                        reject(new Error(`API Error: ${res.statusCode} - ${raw}`));
                    }
                });
            });
            req.on('error', (err) => reject(err));
            req.write(body);
            req.end();
        });
    }
}
exports.ArchitectClient = ArchitectClient;
//# sourceMappingURL=ArchitectClient.js.map
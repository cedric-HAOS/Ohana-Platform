// Measure the production renderer on complete Agent API documents, without a DOM.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const {performance} = require('node:perf_hooks');
const source = fs.readFileSync(path.resolve(__dirname,
    '../../../Ohana-Vision/src/ohana_vision/web/static/incidents.js'), 'utf8')
    .replace(/^import .*;$/gm, '').replace('export class', 'class');
const context = vm.createContext({
    escapeHtml: value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;'),
    formatDate: value => String(value),
});
vm.runInContext(source + '\nglobalThis.Controller = IncidentsController;', context);
const controller = Object.create(context.Controller.prototype);
controller.details = new Map();
controller.expandedDetails = new Set();
controller.expandedLogAnomalies = new Set();
controller.state = {topology: {devices: [], nodes: []}};
controller.equipmentLabel = value => value;
controller.serviceLabel = (_node, service) => service;
const documents = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const results = documents.map(incident => {
    controller.details.set(incident.incident_id, incident);
    controller.expandedDetails.add(incident.incident_id);
    const samples = [];
    let html;
    for (let i = 0; i < 110; i++) {
        const start = performance.now();
        html = controller.incidentCard(incident);
        if (i >= 10) samples.push(performance.now() - start);
    }
    samples.sort((a, b) => a - b);
    if (!html.includes('Parcours de l’incident')) throw Error('Dossier absent');
    return {capability: incident.capability_id, events: incident.events.length,
        p95_ms: Number(samples[94].toFixed(2)), html_bytes: Buffer.byteLength(html)};
});
process.stdout.write(JSON.stringify(results));

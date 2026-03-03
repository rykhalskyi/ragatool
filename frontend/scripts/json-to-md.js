const fs = require('fs');

function getTestId(selectors) {
    if (!selectors || selectors.length === 0) return null;
    
    for (const selectorGroup of selectors) {
        for (const selector of selectorGroup) {
            const match = selector.match(/\[data-testid='([^']+)'\]/);
            if (match) return match[1];
        }
    }
    return null;
}

function formatAction(step) {
    const { type, value, selectors } = step;
    
    const testId = getTestId(selectors);
    const fallbackSelector = selectors && selectors[0] ? selectors[0][0] : '';
    const target = testId || fallbackSelector;

    switch (type) {
        case 'click':
            return `- click '${target}'`;
        case 'change':
            return `- input to '${target}' '${value}'`;
        case 'keyUp':
            return null;
        case 'setViewport':
            return null;
        case 'navigate':
            return `- navigate to '${step.url}'`;
        default:
            return `- ${type} '${target}'`;
    }
}

function transformJsonToMd(jsonPath, outputPath) {
    const jsonContent = fs.readFileSync(jsonPath, 'utf-8');
    const data = JSON.parse(jsonContent);
    
    let md = `# ${data.title}\n\n`;
    
    data.steps.forEach((step, index) => {
        const action = formatAction(step);
        if (action) {
            md += `${action}\n`;
        }
    });
    
    fs.writeFileSync(outputPath, md, 'utf-8');
    console.log(`Output written to: ${outputPath}`);
}

const jsonPath = process.argv[2] || './e2e/scenarios/2_step_import_recording.json';
const outputPath = process.argv[3] || './e2e/scenarios/2_step_import_recording.md';

transformJsonToMd(jsonPath, outputPath);

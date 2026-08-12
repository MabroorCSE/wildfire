#!/usr/bin/env node

const fs = require("fs");

function parseCsv(path) {
    const lines = fs.readFileSync(path, "utf8").trim().split("\n");
    const headers = lines[0].split(",");
    return lines.slice(1).map((line) => {
        const values = line.split(",");
        const row = {};
        headers.forEach((header, i) => {
            row[header] = values[i];
        });
        return row;
    });
}

function loadTotalCellCount(configPath) {
    const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
    return Object.keys(config.cells).filter((cellId) => cellId !== "default").length;
}

function loadIndependentPercentSeries(cellsCsvPath, totalCells) {
    const ignitedByCell = new Map();
    const series = []; // [{ simtime, percent }]

    for (const row of parseCsv(cellsCsvPath)) {
        const cellId = `${row.x},${row.y}`;
        ignitedByCell.set(cellId, row.ignited === "1");
        const simtime = parseFloat(row.simtime);
        let ignitedCount = 0;
        for (const ignited of ignitedByCell.values()) {
            if (ignited) ignitedCount++;
        }
        const percent = (100.0 * ignitedCount) / totalCells;
        series.push({ simtime, percent });
    }

    return series;
}

function loadModelPercentSeries(avgCsvPath) {
    const series = [];
    let previousValue = null;

    for (const row of parseCsv(avgCsvPath)) {
        const value = parseFloat(row.percentCellsIgnited);
        if (value !== previousValue) {
            series.push({ time: parseFloat(row.time), percent: value });
            previousValue = value;
        }
    }

    return series;
}

// Step-function lookup: value in effect at targetTime (last known value at or before it).
function independentPercentAt(series, targetTime) {
    let value = 0.0;
    for (const { simtime, percent } of series) {
        if (simtime > targetTime) break;
        value = percent;
    }
    return value;
}

function main() {
    const [, , configPath, cellsCsvPath, avgCsvPath, toleranceArg] = process.argv;
    if (!configPath || !cellsCsvPath || !avgCsvPath) {
        console.log(
            "Usage: node scripts/validate_percent_ignited.js <config.json> <cells_output.csv> <avg_output.csv> [tolerance_percent]"
        );
        process.exit(1);
    }
    const tolerance = toleranceArg ? parseFloat(toleranceArg) : 0.05;

    const totalCells = loadTotalCellCount(configPath);
    const independentSeries = loadIndependentPercentSeries(cellsCsvPath, totalCells);
    let modelSeries = loadModelPercentSeries(avgCsvPath);

    if (modelSeries.length && modelSeries[0].time === 0) {
        modelSeries = modelSeries.slice(1);
    }

    console.log(`Total cells in grid (from config): ${totalCells}`);
    console.log(`Model samples to check: ${modelSeries.length}`);
    console.log(`Tolerance: ${tolerance} percentage points\n`);

    let worstDiff = 0.0;
    const failures = [];
    for (const { time, percent: modelPercent } of modelSeries) {
        const independentPercent = independentPercentAt(independentSeries, time);
        const diff = Math.abs(modelPercent - independentPercent);
        worstDiff = Math.max(worstDiff, diff);
        if (diff > tolerance) {
            failures.push({ time, modelPercent, independentPercent, diff });
        }
    }

    console.log(`Worst difference observed: ${worstDiff.toFixed(4)} percentage points`);

    if (failures.length) {
        console.log(`\nFAIL: ${failures.length} sample(s) exceed tolerance:`);
        for (const { time, modelPercent, independentPercent, diff } of failures.slice(0, 20)) {
            console.log(
                `  t=${time.toFixed(1)}  model=${modelPercent.toFixed(4)}%  independent=${independentPercent.toFixed(4)}%  diff=${diff.toFixed(4)}`
            );
        }
        process.exit(1);
    } else {
        console.log("\nPASS: atomic model output matches the independent count at every sample.");
    }
}

main();

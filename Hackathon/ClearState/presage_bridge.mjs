import {
  cardioMetrics,
  decodeMetrics,
  faceMetrics,
  ProcessingStatus,
  SmartSpectraSDK,
} from '@smartspectra/node-sdk';

const live = process.argv.includes('--live');

if (!live) {
  console.log(`SmartSpectra native SDK loaded (version ${SmartSpectraSDK.version}).`);
  process.exit(0);
}

const apiKey = process.env.SMARTSPECTRA_API_KEY;
if (!apiKey) {
  console.error('SMARTSPECTRA_API_KEY is missing.');
  process.exit(2);
}

const sdk = new SmartSpectraSDK({
  apiKey,
  enableTelemetry: false,
  requestedMetrics: [...cardioMetrics, ...faceMetrics],
});
let shuttingDown = false;
let lastMetricsAt = 0;
let lastValidation = '';

const expressionNames = {
  0: 'unspecified',
  1: 'angry',
  2: 'contempt',
  3: 'disgust',
  4: 'fear',
  5: 'happy',
  6: 'neutral',
  7: 'sad',
  8: 'surprise',
};

function emit(event) {
  process.stdout.write(`${JSON.stringify(event)}\n`);
}

function latest(items) {
  return items?.length ? items[items.length - 1] : null;
}

function measurement(item) {
  if (!item) return null;
  return {
    value: item.value ?? null,
    confidence: item.confidence ?? null,
    stable: item.stable ?? null,
    timestamp_us: item.timestamp == null ? null : String(item.timestamp),
  };
}

function detection(item) {
  if (!item) return null;
  return {
    detected: item.detected ?? null,
    stable: item.stable ?? null,
    timestamp_us: item.timestamp == null ? null : String(item.timestamp),
  };
}

function faceData(face) {
  if (!face) return null;
  const landmarks = latest(face.landmarks);
  const expression = latest(face.expression);
  return {
    blinking: detection(latest(face.blinking)),
    talking: detection(latest(face.talking)),
    expression: expression ? {
      stable: expression.stable ?? null,
      timestamp_us: expression.timestamp == null ? null : String(expression.timestamp),
      scores: (expression.scores ?? []).map((score) => ({
        type: expressionNames[score.type] ?? String(score.type),
        confidence: score.confidence,
      })),
    } : null,
    landmarks: landmarks ? {
      stable: landmarks.stable ?? null,
      reset: landmarks.reset ?? null,
      timestamp_us: landmarks.timestamp == null ? null : String(landmarks.timestamp),
      points: (landmarks.value ?? []).map(({ x, y }) => ({ x, y })),
    } : null,
  };
}

function metricsData(buffer, timestampUs) {
  const metrics = decodeMetrics(buffer);
  return {
    type: 'metrics',
    timestamp_us: String(timestampUs),
    pulse_rate: measurement(latest(metrics.cardio?.pulseRate)),
    arterial_pressure_trace: measurement(latest(metrics.cardio?.arterialPressureTrace)),
    hrv: latest(metrics.cardio?.hrv) ?? null,
    face: faceData(metrics.face),
  };
}

async function shutdown(exitCode) {
  if (shuttingDown) return;
  shuttingDown = true;
  process.exitCode = exitCode;
  try {
    await sdk.stopAsync();
  } catch {
    // A failed or not-yet-started session may already be stopped.
  }
  try {
    await sdk.destroy();
  } catch (error) {
    console.error(`Shutdown failed: ${error.message}`);
    process.exitCode = 1;
  }
}

sdk.on('processingStatus', (status) => {
  const name = Object.keys(ProcessingStatus).find((key) => ProcessingStatus[key] === status);
  emit({ type: 'status', status: name ?? String(status) });
  if (status === ProcessingStatus.kError) void shutdown(1);
});
sdk.on('validationStatus', (code, timestampUs, hint) => {
  const validation = `${code}:${hint}`;
  if (validation === lastValidation) return;
  lastValidation = validation;
  emit({ type: 'validation', code, timestamp_us: String(timestampUs), hint });
});
sdk.on('metrics', (buffer, timestampUs) => {
  const now = Date.now();
  if (now - lastMetricsAt < 1000) return;
  lastMetricsAt = now;
  try {
    emit(metricsData(buffer, timestampUs));
  } catch (error) {
    emit({ type: 'decode_error', message: error.message });
  }
});
sdk.on('error', (code, message, retryable) => {
  emit({ type: 'error', code, message, retryable });
  void shutdown(1);
});

try {
  sdk.useCamera();
  sdk.start();
  emit({ type: 'started', version: SmartSpectraSDK.version });
} catch (error) {
  emit({ type: 'error', message: error.message });
  await shutdown(1);
}

process.once('SIGINT', async () => {
  await shutdown(0);
});
process.once('SIGBREAK', async () => {
  await shutdown(0);
});
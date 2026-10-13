const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;
    const emit = (name, sink) => (...args) => {
        if (LEVELS[name] >= threshold) sink(`[${new Date().toISOString()}] ${name.toUpperCase()}`, ...args);
    };
    return {
        debug: emit('debug', console.debug),
        info: emit('info', console.info),
        warn: emit('warn', console.warn),
        error: emit('error', console.error),
    };
}

module.exports = { createLogger };

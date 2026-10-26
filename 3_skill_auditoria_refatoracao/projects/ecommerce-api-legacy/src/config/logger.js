const LEVELS = { debug: 10, info: 20, warn: 30, error: 40, silent: 100 };
const threshold = LEVELS[process.env.LOG_LEVEL] || LEVELS.info;

function write(level, message, ...args) {
    if (LEVELS[level] < threshold) return;
    const line = `${new Date().toISOString()} ${level.toUpperCase()} ${message}`;
    (level === 'error' ? console.error : console.log)(line, ...args);
}

module.exports = {
    info: (message, ...args) => write('info', message, ...args),
    warn: (message, ...args) => write('warn', message, ...args),
    error: (message, ...args) => write('error', message, ...args),
};

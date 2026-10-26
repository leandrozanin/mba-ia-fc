const logger = require('./logger');

function loadConfig(overrides = {}) {
    const config = {
        port: Number(process.env.PORT || 3000),
        databaseFile: process.env.DATABASE_FILE || ':memory:',
        paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || null,
        adminApiToken: process.env.ADMIN_API_TOKEN || null,
        seedUserPassword: process.env.SEED_USER_PASSWORD || null,
        ...overrides,
    };

    if (!config.paymentGatewayKey) {
        logger.warn('PAYMENT_GATEWAY_KEY não definida; usando apenas o gateway simulado.');
    }
    if (!config.adminApiToken) {
        logger.warn('ADMIN_API_TOKEN não definida; rotas administrativas ficam bloqueadas.');
    }
    return config;
}

module.exports = { loadConfig };

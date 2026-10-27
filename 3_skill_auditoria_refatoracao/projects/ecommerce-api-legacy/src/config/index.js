const DEFAULT_PORT = 3000;

function loadConfig(env = process.env) {
    const adminToken = env.ADMIN_TOKEN;
    if (!adminToken) {
        throw new Error('Variável de ambiente ADMIN_TOKEN é obrigatória');
    }

    const port = env.PORT ? Number(env.PORT) : DEFAULT_PORT;
    if (!Number.isInteger(port) || port < 0) {
        throw new Error('PORT deve ser um inteiro não negativo');
    }

    return {
        port,
        adminToken,
        dbFile: env.DB_FILE || ':memory:',
        paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || null,
    };
}

module.exports = { loadConfig };

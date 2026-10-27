const express = require('express');
const { loadConfig } = require('./config');
const Database = require('./db/database');
const { initSchema, seed } = require('./db/schema');
const { createPaymentGateway } = require('./services/paymentGateway');
const { createCheckoutService } = require('./services/checkoutService');
const { createReportService } = require('./services/reportService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createAdminAuth } = require('./middlewares/adminAuth');
const { errorHandler } = require('./middlewares/errorHandler');
const { createRouter } = require('./routes');

// Composition root: monta as dependências e devolve o app Express sem iniciar o servidor.
function createApp({ db, config }) {
    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey });

    const app = express();
    app.use(express.json());
    app.use(createRouter({
        adminAuth: createAdminAuth({ adminToken: config.adminToken }),
        checkoutController: createCheckoutController({
            checkoutService: createCheckoutService({ db, paymentGateway }),
        }),
        reportController: createReportController({ reportService: createReportService({ db }) }),
        userController: createUserController({ db }),
    }));
    app.use(errorHandler);
    return app;
}

async function createDatabase(filename) {
    const db = await Database.open(filename);
    await initSchema(db);
    await seed(db);
    return db;
}

async function main() {
    const config = loadConfig();
    const db = await createDatabase(config.dbFile);
    createApp({ db, config }).listen(config.port, () => {
        console.log(`LMS API rodando na porta ${config.port}...`);
    });
}

if (require.main === module) {
    main().catch((err) => {
        console.error(`[FATAL] ${err.message}`);
        process.exit(1);
    });
}

module.exports = { createApp, createDatabase };

// Composition root: monta config, banco, models, controllers, rotas e middlewares.
const express = require('express');
const { loadConfig } = require('./config');
const logger = require('./config/logger');
const { Database } = require('./db/database');
const { seed } = require('./db/seed');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createSimulatedGateway } = require('./services/paymentGateway');
const { createRouter } = require('./views/routes');
const { errorHandler } = require('./middlewares/errorHandler');

async function createApp({ config = loadConfig(), paymentGateway = createSimulatedGateway() } = {}) {
    const db = new Database(config.databaseFile);
    await db.migrate();
    await seed(db, config);

    const users = createUserModel(db);
    const courses = createCourseModel(db);
    const enrollments = createEnrollmentModel(db);

    const app = express();
    app.use(express.json());
    app.use(createRouter({
        checkout: createCheckoutController({ db, users, courses, enrollments, paymentGateway }),
        reports: createReportController({ courses }),
        users: createUserController({ db, users, enrollments }),
        config,
    }));
    app.use(errorHandler);

    return { app, db, config };
}

if (require.main === module) {
    createApp()
        .then(({ app, config }) => {
            app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
        })
        .catch((err) => {
            logger.error(`Falha ao iniciar: ${err.message}`);
            process.exit(1);
        });
}

module.exports = { createApp };

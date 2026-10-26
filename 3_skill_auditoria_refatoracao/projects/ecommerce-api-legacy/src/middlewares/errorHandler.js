const logger = require('../config/logger');
const { AppError } = require('../errors');

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
    if (err instanceof AppError) return res.status(err.status).send(err.message);
    if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');

    logger.error(`Erro inesperado em ${req.method} ${req.path}: ${err.message}`);
    return res.status(500).send('Erro interno');
}

module.exports = { errorHandler };

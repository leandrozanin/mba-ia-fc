const { AppError } = require('../errors');

// O Express identifica o error handler pela aridade 4, então `next` precisa existir.
function errorHandler(err, req, res, next) {
    if (err instanceof AppError) {
        return res.status(err.status).send(err.message);
    }
    // JSON malformado no corpo da requisição (express.json).
    if (err.type === 'entity.parse.failed') {
        return res.status(400).send('Bad Request');
    }
    console.error(`[ERROR] ${req.method} ${req.path}: ${err.message}`);
    res.status(500).send('Erro DB');
}

module.exports = { errorHandler };

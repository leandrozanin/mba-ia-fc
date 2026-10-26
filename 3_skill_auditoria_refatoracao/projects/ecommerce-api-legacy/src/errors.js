class AppError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

// Mensagens em texto puro, como no contrato original da API.
const badRequest = (message = 'Bad Request') => new AppError(400, message);
const unauthorized = (message = 'Não autorizado') => new AppError(401, message);
const forbidden = (message) => new AppError(403, message);
const notFound = (message) => new AppError(404, message);
const conflict = (message) => new AppError(409, message);

module.exports = { AppError, badRequest, unauthorized, forbidden, notFound, conflict };

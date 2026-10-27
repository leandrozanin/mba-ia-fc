// Erros esperados carregam o status e o corpo de texto do contrato HTTP legado.
class AppError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor() {
        super(400, 'Bad Request');
    }
}

class NotFoundError extends AppError {
    constructor(message) {
        super(404, message);
    }
}

class PaymentDeniedError extends AppError {
    constructor() {
        super(400, 'Pagamento recusado');
    }
}

class UnauthorizedError extends AppError {
    constructor() {
        super(401, 'Unauthorized');
    }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentDeniedError, UnauthorizedError };

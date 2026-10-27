const { PAYMENT_STATUS } = require('../models/paymentModel');

// Gateway simulado: mantém a regra legada em que cartões iniciados por "4"
// são aprovados. A chave do gateway nunca é registrada em log.
const APPROVED_CARD_PREFIX = '4';

function createPaymentGateway({ apiKey } = {}) {
    return {
        apiKey,
        async charge({ cardNumber }) {
            return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { createPaymentGateway };

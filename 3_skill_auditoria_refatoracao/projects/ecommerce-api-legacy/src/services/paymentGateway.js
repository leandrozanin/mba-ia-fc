const PAYMENT_STATUS = { PAID: 'PAID', DENIED: 'DENIED' };
const APPROVED_CARD_PREFIX = '4';

/** Gateway simulado: aprova cartões iniciados em 4. Substituível por um real via injeção. */
function createSimulatedGateway() {
    return {
        async charge({ cardNumber }) {
            return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { PAYMENT_STATUS, createSimulatedGateway };

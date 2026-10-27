const { ValidationError } = require('../errors');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_PATTERN = /^\d{12,19}$/;

function isNonEmptyString(value) {
    return typeof value === 'string' && value.trim() !== '';
}

function parsePositiveInt(value) {
    const text = typeof value === 'number' ? String(value) : value;
    if (typeof text !== 'string' || !/^[1-9]\d*$/.test(text)) throw new ValidationError();
    return Number(text);
}

// Valida o payload legado de checkout (campos usr, eml, pwd, c_id, card).
function parseCheckoutInput(body = {}) {
    const { usr, eml, pwd, c_id: courseId, card } = body;
    if (!isNonEmptyString(usr) || !isNonEmptyString(eml) || !EMAIL_PATTERN.test(eml)) throw new ValidationError();
    if (typeof card !== 'string' || !CARD_PATTERN.test(card)) throw new ValidationError();
    if (pwd !== undefined && !isNonEmptyString(pwd)) throw new ValidationError();

    return {
        name: usr.trim(),
        email: eml.trim(),
        password: pwd,
        courseId: parsePositiveInt(courseId),
        cardNumber: card,
    };
}

module.exports = { parseCheckoutInput, parsePositiveInt };

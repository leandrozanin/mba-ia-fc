const { badRequest } = require('../errors');

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const CARD_PATTERN = /^\d{13,19}$/;

const isText = (value) => typeof value === 'string' && value.trim() !== '';

/** Valida o corpo do checkout mantendo os nomes de campo do contrato (usr, eml, pwd, c_id, card). */
function parseCheckout(body) {
    const { usr, eml, pwd, c_id: courseId, card } = body || {};
    if (!usr || !eml || !courseId || !card) throw badRequest();

    const id = Number(courseId);
    if (!isText(usr) || !EMAIL_PATTERN.test(String(eml)) || !Number.isInteger(id) || id <= 0) throw badRequest();
    if (typeof card !== 'string' || !CARD_PATTERN.test(card)) throw badRequest('Cartão inválido');
    if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') throw badRequest();

    return { name: usr.trim(), email: eml, password: pwd || null, courseId: id, cardNumber: card };
}

function parseId(value) {
    const id = Number(value);
    if (!Number.isInteger(id) || id <= 0) throw badRequest('Id inválido');
    return id;
}

module.exports = { parseCheckout, parseId };

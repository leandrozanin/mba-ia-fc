const crypto = require('crypto');
const { forbidden, unauthorized } = require('../errors');

function tokensMatch(expected, received) {
    const a = Buffer.from(expected);
    const b = Buffer.from(String(received || ''));
    return a.length === b.length && crypto.timingSafeEqual(a, b);
}

/** Protege rotas administrativas com o token configurado em ADMIN_API_TOKEN. */
function adminAuth(adminApiToken) {
    return (req, res, next) => {
        if (!adminApiToken) return next(forbidden('Rotas administrativas desabilitadas'));
        if (!tokensMatch(adminApiToken, req.get('x-admin-token'))) return next(unauthorized());
        return next();
    };
}

module.exports = { adminAuth };

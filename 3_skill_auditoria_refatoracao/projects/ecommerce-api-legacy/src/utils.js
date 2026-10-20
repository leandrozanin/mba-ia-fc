const config = Object.freeze({
  port: Number(process.env.PORT || 3000),
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  smtpUser: process.env.SMTP_USER || '',
});
const cache = new Map();
function logAndCache(key, data) { cache.set(key, data); }
function hashPassword(password) {
  const crypto = require('node:crypto');
  const salt = crypto.randomBytes(16).toString('hex');
  const digest = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${digest}`;
}
module.exports = { config, logAndCache, hashPassword, cache };

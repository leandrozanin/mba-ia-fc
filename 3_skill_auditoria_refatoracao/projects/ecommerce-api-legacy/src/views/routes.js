const express = require('express');
const { adminAuth } = require('../middlewares/adminAuth');

// Express 4 não propaga rejeições de handlers async; encaminha ao error handler.
const handle = (fn) => (req, res, next) => fn(req, res).catch(next);

function createRouter({ checkout, reports, users, config }) {
    const router = express.Router();
    const requireAdmin = adminAuth(config.adminApiToken);

    router.post('/api/checkout', handle(async (req, res) => {
        res.status(200).json(await checkout.checkout(req.body));
    }));

    router.get('/api/admin/financial-report', requireAdmin, handle(async (req, res) => {
        res.json(await reports.financialReport());
    }));

    router.delete('/api/users/:id', requireAdmin, handle(async (req, res) => {
        res.json(await users.remove(req.params.id));
    }));

    return router;
}

module.exports = { createRouter };

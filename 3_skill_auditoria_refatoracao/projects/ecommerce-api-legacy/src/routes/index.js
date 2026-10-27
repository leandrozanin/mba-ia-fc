const express = require('express');

// Express 4 não encaminha rejeições de handlers async para o error handler.
const asyncHandler = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);

function createRouter({ adminAuth, checkoutController, reportController, userController }) {
    const router = express.Router();

    router.post('/api/checkout', asyncHandler(checkoutController.create));
    router.get('/api/admin/financial-report', adminAuth, asyncHandler(reportController.financial));
    router.delete('/api/users/:id', adminAuth, asyncHandler(userController.remove));

    return router;
}

module.exports = { createRouter };

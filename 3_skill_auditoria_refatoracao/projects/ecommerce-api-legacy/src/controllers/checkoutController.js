const { parseCheckoutInput } = require('./validation');

function createCheckoutController({ checkoutService }) {
    return {
        async create(req, res) {
            const input = parseCheckoutInput(req.body);
            const { enrollmentId } = await checkoutService.checkout(input);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };

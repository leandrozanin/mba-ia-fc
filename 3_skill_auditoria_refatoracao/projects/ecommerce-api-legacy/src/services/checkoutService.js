const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const { hashPassword } = require('./passwordHasher');
const { NotFoundError, PaymentDeniedError, ValidationError } = require('../errors');

function createCheckoutService({ db, paymentGateway }) {
    async function checkout({ name, email, password, courseId, cardNumber }) {
        const course = await courseModel.findActiveById(db, courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const existingUser = await userModel.findByEmail(db, email);
        if (!existingUser && !password) throw new ValidationError();

        // O pagamento é decidido antes de qualquer escrita: recusas não deixam dados.
        const status = await paymentGateway.charge({ cardNumber, amount: course.price });
        if (status !== paymentModel.PAYMENT_STATUS.PAID) throw new PaymentDeniedError();

        const passwordHash = existingUser ? null : await hashPassword(password);

        return db.transaction(async (tx) => {
            const user = await userModel.findByEmail(tx, email);
            if (!user && !passwordHash) throw new ValidationError();
            const userId = user ? user.id : await userModel.create(tx, { name, email, passwordHash });
            const enrollmentId = await enrollmentModel.create(tx, { userId, courseId: course.id });
            await paymentModel.create(tx, { enrollmentId, amount: course.price, status });
            await auditLogModel.record(tx, `Checkout curso ${course.id} por ${userId}`);
            return { enrollmentId };
        });
    }

    return { checkout };
}

module.exports = { createCheckoutService };

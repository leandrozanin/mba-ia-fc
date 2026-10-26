const logger = require('../config/logger');
const { badRequest, conflict, notFound, unauthorized } = require('../errors');
const { PAYMENT_STATUS } = require('../services/paymentGateway');
const { hashPassword, verifyPassword } = require('../services/passwordHasher');
const { parseCheckout } = require('./validators');

function createCheckoutController({ db, users, courses, enrollments, paymentGateway }) {
    async function resolveBuyer({ name, email, password }) {
        const existing = await users.findActiveByEmail(email);
        if (existing) {
            // Comprar em nome de uma conta existente exige a senha dela.
            if (!password || !verifyPassword(password, existing.pass)) throw unauthorized('Credenciais inválidas');
            return { userId: existing.id, newUser: null };
        }
        if (!password) throw badRequest('Senha obrigatória para novo usuário');
        return { userId: null, newUser: { name, email, passwordHash: hashPassword(password) } };
    }

    return {
        async checkout(body) {
            const input = parseCheckout(body);

            const course = await courses.findActive(input.courseId);
            if (!course) throw notFound('Curso não encontrado');

            const buyer = await resolveBuyer(input);
            if (buyer.userId && (await enrollments.exists(buyer.userId, course.id))) {
                throw conflict('Aluno já matriculado neste curso');
            }

            // Pagamento é decidido antes de qualquer escrita: recusa não deixa usuário órfão.
            const status = await paymentGateway.charge({ cardNumber: input.cardNumber, amount: course.price });
            logger.info(`Pagamento ${status} para curso ${course.id} (cartão final ${input.cardNumber.slice(-4)})`);
            if (status !== PAYMENT_STATUS.PAID) throw badRequest('Pagamento recusado');

            const enrollmentId = await db.transaction(async (tx) => {
                const userId = buyer.userId || (await users.create(tx, buyer.newUser));
                const id = await enrollments.create(tx, { userId, courseId: course.id });
                await enrollments.recordPayment(tx, { enrollmentId: id, amount: course.price, status });
                await enrollments.audit(tx, `Checkout curso ${course.id} por ${userId}`);
                return id;
            }).catch((err) => {
                // Corrida entre checkouts simultâneos: UNIQUE de e-mail ou matrícula.
                if (err.code === 'SQLITE_CONSTRAINT') throw conflict('Aluno já matriculado neste curso');
                throw err;
            });

            return { msg: 'Sucesso', enrollment_id: enrollmentId };
        },
    };
}

module.exports = { createCheckoutController };

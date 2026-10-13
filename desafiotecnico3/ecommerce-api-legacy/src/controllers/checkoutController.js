const { AppError } = require('../utils/errors');
const { isNonEmptyString, isEmail, toPositiveInt } = require('../utils/validation');

function parseCheckout(body) {
    const { usr: name, eml: email, pwd: password, c_id: rawCourseId, card: cardNumber } = body || {};
    const courseId = toPositiveInt(rawCourseId);
    const valid = isNonEmptyString(name)
        && isEmail(email)
        && isNonEmptyString(cardNumber)
        && courseId !== null
        && (password === undefined || password === null || typeof password === 'string');
    if (!valid) throw new AppError('Bad Request', 400);
    return { name, email, password: password || null, courseId, cardNumber };
}

class CheckoutController {
    constructor({ checkoutService }) { this.checkoutService = checkoutService; }

    checkout = async (req, res) => {
        const { enrollmentId } = await this.checkoutService.checkout(parseCheckout(req.body));
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    };
}

module.exports = CheckoutController;

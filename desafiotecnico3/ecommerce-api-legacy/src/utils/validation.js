const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

const isEmail = (value) => isNonEmptyString(value) && EMAIL_PATTERN.test(value);

// Aceita inteiro ou string só com dígitos (ex.: parâmetro de rota); devolve null se inválido.
const toPositiveInt = (value) => {
    const number = typeof value === 'string' && /^\d+$/.test(value) ? Number(value) : value;
    return Number.isInteger(number) && number > 0 ? number : null;
};

module.exports = { isNonEmptyString, isEmail, toPositiveInt };

const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

module.exports = (controller, requireAdmin) => express.Router()
    .delete('/api/users/:id', requireAdmin, asyncHandler(controller.remove));

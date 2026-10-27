function createReportController({ reportService }) {
    return {
        async financial(req, res) {
            res.json(await reportService.financialReport());
        },
    };
}

module.exports = { createReportController };

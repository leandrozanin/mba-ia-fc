class AppError(Exception):
    """Erro de aplicação com status HTTP e campos extras do contrato original."""

    status_code = 500

    def __init__(self, mensagem, **extra):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.extra = extra

    def to_dict(self):
        return {"erro": self.mensagem, **self.extra}


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409

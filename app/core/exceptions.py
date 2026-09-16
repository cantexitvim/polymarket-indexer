class AppError(Exception):
    pass


class DomainError(AppError):
    pass


class WalletNotFoundError(DomainError):
    pass

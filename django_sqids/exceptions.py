class ConfigError(Exception):
    pass


class RealFieldDoesNotExistError(ConfigError):
    pass


class IncorrectPrefixError(ConfigError):
    pass

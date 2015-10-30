import raspi_mon_sys.MailLoggerClient as MailLoggerClient

logger = MailLoggerClient.open()

logger.config(logger.levels.DEBUG, logger.schedules.INSTANTANEOUSLY)

logger.debug("Debug test 1")

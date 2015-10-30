import raspi_mon_sys.MailLoggerClient as MailLoggerClient

logger = MailLoggerClient.open()

logger.config(logger.levels.DEBUG, logger.schedules.INSTANTANEOUSLY)
logger.config(logger.levels.INFO, logger.schedules.HOURLY)

logger.debug("Debug test 1")
logger.info("Info test 1")

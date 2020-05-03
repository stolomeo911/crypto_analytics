import logging
import datetime as dt
import configparser
import os

logger = logging.getLogger(__name__)

__all__ = ["Configuration"]


class Configuration:

    __shared_state = {}

    AS_OF_DATE_FORMAT = "%Y%m%d"
    GEN_DATE_FORMAT = "%Y%m%d_%H%M%S"
    AS_OF_DATE = "asofdate"
    EXECUTION_ID = "executionid"
    LOG = "LOG"

    def __init__(self, configuration_file, as_of_date=dt.datetime.now().date()):
        if self.__shared_state == {}:
            self.as_of_date = as_of_date
            run_id = dt.datetime.now().strftime(self.GEN_DATE_FORMAT)

            defaults = {self.AS_OF_DATE: as_of_date.strftime(self.AS_OF_DATE_FORMAT),
                        self.EXECUTION_ID: run_id}
            config = configparser.ConfigParser(defaults=defaults,
                                               interpolation=configparser.ExtendedInterpolation())
            config.read(configuration_file)
            self.__config = config
            Configuration.__shared_state = self.__dict__
            logger.debug("Configuration Manager have been instantiated")
        else:
            self.__dict__ = self.__shared_state
            logger.debug("Configuration Manager have been retrieved")

    def get_config(self):
        return self.__config

    def get(self, section, option):
        return self.__config.get(section, option)

    def getboolean(self, section, option):
        return self.__config.getboolean(section, option)

    def getint(self, section, option):
        return self.__config.getint(section, option)

    def getfloat(self, section, option):
        return self.__config.getfloat(section, option)

    def getlist(self, section, option):
        return self.__config.get(section, option).split(",")

    def enhanced_get(self, section, option):
        try:
            return self.getfloat(section, option)
        except ValueError:
            pass
        try:
            return self.getint(section, option)
        except ValueError:
            pass
        try:
            return self.getboolean(section, option)
        except ValueError:
            return self.get(section, option)

    def get_composite_option(self, section, prefix, *args):
        option = ".".join(list(args))
        return self.enhanced_get(section, prefix + "." + option)

    @staticmethod
    def log_config(config):
        run_id = config.defaults()[Configuration.EXECUTION_ID]
        output_file = config.get("PATH", "paths.logpath") + "/" + run_id + ".log"
        activate_log = config.getboolean(Configuration.LOG, "logging.activate")
        activate_log_stream = config.getboolean(Configuration.LOG, "logging.streamhandler.activate")
        activate_log_file = config.getboolean(Configuration.LOG, "logging.filehandler.activate")
        root_logger = logging.getLogger()
        root_logger.handlers = []
        if not activate_log:
            pass
        else:
            root_logger.setLevel(logging.DEBUG)
            if activate_log_stream:
                formatter = logging.Formatter('%(levelname)s | %(name)s | %(message)s')
                handler = logging.StreamHandler()
                stream_handler_level = config.get("LOG", "logging.streamhandler.level")
                handler.setLevel(getattr(logging, stream_handler_level))
                handler.setFormatter(formatter)
                root_logger.addHandler(handler)
            if activate_log_file:
                formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
                try:
                    handler = logging.FileHandler(output_file, "w")
                except FileNotFoundError:
                    os.makedirs(os.path.dirname(output_file))
                    handler = logging.FileHandler(output_file, "w")
                handler.setLevel(logging.DEBUG)
                handler.setFormatter(formatter)
                root_logger.addHandler(handler)


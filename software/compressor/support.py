class Color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


class Converter(object):
    def humanReadableSeconds(self, time_total):
        SECOND  = 1
        MINUTE  = SECOND * 60
        HOUR    = MINUTE * 60
        DAY     = HOUR * 24

        time_total = int(time_total)

        seconds = time_total % MINUTE
        minutes = (time_total % HOUR) / MINUTE
        hours   = (time_total % DAY) / HOUR 
        days    = time_total / DAY

        output = "{0:2d}s".format(seconds)

        if days >= 1 or hours >= 1 or minutes >= 1:
            output = "{0:2d}min ".format(int(minutes)) + output

        if days >= 1 or hours >= 1:
            output = "{0:2d}h ".format(int(hours)) + output

        if days >= 1:
            output = "{0:2d}d ".format(int(days)) + output

        return output


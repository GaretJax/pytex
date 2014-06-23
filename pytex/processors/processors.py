
from pytex.processors import RstProcessor


def loadprocessors(config, logger):
    processorlist = config.get('compilation', 'preprocessors').split(',')

    # Make sure there are no duplicates
    processorlist = set(processorlist)

    # Instantiate all the necessary processors
    processors = []
    for p in processorlist:
        if p == 'rst':
            processors.append(RstProcessor())
            processors[-1].logger = logger
            logger.info("Loaded {}".format(processors[-1].name))

    return processors

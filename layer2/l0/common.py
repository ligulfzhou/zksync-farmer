import time, random
from layer2.logger import global_logger


def sleep_common_interaction_gap():
    gap = random.randint(10, 60)
    global_logger.info(f'L0: randomly sleep {gap} seconds.')
    time.sleep(gap)

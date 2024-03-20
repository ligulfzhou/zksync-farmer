import time
import copy
import random
from layer2.logger import global_logger
from layer2.lib.l1_utils import L1Utils
from layer2.lib.rs import is_already_failed
from layer2.consts import normal_type_cnt
from layer2.config.config import conf


def sleep_common_interaction_gap():
    global_logger.info('....sleep_common_interaction_gap: [0.5, 2] minutes.....')
    sleep_some_seconds(min_seconds=int(0.5*60), max_seconds=2*60)


def sleep_some_seconds(min_seconds: int = 0, max_seconds: int = 60):
    if conf.env == 'era_testnet':
        min_seconds /= 10
        max_seconds /= 10

    sleep_seconds = random.randint(min_seconds, max_seconds)
    global_logger.info(f'....sleep for {sleep_seconds} seconds.....')
    time.sleep(sleep_seconds)


def limit_cnt_if_nonce(nonce: int, cnt: int) -> bool:
    if nonce > 25 and cnt >= random.randint(1, 2):
        return True
    return False


def checking_limits(idx: int, nonce: int = 0, cnt: int = 0) -> bool:
    if is_already_failed(idx):
        return True

    if limit_cnt_if_nonce(nonce, cnt):
        return True
    return False


# balance is in wei
def transfer_value_in_eth(balance: int) -> str:
    if not balance:
        return '0'

    if balance > 0.002 * (10 ** 18):
        return '{0:.10f}'.format(balance / random.randint(110, 140) * 100 / (10 ** 18))[:8]

    if balance > 0.001 * (10 ** 18):
        return f'0.000{random.randint(1, 95)}'

    if balance > 0.0004 * (10 ** 18):
        return f'0.000{random.randint(10, 25)}'

    return '0'


def deposit_if_balance_too_low(idx, balance):
    if balance > 0.0015 * (10 ** 18):
        return

    if not random.randint(0, 5):
        L1Utils.deposit_zksync_lite()


def pickup_a_transaction_type(cur: str) -> str:
    type_cnt = copy.deepcopy(normal_type_cnt)

    type_cnt.update({
        cur: type_cnt.get(cur, 0) / 3
    })

    transaction_type_list = []
    for tp, count in type_cnt.items():
        transaction_type_list.extend([tp] * int(count))

    for _ in range(5):
        random.shuffle(transaction_type_list)

    return transaction_type_list[0]

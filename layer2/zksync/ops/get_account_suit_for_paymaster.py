import re
import time
import random
import datetime
from os import path
from typing import List
from eth_account import Account
from eth_account.signers.local import LocalAccount

from layer2.lib.rs import rs
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.consts import TokenAddress


def sleep_random_seconds():
    time.sleep(random.randint(5, 15))


def get_transaction_time_of_account(account: LocalAccount) -> int:
    v = rs.get(f'{account.address}_last_transaction_timestamp')
    if v:
        return int(v.decode())
    return 0


eth_price = 3000


def get_idx_already_paymasters() -> List[int]:
    with open(path.join(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))), "main.md")) as f:
        lines = f.readlines()

    idxs: List[int] = []
    for line in lines:
        if 'paymaster' in line:
            res = re.match(r'idx#(\d+):', line)
            if not res:
                continue

            res = res.groups()
            if not res:
                continue

            idxs.append(int(res[0]))

    return idxs


def main():
    idxs = get_idx_already_paymasters()
    print(idxs)

    choices = []
    choices.extend(list(range(48, 841)))
    choices.append('473f28e4557f4a5eaaac93fd8dbd1d75c289a663e40fd830a3f9627a7c4b825a')

    for _ in range(10):
        random.shuffle(choices)

    now = int(datetime.datetime.utcnow().timestamp())
    while choices:
        i = choices.pop()

        global_logger.info(f'{"*" * 50} check_balance {i} {"*" * 50}')
        if type(i) == int:
            t: LocalAccount = from_mnemonic(idx=i)
        else:
            t: LocalAccount = Account.from_key(i)

        try:
            last_ts = get_transaction_time_of_account(t)
            if now - last_ts <= 21 * 24 * 60 * 60:
                continue

            usdc_balance = ZksyncEraUtils.get_balance(account=t, token_address=TokenAddress.usdc.value)
            if usdc_balance < 1 * 10 ** 6:
                continue

            print(f"=======idx: {i} =======")
        except:
            time.sleep(5)
            choices.append(i)
            continue

        global_logger.info(choices)
        sleep_random_seconds()


if __name__ == '__main__':
    main()

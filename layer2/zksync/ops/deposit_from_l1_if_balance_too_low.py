import asyncio
import random
import time
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.lib.l1_utils import L1Utils
from layer2.config.config import conf
from layer2.common import sleep_some_seconds
from layer2.lib.l1_utils import from_mnemonic
from layer2.zksync.zksync_lite_utils import ZKSyncLiteUtils


def random_amount() -> int:
    r = random.randint(conf.deposits[0], conf.deposits[-1])
    l = len(str(r))
    return r - r % (10 ** (l - random.randint(2, 4)))


async def main():
    choices = []
    choices.extend(range(48, 841))
    choices.extend(list(range(1500, 1503)))
    choices.append(2012)
    for _ in range(5):
        random.shuffle(choices)

    while choices:
        idx = choices.pop()
        account: LocalAccount = from_mnemonic(idx)

        balance = await ZKSyncLiteUtils.get_balance(account)
        if balance >= 0.005 * 10 ** 18:
            global_logger.error(f'idx#{idx} already have enough lite balance: {balance / (10 ** 18)}, just skip')
            time.sleep(1)
            continue

        l1_balance = L1Utils.get_balance(account.address)
        if l1_balance <= 0.003 * 10 ** 18:
            global_logger.info(f'idx#{idx} do not have enough l1 balance: {l1_balance / (10 ** 18)}')
            time.sleep(1)
            continue

        gas_price = int(random.randint(1150, 1220) * 10 ** 7)
        gas = random.randint(64000, 65000)
        value = int(l1_balance - gas * gas_price)
        L1Utils.deposit_zksync_lite(idx=idx, value=value, gas_price=gas_price, gas=gas, wait_transaction_done=False)
        sleep_some_seconds(min_seconds=60, max_seconds=5*60)


if __name__ == '__main__':
    asyncio.run(main())

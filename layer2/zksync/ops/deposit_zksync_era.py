'''
以前的zksync2库完全没法用(所以没用它，直接调合约的，但是有问题）
现在的zksync2也许可以用，但我没试过，我反正是没去尝试
下面的代码是不好使的
'''
import pdb
import random
import time
from layer2.logger import global_logger
from layer2.lib.rs import save_era_idex, if_era_done
from layer2.lib.l1_utils import L1Utils, w3, from_mnemonic
from layer2.common import sleep_some_seconds


def main():
    choices = []
    choices.extend(list(range(72, 73)))
    # choices.extend(list(range(1500, 1504)))

    for _ in range(5):
        random.shuffle(choices)

    while len(choices):
        i = choices.pop()
        if if_era_done(i):
            global_logger.info(f'idx#{i} already done, just skip...')
            continue

        account = from_mnemonic(idx=i)
        balance = L1Utils.get_balance(account.address)
        if balance < 12000000000000000:
            global_logger.info(f'idx#{i} balance too low, {balance / (10 ** 18)}, just skip...')
            continue

        global_logger.info(f'work on {i}')
        while True:
            gas_price = w3.eth.gas_price
            if gas_price < 23 * (10 ** 9):
                break

            global_logger.info(f'gas price: {gas_price} too high....')
            sleep_some_seconds(min_seconds=15, max_seconds=60)

        gas = 125000 + random.randint(10, 99)
        # value = int(balance - gas * gas_price * 2 - 0.00001 * random.randint(50, 90))
        value = int(0.015*10**18)
        pdb.set_trace()
        done = L1Utils.deposit_zksync_era(account=account, value=value, gas_price=gas_price, gas=gas)
        if done:
            save_era_idex(i)

        time.sleep(random.randint(10, 90))
        global_logger.info(f'{"*" * 50} done {i} {"*" * 50}, and sleep for 3~15 minutes')
        sleep_some_seconds(min_seconds=60, max_seconds=60 * 5)


if __name__ == '__main__':
    main()

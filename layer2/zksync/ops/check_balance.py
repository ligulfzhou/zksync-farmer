import random
import time
from typing import List
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.consts import TokenAddress
# from okx import Funding
from eth_account.signers.local import LocalAccount


# api_key = "..."
# secret_key = "..."
# passphrase = "..."
# flag = '0'

# host = 'https://www.okx.com'

# fundingAPI = Funding.FundingAPI(api_key, secret_key, passphrase, False, flag)
# result = fundingAPI.get_balances('ETH')
# global_logger.info(result)


def sleep_random_seconds():
    time.sleep(random.randint(5, 15))
    # time.sleep(random.randint(5 * 60, 60 * 15))


def random_amount() -> str:
    # i = random.randint(100000, 145000)
    # return f'{i / 10000000}'
    return "10000000000000000"


eth_price = 3000


def main():
    choices = []
    choices.extend(list(range(48, 841)))
    choices.extend(list(range(1500, 1503)))
    choices.append(2012)
    choices.append('473f28e4557f4a5eaaac93fd8dbd1d75c289a663e40fd830a3f9627a7c4b825a')

    for _ in range(10):
        random.shuffle(choices)

    idx_to_total = {}
    total_to_idxs = {}
    while choices:
        i = choices.pop()

        global_logger.info(f'{"*" * 50} check_balance {i} {"*" * 50}')
        t: LocalAccount = from_mnemonic(idx=i)

        try:
            eth_balance = ZksyncEraUtils.get_balance(account=t)
            usdc_balance = ZksyncEraUtils.get_balance(account=t, token_address=TokenAddress.usdc.value)

            total = eth_price * eth_balance / 10 ** 18 + usdc_balance / 10 ** 6
            print(f"eth_balance: {eth_balance}, usdc_balance: {usdc_balance}, worth: {total}")
            idx_to_total.update({
                i: total
            })
            total_to_idxs.setdefault(total, []).append(i)
        except:
            time.sleep(5)
            choices.append(i)
            continue

        global_logger.info(choices)
        sleep_random_seconds()

    for total in sorted(list(total_to_idxs.keys())):
        if total > 20:
            break
        print(f"total: {total}, idxes: {total_to_idxs.get(total, [])}")

    print("=========================")
    print(idx_to_total)


if __name__ == '__main__':
    main()

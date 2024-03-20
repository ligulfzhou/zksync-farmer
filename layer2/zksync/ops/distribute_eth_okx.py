import random
import time
from typing import List, Optional
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic, w3, L1Utils
from okx import Funding
from eth_account.signers.local import LocalAccount

api_key = "..."
secret_key = "..."
passphrase = "..."
flag = '0'

host = 'https://www.okx.com'

fundingAPI = Funding.FundingAPI(api_key, secret_key, passphrase, False, flag)
result = fundingAPI.get_balances('ETH')
global_logger.info(result)

to_skip: List[int] = [
    216,
    245, 246, 247, 248, 249, 250
]


def sleep_random_seconds():
    time.sleep(random.randint(5 * 60, 60 * 15))


def random_amount() -> str:
    i = random.randint(100000, 145000)
    return f'{i / 10000000}'


def distribute_eth_to_account(account: Optional[LocalAccount], idx: int = 0, amount: str = '0.003'):
    if not account:
        account = from_mnemonic(idx)

    global_logger.info(f'{idx}: transafer {amount} to {account.address}...')
    result = fundingAPI.withdrawal('ETH', amount, '4', account.address, '0.000041', 'ETH-zkSync Era')
    global_logger.info(result)


def main():
    s, t = 153, 200
    idxs: List[int] = list(range(s, t))
    for _ in range(5):
        random.shuffle(idxs)

    while len(idxs):
        i = idxs.pop()
        if i in to_skip:
            continue

        global_logger.info(f'{"*" * 50} distribute {i} {"*" * 50}')
        t: LocalAccount = from_mnemonic(idx=i)
        balance = L1Utils.get_balance(t.address)

        amount = random_amount()
        global_logger.info(f'{i}: transafer {amount} to {t.address}...')

        result = fundingAPI.withdrawal('ETH', amount, '4', t.address, '', '0.00096')
        global_logger.info(result)

        global_logger.info(idxs)
        sleep_random_seconds()


if __name__ == '__main__':
    main()

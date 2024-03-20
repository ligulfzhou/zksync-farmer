import random
import time
from web3 import Web3
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from okx import Funding
from typing import Optional
from eth_account.signers.local import LocalAccount

api_key = "..."
secret_key = "..."
passphrase = "..."
flag = '0'

host = 'https://www.okx.com'

fundingAPI = Funding.FundingAPI(api_key, secret_key, passphrase, False, flag)
# result = fundingAPI.get_balances('ETH')
# global_logger.info(result)

celo_rpc = 'https://celo-mainnet.infura.io/v3/786649a580e3441f996da22488a8742a'
celo_w3 = Web3(Web3.HTTPProvider(celo_rpc))


celo_or_genosis_minimum_balance = 0.02 * 10 ** 18

# 下面的 0.0002，0.0003, 0.001456可能会变，需要去okx查,或者调 fundingAPI.get_currencies() 获取
# global_logger.info(fundingAPI.get_currencies())
# pdb.set_trace()


def sleep_random_seconds():
    time.sleep(random.randint(1 * 60, 60 * 3))


def random_amount() -> str:
    i = random.randint(100, 121)
    return f'{i / 100}'


def withdraw_celo(account: Optional[LocalAccount] = None, i: int = 0) -> bool:
    if not account:
        account = from_mnemonic(i)

    balance = celo_w3.eth.get_balance(account=Web3.to_checksum_address(account.address))
    if balance and balance > celo_or_genosis_minimum_balance:
        global_logger.info(f'idx#{i} already have balance, just skip...')
        time.sleep(1)
        return False

    amount = random_amount()
    global_logger.info(f'{i}: transafer {amount} to {account.address}...')
    res = fundingAPI.withdrawal("CELO", amount, "4", account.address, "0.0008", 'CELO-CELO')
    global_logger.info(f'result: {res}')


def main():
    choices = []
    choices.extend(list(range(301, 421)))

    for _ in range(5):
        random.shuffle(choices)

    done_choices = []
    while len(choices):
        i = choices.pop()
        done_choices.append(i)

        global_logger.info(f'{"*" * 50} distribute {i} {"*" * 50}')

        withdraw_celo(i=i)

        global_logger.info(f'done choices: \n{done_choices}')
        global_logger.info(f'left choices: \n{choices}')
        sleep_random_seconds()


if __name__ == '__main__':
    main()

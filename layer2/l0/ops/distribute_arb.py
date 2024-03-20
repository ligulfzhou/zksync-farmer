import datetime
import random
import time
from web3 import Web3
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from okx import Funding
from eth_account.signers.local import LocalAccount
from typing import Optional

api_key = "..."
secret_key = "..."
passphrase = "..."
flag = '0'

host = 'https://www.okx.com'

fundingAPI = Funding.FundingAPI(api_key, secret_key, passphrase, False, flag)
# result = fundingAPI.get_balances('ETH')
# global_logger.info(result)

arb_rpc = 'https://arbitrum-mainnet.infura.io/v3/786649a580e3441f996da22488a8742a'
arb_w3 = Web3(Web3.HTTPProvider(arb_rpc))

# 下面的 0.0002，0.0003, 0.001456可能会变，需要去okx查,或者调 fundingAPI.get_currencies() 获取
# global_logger.info(fundingAPI.get_currencies())
# pdb.set_trace()


balance_at_least = int(0.0007 * 10 ** 18)


def sleep_random_seconds():
    time.sleep(random.randint(1 * 60, 60 * 3))


def random_amount() -> str:
    i = random.randint(450, 530)
    return f'{i / 100000}'


def random_low_amount() -> str:
    i = random.randint(250, 350)
    return f'{i / 100000}'


def withdrawl_to_account(account: Optional[LocalAccount] = None, i: int = 0) -> bool:
    if not account:
        account: LocalAccount = from_mnemonic(idx=i)

    global_logger.info(f'=============withdrawl_to_account== idx#{i} === {account.address} ==========')
    balance = arb_w3.eth.get_balance(account=Web3.to_checksum_address(account.address))
    if balance and balance > balance_at_least:
        global_logger.info(f'idx#{i} : {account.address} already have balance: {balance / 10 ** 18}, just skip...')
        time.sleep(1)
        return False

    if balance:
        amount = random_low_amount()
    else:
        amount = random_amount()

    global_logger.info(f'{i}: transafer {amount} to {account.address}...')
    now = datetime.datetime.now().date()
    # todo: temp solution
    if now.month == 2 and i >= 421:
        res = fundingAPI.withdrawal("ETH", amount, "4", account.address, "0.0001", 'ETH-Arbitrum One')
        global_logger.info(f'result: {res}')
        return True
    return False


def main():
    choices = []
    choices.extend(list(range(239, 421)))

    for _ in range(5):
        random.shuffle(choices)

    done_choices = []
    while len(choices):
        i = choices.pop()
        done_choices.append(i)

        global_logger.info(f'{"*" * 50} distribute {i} {"*" * 50}')
        withdrawl_to_account(i=i)

        global_logger.info(f'done choices: \n{done_choices}')
        global_logger.info(f'left choices: \n{choices}')
        sleep_random_seconds()


if __name__ == '__main__':
    main()

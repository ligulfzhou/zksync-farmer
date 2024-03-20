"""
这里是以前给（zksync lite）每个号的成本比较低
arb的规则出来后，准备从okx 提币到zksync lite上，补充一下余额
"""
import random
import asyncio
from typing import List
from layer2.logger import global_logger
from layer2.common import sleep_some_seconds
from eth_account.signers.local import LocalAccount
from layer2.lib.l1_utils import from_mnemonic
from layer2.zksync.zksync_lite_utils import ZKSyncLiteUtils
from okx import Funding

api_key = "..."
secret_key = "..."
passphrase = "..."
flag = '0'

fundingAPI = Funding.FundingAPI(api_key, secret_key, passphrase, False, flag)
result = fundingAPI.get_balances('ETH')
global_logger.info(f'okx eth balance: {result}')

to_skip: List[int] = []
# 自己分账的账户
to_skip.extend(list(range(0, 50)))
to_skip.extend([216, 245, 246, 247, 248, 249, 250])

# 清空eth去zksync的账号
always_need_to_run: List[int] = []
always_need_to_run.extend(list(range(50, 153)))
always_need_to_run.extend(list(range(823, 833)))

least_lite_eth_in_wei: int = int(0.005 * 10 ** 18)

all_indexes: List[int] = []
all_indexes.extend(list(range(0, 833)))


def okx_withdraw_eth_to_lite(address: str, amount: str = '0.0056'):
    sleep_some_seconds(min_seconds=3, max_seconds=100)
    res = fundingAPI.withdrawal('ETH', amount, '4', address, '0.0002', "ETH-zkSync Lite")
    global_logger.info(res)


def get_deposit_amount(balance: int) -> str:
    return f'{(random.randint(80, 100) - int(balance / (10 ** 18) * 10000)) / 10000}'


async def deposit_to_lite_idx(idx: int) -> bool:
    account: LocalAccount = from_mnemonic(idx=idx)
    balance = await ZKSyncLiteUtils.get_balance(account)

    if idx in always_need_to_run:
        global_logger.info(f'----------always_need_to_run#{idx}-----')
        if balance > least_lite_eth_in_wei:
            global_logger.error(f'account#{idx}, {account.address} already has balance > 0.005 ETH, just skip')
            return False
        else:
            deposit_amount = get_deposit_amount(balance)
            okx_withdraw_eth_to_lite(account.address, deposit_amount)
            return True

    global_logger.info(f'----------not always_need_to_run#{idx}-----')
    idx_bro = idx + 1 if idx % 2 else idx - 1
    account_bro: LocalAccount = from_mnemonic(idx_bro)
    balance_bro = await ZKSyncLiteUtils.get_balance(account_bro)

    if balance > least_lite_eth_in_wei or balance_bro > least_lite_eth_in_wei:
        global_logger.info(f'balance#{idx} or balance_bro#{idx_bro} > 0.005eth, just skip...')
        return False

    if balance_bro > balance:
        chosen_address = account_bro.address
        deposit_amount = get_deposit_amount(balance_bro)
    else:
        chosen_address = account.address
        deposit_amount = get_deposit_amount(balance)

    okx_withdraw_eth_to_lite(chosen_address, deposit_amount)
    return True


async def deposit_to_lite():
    for _ in range(5):
        random.shuffle(all_indexes)

    while len(all_indexes):
        i = all_indexes.pop()
        global_logger.info(f'execute {i}')
        if i in to_skip:
            global_logger.info(f'{i} is always skipped...')
            continue

        sleep_some_seconds(min_seconds=3, max_seconds=100)
        executed = await deposit_to_lite_idx(i)
        global_logger.info(all_indexes)
        if executed:
            sleep_some_seconds(min_seconds=30 * 60, max_seconds=60 * 60)
        else:
            sleep_some_seconds(min_seconds=10, max_seconds=30)


async def main():
    await deposit_to_lite()


if __name__ == '__main__':
    asyncio.run(main())

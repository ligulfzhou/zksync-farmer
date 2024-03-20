"""
这里是想把 以太坊 从eth跨链到zksync lite
"""
import asyncio
import random
import time

from layer2.logger import global_logger
from layer2.lib.rs import failed_indexes, remove_failed_idx
from layer2.lib.l1_utils import L1Utils, get_gasprice, get_max_gas_price
from eth_account.signers.local import LocalAccount
from layer2.lib.l1_utils import from_mnemonic
# from eth.zksync.zksync_lite_utils import ZKSyncLiteUtils



async def deposit_if_not_enough(account: LocalAccount) -> bool:
    # balance = await ZKSyncLiteUtils.get_balance(account)
    # global_logger.info(f'balance: {balance}')
    # if balance >= 80000000000000:
    #     return True

    # < 0.001 eth
    l1_balance = L1Utils.get_balance(account.address)
    global_logger.info(f'l1 balance: {l1_balance}')
    if l1_balance < 4000000000000000:
        return False

    gas_price = random.randint(10.5*10**9, 12.4*10**9)
    if gas_price > 25 * 10**9:
        global_logger.error(f'gas_price too high, just skip...')
        return False

    gas_price_ = gas_price

    gas = 65_000
    value = l1_balance - gas_price_ * gas
    L1Utils.deposit_zksync_lite(account=account, value=value, gas_price=gas_price_, gas=gas)
    return True


async def main():
    idxes = failed_indexes()
    for idx in idxes:
        account: LocalAccount = from_mnemonic(idx=idx)
        success = await deposit_if_not_enough(account)
        if success:
            remove_failed_idx(idx)

        time.sleep(random.randint(10, 30))


if __name__ == '__main__':
    asyncio.run(main())

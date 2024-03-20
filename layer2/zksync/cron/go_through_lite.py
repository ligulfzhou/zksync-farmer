import asyncio
import datetime
import random
from eth_account import Account
from zksync_sdk.types import AccountState

from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.lib.rs import save_failed_idx, is_already_failed
from layer2.consts import TransactionType
from layer2.zksync.zksync_lite_utils import ZKSyncLiteUtils
from layer2.common import sleep_common_interaction_gap, transfer_value_in_eth, pickup_a_transaction_type


async def execute(private_key: str = '', idx: int = 0):
    # if not private_key and is_already_failed(idx):
    #     global_logger.info(f'already failed, just skip {idx}...')
    #     return

    if private_key:
        account = Account.from_key(private_key)
    else:
        account = from_mnemonic(idx)

    # forbid frequency
    # day = datetime.datetime.utcnow().day
    now_dt = datetime.datetime.utcnow()
    now = int(now_dt.timestamp())
    tx = ZKSyncLiteUtils.get_last_tx(account)
    ts = ZKSyncLiteUtils.get_ts_from_tx(tx)
    nonce = ZKSyncLiteUtils.get_nonce_from_tx(tx)
    global_logger.info(f'nonce: {nonce}')

    if not nonce:
        global_logger.info(f'{account.address} not activated, activate it first...')
        await ZKSyncLiteUtils.activate(account=account)
        # return

    if nonce:
        days = 26
        # if nonce < 5:
        #     days = random.randint(3, 7)
        # elif nonce < 10:
        #     days = random.randint(5, 11)
        # elif nonce < 20:
        #     days = random.randint(7, 18)
        # else:
        #     days = random.randint(23, 26)

        if now - ts <= days * 24 * 60 * 60:
            global_logger.error(
                f'for {idx} or {account.address}, now-ts = {now - ts} <<<< {days}*24*60*60 = {days * 24 * 60 * 60},'
                f' then just skip..')
            return

        # 如果上次也在这个月，就先跳过
        last_dt = datetime.datetime.fromtimestamp(ts)
        if last_dt.month == now_dt.month:
            global_logger.error(
                f'😤 last_dt: {last_dt}, now_dt: {now_dt}, '
                f' then just skip..')
            return

        r = random.randint(3, 10)
        if now_dt.day + r <= 15:
            global_logger.error(
                f'😤 last_dt: {last_dt}, now_dt: {now_dt}, wait now_dt.day#{now_dt.day + r} > 15, '
                f' then just skip..')
            return

    # limit too many tx
    # if i and checking_limits(i):
    #     global_logger.info(f'{"*" * 50} {i} is already failed,just skip {"*" * 50}')
    #     return
    # check balance
    account_state: AccountState = await ZKSyncLiteUtils.get_account(account=account)
    balance = account_state.committed.balances.get('ETH', 0)
    if balance < 0.00004 * 10 ** 18:
        save_failed_idx(idx)
        global_logger.error(f'{idx}: balance too low..')
        return

    global_logger.info(f'{"*" * 50} work on {idx} or {account.address} {"*" * 50}')

    last_tx_type = ZKSyncLiteUtils.get_type_from_tx(tx)

    n = 1 if nonce >= 13 else 2
    for _ in range(0, n):
        tx_type = pickup_a_transaction_type(last_tx_type)

        if tx_type == TransactionType.transfer.value:
            success = await ZKSyncLiteUtils.transfer_to_self(account=account,
                                                             value_in_eth=transfer_value_in_eth(balance))
        elif tx_type == TransactionType.mint_nft.value:
            success = await ZKSyncLiteUtils.mint_nft(account=account)
        else:  # TransactionType.transfer_nft.value
            success = await ZKSyncLiteUtils.tranfer_nft_to_self(account=account)

        if not success and idx:
            save_failed_idx(idx)

        last_tx_type = tx_type


async def iterate_all():
    choices = []
    choices.extend(list(range(0, 841)))
    choices.extend(list(range(1500, 1504)))

    for _ in range(10):
        random.shuffle(choices)

    while choices:
        i = choices.pop()
        try:
            if type(i) == int:
                await execute(idx=i)
            else:
                await execute(private_key=i)
        except Exception as e:
            global_logger.error(f'execute {i} failed with {e}')

        global_logger.info(f'{"*" * 50} done {i} {"*" * 50}')
        global_logger.info(choices)
        sleep_common_interaction_gap()


async def main():
    while True:
        global_logger.info('\n' * 3)
        global_logger.info(f'{"*" * 50} iterate start..{"*" * 50}')
        global_logger.info('\n' * 3)

        await iterate_all()

        global_logger.info('\n' * 3)
        global_logger.info(f'{"*" * 50} iterate stop..{"*" * 50}')
        global_logger.info('\n' * 3)

        sleep_common_interaction_gap()


if __name__ == '__main__':
    asyncio.run(main())

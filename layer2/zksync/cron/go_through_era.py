import time
import random
import datetime
from enum import Enum
from eth_account import Account
from typing import List, Optional
from eth_account.signers.local import LocalAccount

from layer2.lib.rs import rs, skip_idxs
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.consts import TokenAddress
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.zksync.ops.distribute_eth_okx import distribute_eth_to_account
from layer2.common import sleep_common_interaction_gap, sleep_some_seconds
from layer2.zksync.era_project.weth_wrapper import WethWrapper


class TransactionType(Enum):
    mint_nft: str = 'mint_nft'
    syncswap: str = 'syncswap'
    mute: str = 'mute'
    approve_token: str = 'approve_token'
    weth_wrap_unwrap: str = 'wrap_unwrap'
    velocore_swap: str = 'velocore'
    spacefi_swap: str = 'spacefi'
    # this failed..
    zkswap: str = 'zkswap'
    account: str = 'account'


transaction_types: List[str] = [
    TransactionType.mint_nft.value,
    TransactionType.syncswap.value,
    TransactionType.mute.value,
    TransactionType.velocore_swap.value,
    TransactionType.spacefi_swap.value,
    # TransactionType.zkswap.value,
    TransactionType.approve_token.value,
    TransactionType.weth_wrap_unwrap.value,
    TransactionType.account.value
]


def get_done_transaction_types_of_account(account: LocalAccount) -> List[str]:
    res = rs.lrange(f'{account.address}_transaction_types', 0, -1)
    return [i.decode() for i in res]


def save_transaction_types_of_account(account: LocalAccount, transaction_type: str):
    rs.rpush(f'{account.address}_transaction_types', transaction_type)


def save_transaction_time_of_account(account: LocalAccount):
    ts = int(datetime.datetime.utcnow().timestamp())
    rs.set(f'{account.address}_last_transaction_timestamp', ts)


def get_transaction_time_of_account(account: LocalAccount) -> int:
    v = rs.get(f'{account.address}_last_transaction_timestamp')
    if v:
        return int(v.decode())
    return 0


def choose_transaction_type(account: LocalAccount, idx: int = 0) -> str:
    mint_nft_limit = 1
    # mint_nft_limit = random.randint(2, 4)
    done_transaction_types = get_done_transaction_types_of_account(account)
    nft_minted = TransactionType.mint_nft.value in done_transaction_types

    to_choose_from = [i for i in transaction_types if i not in done_transaction_types]
    to_choose_from = [item for item in to_choose_from if
                      item not in (TransactionType.mute.value, TransactionType.spacefi_swap.value)]
    if idx in (162, 163):
        to_choose_from = [item for item in to_choose_from if item == TransactionType.account.value]

    if not to_choose_from:
        to_choose_from = [TransactionType.syncswap.value] * 2 \
                         + [TransactionType.velocore_swap.value] * 2 \
                         + [TransactionType.approve_token.value] \
                         + [TransactionType.weth_wrap_unwrap.value] * 2
        # + [TransactionType.mute.value] * 2 \
        # + [TransactionType.spacefi_swap.value] * 2 \

    transaction_type = random.choice(to_choose_from)
    if transaction_type == TransactionType.mint_nft.value and nft_minted >= mint_nft_limit:
        return choose_transaction_type(account)
    return transaction_type


def check_balance(account: LocalAccount, idx: int) -> bool:
    if idx <= 48:
        global_logger.info(f"skip withdraw to idx#{idx} < 48")
        return False

    balance = ZksyncEraUtils.get_balance(account=account)
    usdc_balance = ZksyncEraUtils.get_balance(account=account, token_address=TokenAddress.usdc.value)
    cur = balance / 10 ** 18 + usdc_balance / 10 ** 6 / 4000
    global_logger.info(f'balance: eth: {balance / 10 ** 18}, usdc: {usdc_balance / 10 ** 6}, total: {cur}')

    gap = 0.0055 - cur
    if gap <= 0:
        global_logger.info(f"{account.address} has balance {cur} > 0.005, skip withdraw eth to it..")
        return False

    # if 500 <= idx < 600:
    #     global_logger.info(f"{account.address} - 0.005 = {gap}, idx#{idx}, [500, 600), just skip...")
    #     return False

    if gap < 0.0015:
        # global_logger.info(f"{account.address} - 0.005 = {gap}, < 0.001, just skip...")
        # return False
        if gap * 3 < 0.002:
            amount = f'0.00{random.randint(20, 35)}'
        else:
            amount = f'{(gap * 3):.04f}'
    else:
        if gap * 2 < 0.002:
            amount = f'0.00{random.randint(20, 35)}'
        else:
            # amount = f'{(gap * 3):.04f}'
            amount = f'{(gap * 2):.04f}'

    distribute_eth_to_account(account, idx, amount)
    return True


def execute(private_key: Optional[str] = None, idx: int = 0):
    if private_key:
        account = Account.from_key(private_key)
    else:
        account = from_mnemonic(idx)

    w3 = ZksyncEraUtils.get_w3_cli()

    global_logger.info(f'execute {private_key} or {idx}, address is {account.address} ')

    # check balance
    balance = w3.eth.get_balance(account.address)
    if balance < 0.00004 * 10 ** 18:
        global_logger.info(f'🥺🥺🥺🥺🥺{idx}: balance too low..🥺🥺🥺🥺🥺')
        return

    if check_balance(account, idx):
        time.sleep(random.randint(80, 120))

    weth_balance = ZksyncEraUtils.get_balance(account=account, token_address=TokenAddress.weth.value)
    if weth_balance:
        if WethWrapper.withdraw(account, w3, value=weth_balance):
            global_logger.info(f'run unwrap on {account.address}, success: true')
            global_logger.info('🚀success🚀')
            save_transaction_types_of_account(account, TransactionType.weth_wrap_unwrap.value)
            save_transaction_time_of_account(account)
            return

    nonce = w3.eth.get_transaction_count(account.address)
    global_logger.info(f'nonce: {nonce}')

    now_dt = datetime.datetime.utcnow()
    now = int(now_dt.timestamp())
    global_logger.info(f'now ts: {now}, date: {datetime.datetime.fromtimestamp(now)}')
    last_ts = ZksyncEraUtils.get_last_transaction_timestamp_of_account(account=account)
    # global_logger.info(
    #     f'last_transaction_ts of {account.address} is {last_ts}, date: {datetime.datetime.fromtimestamp(last_ts)}')

    # if not last_ts:
    #     global_logger.error(f"ATTENTION: {account.address} last_ts is 0, just continue to run transaction..")

    if last_ts == -1:
        # global_logger.error(f'ATTENTION: failed to get last_transaction_ts from zksync2-mainnet-explorer.zksync.io')
        last_ts = get_transaction_time_of_account(account)
        if not last_ts:
            days_ = random.randint(1, 25)
            last_ts = now - days_ * 24 * 60 * 60
            global_logger.error(f'...randomly set a ts: {last_ts}, {days_} days ago.')
        else:
            global_logger.error(f'...get it from redis: {last_ts}')

    global_logger.info(
        f'last_transaction_ts of {account.address} is {last_ts}, date: {datetime.datetime.fromtimestamp(last_ts)}')

    # should decrease gap...
    # because if the gas price stay high for a long time, we will not have transactions at all
    if nonce and last_ts:
        days = 0

        # if nonce < 5:
        #     days = random.randint(3, 7)
        # elif nonce < 10:
        #     days = random.randint(5, 11)
        # elif nonce < 50:
        #     last_dt = datetime.datetime.fromtimestamp(last_ts)
        #     usdc_balance = ZksyncEraUtils.get_balance(account=account, token_address=TokenAddress.usdc.value)
        #     if last_dt.month == now_dt.month and usdc_balance < 1 * 10 ** 6:
        #         print(f"如果这个月做过了，并且usdc的余额<1,这个月就别动了")
        #         if nonce > 40:
        #             days = random.randint(20, 30)
        #         else:
        #             days = random.randint(7, 15)
        #     else:
        #         days = random.randint(2, 5)
        # else:
        #     usdc_balance = ZksyncEraUtils.get_balance(account=account, token_address=TokenAddress.usdc.value)
        #     if usdc_balance < 1 * 10 ** 6:
        #         days = random.randint(25, 27)
        #     else:
        #         days = random.randint(7, 15)

        if not private_key and 0 <= idx <= 48:
            # 0~49的本来就是女巫号(完全关联在一起了)，还是少跑点, 省点钱
            days *= 2
            if days > 30:
                days = 24

        global_logger.info(f'choose the days gap: {days}, actually days gap: {(now - last_ts) / 24 / 60 / 60:.2f}')
        if now - last_ts <= days * 24 * 60 * 60:
            global_logger.error(
                f'😤for {idx} or {account.address}, now-ts = {now - last_ts} <<<< {days}*24*60*60 = {days * 24 * 60 * 60},'
                f' then just skip..')
            return

        # 如果上次也在这个月，就先跳过
        last_dt = datetime.datetime.fromtimestamp(last_ts)
        # if last_dt.month == now_dt.month:
        #     global_logger.error(
        #         f'😤 last_dt: {last_dt}, now_dt: {now_dt}, '
        #         f' then just skip..')
        #     return

        r = random.randint(3, 10)
        min_day = 15 if now_dt.month != 3 else 5
        if now_dt.day + r <= min_day:
            global_logger.error(
                f'😤 last_dt: {last_dt}, now_dt: {now_dt}, r: {r}, wait now_dt.day#{now_dt.day + r} > {min_day}, '
                f' then just skip..')
            return

    # zat已经全卖完了，所以下面的代码注释掉了。。
    # if not private_key and not last_ts and 0 <= idx <= 48 and nonce:
    #     # make sure next trans for (0~49) is after 2023-06-01
    #     t = datetime.datetime.strptime('2023-06-01', '%Y-%m-%d')
    #     if now < t.timestamp():
    #         global_logger.info(f'idx#{idx} should run after 06-01, just return...')
    #         return

    # if not private_key and idx <= 49 and not nonce:
    #     ZksyncEraUtils.sell_zat_token(account=account, force=True)

    # sell zat token
    # low_bar = False
    # if not private_key and 500 <= idx <= 599:
    #     low_bar = True

    # global_logger.info(f'try to sell zat token for account: {account.address}')
    # ZksyncEraUtils.sell_zat_token(account=account, low_bar=low_bar)

    transaction_type = choose_transaction_type(account, idx=idx)
    success = False
    if transaction_type == TransactionType.mint_nft.value:
        success = ZksyncEraUtils.mint_nft(account=account)
    elif transaction_type == TransactionType.syncswap.value:
        success = ZksyncEraUtils.syncswap_swap(account=account)
    elif transaction_type == TransactionType.mute.value:
        success = ZksyncEraUtils.mute_swap(account=account)
    elif transaction_type == TransactionType.spacefi_swap.value:
        success = ZksyncEraUtils.spacefi_swap(account=account)
    elif transaction_type == TransactionType.velocore_swap.value:
        success = ZksyncEraUtils.velocore_swap(account=account)
    elif transaction_type == TransactionType.approve_token.value:
        success = ZksyncEraUtils.random_approve_token(account=account)
    elif transaction_type == TransactionType.zkswap.value:
        success = ZksyncEraUtils.zkswap_swap(account=account)
    elif transaction_type == TransactionType.account.value:
        if idx in (163, 162):
            success = False
        else:
            success = ZksyncEraUtils.account_create(account=account, idx=idx)
    elif transaction_type == TransactionType.weth_wrap_unwrap.value:
        success = ZksyncEraUtils.wrap_unwrap_weth(account=account)

    global_logger.info(f'run transaction:#{transaction_type} on {account.address}, success: {success}')
    if success:
        global_logger.info('🚀success🚀')
        save_transaction_types_of_account(account, transaction_type)
        save_transaction_time_of_account(account)


def iterate_all():
    choices = []
    choices.extend(list(range(0, 841)))
    choices.extend(list(range(1500, 1503)))
    choices.append(2012)

    for _ in range(10):
        random.shuffle(choices)

    while choices:
        i = choices.pop()
        idxes_to_skip = skip_idxs()
        if str(i) in idxes_to_skip:
            global_logger.info(f'idx#{i} is in skip idxes, all idxes to skip: {idxes_to_skip}')
            continue

        try:
            if type(i) == int:
                execute(idx=i)
            else:
                execute(private_key=i)
        except Exception as e:
            global_logger.error(f'execute {i} failed with {e}')

        if choices:
            global_logger.info(choices)
            global_logger.info(f'{"*" * 50} done {i} {"*" * 50}')
            sleep_common_interaction_gap()
        else:
            global_logger.info('-----------iterate_all done--------------')


def main():
    while True:
        global_logger.info('\n' * 3)
        global_logger.info(f'{"*" * 50} iterate start..{"*" * 50}')
        global_logger.info('\n' * 3)

        iterate_all()

        global_logger.info('\n' * 3)
        global_logger.info(f'{"*" * 50} iterate stop..{"*" * 50}')
        global_logger.info('\n' * 3)

        sleep_common_interaction_gap()


if __name__ == '__main__':
    main()

import random
import datetime
from web3 import Web3
from eth_account import Account
from typing import Optional
from eth_account.signers.local import LocalAccount

from layer2.lib.rs import rs
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.l0.common import sleep_common_interaction_gap
from layer2.l0.ops.distribute_arb import withdrawl_to_account
from layer2.l0.ops.arb_dfk_klaytn import execute_on_account as bridge_dfk_gold
from layer2.l0.ops.arb_celo_gnosis import execute_on_account as bridge_ageur

arb_rpc = 'https://arbitrum-mainnet.infura.io/v3/786649a580e3441f996da22488a8742a'
arb_w3 = Web3(Web3.HTTPProvider(arb_rpc))

one_day = 24 * 60 * 60


def if_to_limit_on_frequency(account: LocalAccount) -> bool:
    key = f'l0_{account.address}'
    limit = rs.setnx(key, 1)
    if limit:
        rs.expire(key, random.randint(1, 3) * one_day)
    else:
        seconds = rs.ttl(key)
        if seconds < 50:
            rs.delete(key)
            return False
        global_logger.info(f'account#{account.address} still need {seconds} seconds,'
                           f' or {seconds // 3600}H{seconds // 60 % 60}M{seconds % 60}S')
    return not limit


def execute(private_key: Optional[str] = None, idx: int = 0, force: bool = False):
    global_logger.info(f'=============execute: idx#{idx} or private key: {private_key}========================')
    if private_key:
        account = Account.from_key(private_key)
    else:
        account = from_mnemonic(idx)

    if not force and if_to_limit_on_frequency(account):
        global_logger.info(f'=============execute done: idx#{idx} limit on frequency========================')
        return

    withdrawed = withdrawl_to_account(account, idx)
    if withdrawed:
        global_logger.info(f'😤 no arb balance, withdrawl some arb, and skip...')
        rs.delete(f'l0_{account.address}')
        return

    # balance = arb_w3.eth.get_balance(Web3.to_checksum_address(account.address))
    # if not balance:
    #     global_logger.info(f'😤 no arb balance, return...')
    #     return True

    other = random.randint(1, 2)
    one_of = random.randint(1, 2)

    choices = ['ageur'] * other + ['dfk'] * one_of
    random.shuffle(choices)
    failed_count = 0
    ageur_failed = False
    for choice in choices:
        if choice == 'ageur':
            if not ageur_failed:
                ageur_status = bridge_ageur(account=account, exec_count=1)
                if not ageur_status:
                    ageur_failed = True
                    failed_count += 1
            else:
                failed_count += 1
        else:
            dfk_gold_status = bridge_dfk_gold(account=account, exec_count=1)
            if not dfk_gold_status:
                failed_count += 1

    if failed_count >= 2:
        rs.delete(f'l0_{account.address}')

    global_logger.info(
        f'===========execute done: idx#{idx}, runed {other + one_of - failed_count} jobs=================')


def iterate_all():
    choices = []
    choices.extend(list(range(48, 500)))
    choices.append('...private key..')

    for _ in range(10):
        random.shuffle(choices)

    while choices:
        i = choices.pop()
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

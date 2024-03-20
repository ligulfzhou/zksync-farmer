import random
import time

from web3 import Web3
from eth_account.signers.local import LocalAccount

from layer2.lib.rs import rs
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.l0.ops.arb_dfk_klaytn import execute_on_account as bridge_dfk_gold
from layer2.l0.ops.arb_celo_gnosis import execute_on_account as bridge_ageur

arb_rpc = 'https://arbitrum-mainnet.infura.io/v3/786649a580e3441f996da22488a8742a'
arb_w3 = Web3(Web3.HTTPProvider(arb_rpc))

balance_at_least = int(0.001 * 10 ** 18)


def if_to_limit_on_frequency(account: LocalAccount) -> bool:
    balance = arb_w3.eth.get_balance(Web3.to_checksum_address(account.address))
    if not balance or balance < balance_at_least:
        return True

    key = f'l0_{account.address}'
    limit = rs.setnx(key, 1)
    if limit:
        expire = 24 * 60 * 60
        if random.randint(0, 1):
            expire += random.randint(0, 2000)
        else:
            expire -= random.randint(0, 2000)
        rs.expire(key, expire)
    else:
        seconds = rs.ttl(key)
        global_logger.error(f'😤account#{account.address} still need {seconds} seconds, or {seconds // 60}M{seconds % 60}S')
    return not limit


def iterate_all():
    choices = []
    choices.extend(list(range(239, 421)))

    for _ in range(10):
        random.shuffle(choices)

    while choices:
        i = choices.pop()
        account: LocalAccount = from_mnemonic(i)

        if if_to_limit_on_frequency(account):
            global_logger.error(f'😤skip idx#{i}')
            time.sleep(random.randint(1, 5))
            continue

        try:
            exec_count = i % 5
            if exec_count in (0, 1):
                exec_count += random.randint(2, 5)

            if random.randint(0, 1):
                success = bridge_dfk_gold(account=account, exec_count=exec_count)
            else:
                success = bridge_ageur(account=account, exec_count=exec_count)

            if not success:
                key = f'l0_{account.address}'
                rs.delete(key)
        except Exception as e:
            global_logger.error(f'execute {i} failed with {e}')

        if choices:
            global_logger.info(choices)
            global_logger.info(f'{"*" * 50} done {i} {"*" * 50}')
            time.sleep(random.randint(10, 60))
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


if __name__ == '__main__':
    main()

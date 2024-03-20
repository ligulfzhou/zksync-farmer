import time
import random
import asyncio
import datetime

import requests
from web3 import Web3
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.lib.rs import rs
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.assets.assets import get_abi
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.zksync.era_project.syncswap import SyncSwap
from layer2.common import sleep_some_seconds, sleep_common_interaction_gap

contract_addr = '0x95702a335e3349d197036Acb04BECA1b4997A91a'
token_addr = '0x7D54a311D56957fa3c9a3e397CA9dC6061113ab3'

zkpepe_abi = get_abi("zkpepe.json")

w3 = ZksyncEraUtils.get_w3_cli()


def claim(idx):
    account: LocalAccount = from_mnemonic(idx)

    res = requests.get(f'https://www.zksyncpepe.com/resources/amounts/{account.address.lower()}.json').json()
    amount = res[0]
    proof = requests.get(f'https://www.zksyncpepe.com/resources/proofs/{account.address.lower()}.json').json()
    proof = [Web3.to_bytes(hexstr=i) for i in proof]

    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=zkpepe_abi)
    tx_hash = contract.functions.claim(
        proof,
        amount * 10 ** 18
    ).build_transaction({
        'from': Web3.to_checksum_address(account.address),
        'nonce': w3.eth.get_transaction_count(account.address),
        'gasPrice': w3.eth.gas_price,
    })

    gas_estimate = w3.eth.estimate_gas(tx_hash)
    gas_price = w3.eth.gas_price
    gas_fee = gas_estimate * gas_price
    global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

    signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')


def check_if_claimed(idx: int) -> bool:
    return False


def check_claims(st: int = 0, ed: int = 456):
    # 检查是否领了。。
    for idx in range(st, ed):
        claimed = check_if_claimed(idx)
        if claimed:
            global_logger.info(f'idx#{idx} ok')
        else:
            global_logger.info(f'-----------------------idx#{idx} claimed: {claimed}----------------')
            global_logger.info(f'just claim it: #{idx}')
            claim(idx)
        time.sleep(random.randint(30, 50) / 100)


def claim_range():
    idxs = []
    idxs.extend(list(range(0, 841)))
    idxs.extend([1500, 1501, 1502, 2012])

    for _ in range(5):
        random.shuffle(idxs)

    while True:
        if len(idxs) <= 0:
            break

        i = idxs.pop()
        if i in (74, 80):
            continue

        try:
            claimed = check_if_claimed(i)
            if not claimed:
                global_logger.info(f'=====> claim idx#{i} <=====')
                try:
                    claim(i)
                except Exception as e:
                    global_logger.error(f'claim {i} failed with {e}')

                global_logger.info(f"{'*' * 100} {i} {'*' * 100}")
            else:
                global_logger.info(f'idx#{i} is already claimed, just skip...')

        except Exception as e:
            global_logger.error(e)
            global_logger.info(f"{'*' * 100} {i} {'*' * 100}")

        global_logger.info(f"left: {idxs}")
        sleep_some_seconds(0, 10)


def sell_zkpepe():
    idxs = []
    idxs.extend(list(range(0, 841)))
    idxs.extend([1500, 1501, 1502, 2012])
    for _ in range(5):
        random.shuffle(idxs)

    while True:
        if len(idxs) <= 0:
            break

        i = idxs.pop()
        global_logger.info(f'start to sell {i}....')
        try:
            success = ZksyncEraUtils.sell_zkpepe(idx=i)
        except:
            print(f'failed: {i}')
        if success:
            sleep_common_interaction_gap()

        account: LocalAccount = from_mnemonic(i)
        ts = int(datetime.datetime.utcnow().timestamp())
        rs.set(f'{account.address}_last_transaction_timestamp', ts)


def approve_zkpepe():
    # 714～840的偶数的账号（基数没有余额，需要给基数的转）
    idxs = []
    idxs.extend(list(range(0, 841)))
    idxs.extend([1500, 1501, 1502, 2012])
    for _ in range(5):
        random.shuffle(idxs)

    for i in idxs:
        if i % 2:
            continue

        global_logger.info(f'start to approve {i}....')
        account: LocalAccount = from_mnemonic(i)

        zat_balance = ZksyncEraUtils.get_balance(account=account, token_address=token_addr)
        if zat_balance < 50 * 10 ** 18:
            global_logger.error(f'you do not have zat token, just skip...')
            return False

        SyncSwap.approve_token(account, w3, token_addr)
        time.sleep(1)
        ts = int(datetime.datetime.utcnow().timestamp())
        rs.set(f'{account.address}_last_transaction_timestamp', ts)


def check_balance():
    idxs = []
    idxs.extend(list(range(0, 841)))
    idxs.extend([1500, 1501, 1502, 2012])

    balance = 0
    for _ in range(5):
        random.shuffle(idxs)

    for i in idxs:
        if i % 2:
            continue

        account: LocalAccount = from_mnemonic(i)
        zat_balance = ZksyncEraUtils.get_balance(account=account, token_address=token_addr)
        balance += zat_balance
        print(f"{account.address} balance: {zat_balance}, sum: {balance}")

    time.sleep(1)
    print(f'sum balance: {balance}')


async def main():
    # claim_range()
    # check_balance()
    sell_zkpepe()


if __name__ == '__main__':
    asyncio.run(main())

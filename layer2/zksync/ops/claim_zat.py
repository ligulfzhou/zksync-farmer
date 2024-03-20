"""
项目已领取结束,并已经全卖掉了,脚本已无用处
"""
import asyncio
import random
import time

import requests
from web3 import Web3
from typing import Dict
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.assets.assets import get_abi
from layer2.zksync.era_project.syncswap import SyncSwap
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.consts import TokenAddress
from layer2.common import sleep_some_seconds
from layer2.zksync.ops.tranfer_eth_v2 import transfer_eth

from okx import Funding

zat_claim_addr = '0x9aA48260Dc222Ca19bdD1E964857f6a2015f4078'
zat_claim_abi = get_abi("claim_zat.json")

headers = {'accept': 'application/json, text/plain, /', 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
           'content-type': 'application/json',
           'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"', 'sec-ch-ua-mobile': '?0',
           'sec-ch-ua-platform': '"macOS"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors',
           'sec-fetch-site': 'same-site', 'Referer': 'https://airdrop.zkape.io/',
           'Referrer-Policy': 'strict-origin-when-cross-origin'}

w3 = ZksyncEraUtils.get_w3_cli()

api_key = "..."
secret_key = "..."
passphrase = "..."
flag = '0'

fundingAPI = Funding.FundingAPI(api_key, secret_key, passphrase, False, flag)

global_logger.info(fundingAPI.get_currencies())

# result = fundingAPI.get_balances('ETH')
# global_logger.info(f'okx eth balance: {result}')


def check_if_claimed(idx) -> bool:
    account: LocalAccount = from_mnemonic(idx)

    contract = w3.eth.contract(address=Web3.to_checksum_address(zat_claim_addr), abi=zat_claim_abi)
    claimed = contract.functions.claimed(Web3.to_checksum_address(account.address)).call()
    return claimed


def claim(idx):
    account: LocalAccount = from_mnemonic(idx)

    params = {
        'address': account.address
    }
    res = requests.post('https://zksync-ape-apis.zkape.io/airdrop/index/getcertificate', headers=headers,
                        json=params).json()

    global_logger.info(res)
    data = res.get('Data', {})
    owner, value, nonce, deadline, v, r, s = data['owner'], data['value'], data['nonce'], data['deadline'], data['v'], \
        data['r'], data['s']

    contract = w3.eth.contract(address=Web3.to_checksum_address(zat_claim_addr), abi=zat_claim_abi)
    tx_hash = contract.functions.claim(
        Web3.to_checksum_address(owner),
        int(value),
        int(nonce),
        deadline,
        v,
        Web3.to_bytes(hexstr=r),
        Web3.to_bytes(hexstr=s)
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


def claim_0_to_50():
    for i in range(50):
        global_logger.info(f'run on {i} ...')
        if i > 0:
            claim(i)

        if i == 49:
            break

        ether_balance = ZksyncEraUtils.get_balance(idx=i)
        if ether_balance < (0.01 + 0.002) * 10 ** 18 and i > 0:
            # force sell zat
            ZksyncEraUtils.sell_zat_token(idx=i, force=True)
            global_logger.info('sleep for 5 minutes...')
            time.sleep(3 * 60)
            ether_balance = ZksyncEraUtils.get_balance(idx=i)

        transfer_value = ether_balance - 10 ** 16
        global_logger.info(f'transfer_value: {transfer_value / (10 ** 18)}, from {i} to {i + 1}')
        account = from_mnemonic(i)
        next_account = from_mnemonic(i + 1)
        tx = {
            'nonce': w3.eth.get_transaction_count(Web3.to_checksum_address(account.address)),
            'to': Web3.to_checksum_address(next_account.address),
            'value': transfer_value,
            'gas': 1000000,
            'gasPrice': w3.eth.gas_price
        }
        signed_tx = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        global_logger.info(w3.to_hex(tx_hash))
        time.sleep(3 * 60)

        # transfer_value = ether_balance - 10**16
        # transfer_value = 10**15
        # WethWrapper.deposit(account, w3, value=transfer_value)
        # Erc20Utils.transfer_token(w3, account, TokenAddress.weth.value, next_account.address, transfer_value)


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


def okx_withdraw_eth_to_lite(address: str, amount: str = '0.01'):
    sleep_some_seconds(min_seconds=1, max_seconds=5)
    res = fundingAPI.withdrawal('ETH', amount, '4', address, '0.0002', "ETH-zkSync Lite")
    global_logger.info(res)


def get_deposit_amount() -> str:
    return f'{(random.randint(95, 110)) / 10000}'


async def withdraw_from_okx():
    # okx提币
    idxs = []
    idxs.extend(list(range(472, 501)))
    idxs.extend(list(range(601, 841)))
    # for i in idxs:
    #     if i % 2:
    #         global_logger.info(f'skip {i} for it"s not even')
    #         continue
    #
    #     global_logger.info(f'==============> exec {i} <================')
    #     account: LocalAccount = from_mnemonic(i)
    #     # balance = await ZKSyncLiteUtils.get_balance(account=account)
    #     # if balance < 0.015 * 10 ** 18:
    #
    #     amount = get_deposit_amount()
    #     global_logger.info(f'withdraw {amount} to {i} , address: {account.address}')
    #     okx_withdraw_eth_to_lite(account.address, amount=get_deposit_amount())

    cnt = 0
    for i in idxs:
        if i % 2:
            if cnt > 65:
                return

            global_logger.info(f'==============> exec {i} <================')
            account: LocalAccount = from_mnemonic(i)
            # balance = await ZKSyncLiteUtils.get_balance(account=account)
            # if balance < 0.015 * 10 ** 18:

            amount = get_deposit_amount()
            global_logger.info(f'withdraw {amount} to {i} , address: {account.address}')
            okx_withdraw_eth_to_lite(account.address, amount=get_deposit_amount())
            cnt += 1


def claim_range():
    idxs = []
    idxs.extend(list(range(0, 841)))
    idxs.extend([1500, 1501, 1502, 2012])

    for i in idxs:
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

            # if not random.randint(0, 4):
            #     time.sleep(1)
            #     account: LocalAccount = from_mnemonic(i)
            #     approved = SyncSwap.checking_token_approved(account, w3, TokenAddress.zat.value)
            #     if not approved:
            #         global_logger.info(f'approve idx#{i}')
            #         zat_balance = ZksyncEraUtils.get_balance(account=account, token_address=TokenAddress.zat.value)
            #         SyncSwap.approve_token(account, w3, TokenAddress.zat.value, zat_balance)
        except Exception as e:
            global_logger.error(e)
            global_logger.info(f"{'*' * 100} {i} {'*' * 100}")

        time.sleep(1.3)


def sell_zat():
    # 卖掉 714～840的偶数的账号（基数没有余额，需要给基数的转）
    # idxs = list(range(0, 499))
    # idxs.extend(list(range(600, 841)))
    # idxs.extend([1500, 1501, 1502, 2012])
    idxs = [695, 439, 303, 21, 25, 161, 267, 145, 423, 411, 377, 437, 227, 165, 41, 677, 429, 453, 601, 801, 151, 195, 603, 647, 13, 283, 33, 167, 193, 637, 139, 15, 27, 43, 805, 215, 131, 433, 487, 773, 147, 729, 225, 435, 745, 35, 99, 229, 37, 11, 181, 331, 681, 173, 723, 3, 231, 223, 415, 171, 205, 721, 5]
    for _ in range(5):
        random.shuffle(idxs)

    for i in idxs:
        global_logger.info(f'start to sell {i}....')
        ZksyncEraUtils.sell_zat_token(idx=i, force=True)
        sleep_some_seconds(1, 3)
        # if i == 840:
        #     to_account = from_mnemonic(1500)
        # else:
        #     to_account = from_mnemonic(i+1)


def approve_zat():
    # 714～840的偶数的账号（基数没有余额，需要给基数的转）
    idxs = list(range(714, 841))
    for _ in range(5):
        random.shuffle(idxs)

    for i in idxs:
        if i % 2:
            continue

        global_logger.info(f'start to approve {i}....')
        account: LocalAccount = from_mnemonic(i)

        zat_balance = ZksyncEraUtils.get_balance(account=account, token_address=TokenAddress.zat.value)
        if zat_balance < 50 * 10 ** 18:
            global_logger.error(f'you do not have zat token, just skip...')
            return False

        SyncSwap.approve_token(account, w3, TokenAddress.zat.value)
        time.sleep(1)


def do_transfer_eth():
    # 714～840中的偶数，转给 它的+1。。最后的840就给 1500 吧
    # 714～840的偶数的账号（基数没有余额，需要给基数的转）
    idxs = list(range(714, 841))
    for _ in range(5):
        random.shuffle(idxs)

    for i in idxs:
        if i % 2:
            continue

        global_logger.info(f'start to transfer {i}....')
        from_account: LocalAccount = from_mnemonic(i)
        if i == 840:
            to_account: LocalAccount = from_mnemonic(1500)
        else:
            to_account: LocalAccount = from_mnemonic(i + 1)

        balance = ZksyncEraUtils.get_balance(to_account)
        if balance > 0:
            global_logger.info(f'{i + 1} or 1500 already have balance, just skip')
            continue

        transfer_eth(from_account, to_account.address, float(f'0.00{random.randint(20, 40)}'))
        time.sleep(1.5)


def print_if_sold(idx_if_sold_dict: Dict[int, bool]):
    me_sold, me_unsold, he_sold, he_unsold = 0, 0, 0, 0
    me_unsolds, he_unsolds = [], []
    for i, sold in idx_if_sold_dict.items():
        if 500 <= i < 600 and sold:
            he_sold += 1
        elif 500 <= i < 600 and not sold:
            he_unsold += 1
            he_unsolds.append(i)
        elif sold:
            me_sold += 1
        else:
            me_unsold += 1
            me_unsolds.append(i)
    global_logger.info(f'me_sold: {me_sold}, me_unsold: {me_unsold}, he_sold: {he_sold}, he_unsold: {he_unsold}')
    global_logger.info(f'me_unsolds: {me_unsolds}, he_unsolds: {he_unsolds}')


def check_sold():
    idxs = list(range(0, 499))
    idxs.extend(list(range(600, 841)))
    idxs.extend([1500, 1501, 1502, 2012])
    idx_if_sold_dict: Dict[int, bool] = {}

    for _ in range(5):
        random.shuffle(idxs)

    while idxs:
        i = idxs.pop()
        global_logger.info(f'checking {i}')
        account: LocalAccount = from_mnemonic(i)

        sold = False
        zat_balance = ZksyncEraUtils.get_balance(account=account, token_address=TokenAddress.zat.value)
        if zat_balance < 50 * 10 ** 18:
            global_logger.info(f'you do not have zat token, just skip...')
            sold = True
        idx_if_sold_dict.update({
            i: sold
        })

        print_if_sold(idx_if_sold_dict)
        global_logger.info(idxs)

        sleep_some_seconds(1, 10)


async def main():
    # await withdraw_from_okx()
    # claim_range()
    sell_zat()
    # approve_zat()
    # do_transfer_eth()

    # check_sold()


if __name__ == '__main__':
    asyncio.run(main())

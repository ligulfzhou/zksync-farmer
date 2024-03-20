import re
import time
import random
import datetime
import asyncio
from os import path
from typing import List
from web3.types import TxReceipt

from layer2.lib.rs import rs
from layer2.logger import global_logger
from layer2.erc20_utils import Erc20Utils
from layer2.config.config import conf
from layer2.lib.l1_utils import from_mnemonic
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.assets.assets import get_abi
from zksync2.manage_contracts.paymaster_utils import PaymasterFlowEncoder
from zksync2.module.module_builder import ZkSyncBuilder
from zksync2.core.types import EthBlockParams, PaymasterParams, HexStr
from eth_account import Account
from eth_account.signers.local import LocalAccount
from zksync2.signer.eth_signer import PrivateKeyEthSigner
from zksync2.transaction.transaction_builders import (
    TxFunctionCall,
)


def sleep_random_seconds():
    time.sleep(random.randint(5 * 60, 15 * 60))


def save_transaction_time_of_account(account: LocalAccount):
    ts = int(datetime.datetime.utcnow().timestamp())
    rs.set(f'{account.address}_last_transaction_timestamp', ts)


def save_transaction_types_of_account(account: LocalAccount, transaction_type: str):
    rs.rpush(f'{account.address}_transaction_types', transaction_type)


def get_done_transaction_types_of_account(account: LocalAccount) -> List[str]:
    res = rs.lrange(f'{account.address}_transaction_types', 0, -1)
    return [i.decode() for i in res]


usdc_token: str = '0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4'


async def approve_mute(account: LocalAccount, token_address: str = usdc_token,
                       contract_address: str = '0x8B791913eB07C32779a16750e3868aA8495F5964',
                       paymaster_address: str = '0x4ae2Ba9A5C653038C6d2F5D9F80B28011A454597',
                       allowance: int = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)-> bool:
    print('approve mute ..')

    zk_web3 = ZkSyncBuilder.build(conf.get_zksync_rpc())
    token_address = zk_web3.to_checksum_address(token_address)
    contract_address = zk_web3.to_checksum_address(contract_address)

    if Erc20Utils.checking_token_totally_approved(zk_web3, account, token_address, contract_address):
        print(f" account#{account.address} already approved...just skip...")
        return False

    chain_id = zk_web3.zksync.chain_id
    signer = PrivateKeyEthSigner(account, chain_id)
    nonce = zk_web3.zksync.get_transaction_count(account.address, EthBlockParams.PENDING.value)
    gas_price = zk_web3.zksync.gas_price

    erc_20_abi = get_abi('erc20.json')
    token_contract = zk_web3.eth.contract(address=token_address, abi=erc_20_abi)
    call_data = token_contract.encodeABI(fn_name="approve", args=[contract_address, allowance])
    print(f"CALLDATA: {call_data}")

    paymaster_params = PaymasterParams(
        paymaster=HexStr(paymaster_address),
        paymaster_input=zk_web3.to_bytes(
            hexstr=HexStr(PaymasterFlowEncoder(zk_web3).encode_approval_based(
                token_address,
                allowance,
                b''
            )[2:]))
    )
    print(f"paymaster_params {paymaster_params}")

    tx_func_call = TxFunctionCall(
        chain_id=chain_id,
        nonce=nonce,
        from_=zk_web3.to_checksum_address(account.address),
        to=token_address,
        data=HexStr(call_data),
        gas_limit=300_0000,
        max_priority_fee_per_gas=0,
        gas_price=gas_price,
        paymaster_params=paymaster_params,
    )
    print(f"tx_func_call {tx_func_call.tx}")

    estimate_gas = zk_web3.zksync.eth_estimate_gas(tx_func_call.tx)
    print(f"estimate_gas {estimate_gas}")
    tx_712 = tx_func_call.tx712(estimate_gas)

    signed_message = signer.sign_typed_data(tx_712.to_eip712_struct())
    msg = tx_712.encode(signed_message)

    tx_hash = zk_web3.zksync.send_raw_transaction(msg)
    r: TxReceipt = zk_web3.zksync.wait_for_transaction_receipt(tx_hash)
    print(f'transaction hash: {zk_web3.to_hex(tx_hash)} \ntransaction status: {r}')

    return True

async def approve_syncswap(account: LocalAccount, token_address: str = usdc_token,
                           contract_address: str = '0x9B5def958d0f3b6955cBEa4D5B7809b2fb26b059',
                           paymaster_address: str = '0x0c08f298a75a090dc4c0bb4caa4204b8b9d156c1',
                           allowance: int = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)-> bool:
    print('approve_syncswap ..')

    zk_web3 = ZkSyncBuilder.build(conf.get_zksync_rpc())
    token_address = zk_web3.to_checksum_address(token_address)
    account_address = zk_web3.to_checksum_address(account.address)
    contract_address = zk_web3.to_checksum_address(contract_address)

    if Erc20Utils.checking_token_totally_approved(zk_web3, account, token_address, contract_address):
        print(f" account#{account.address} already approved...just skip...")
        return False

    chain_id = zk_web3.zksync.chain_id
    signer = PrivateKeyEthSigner(account, chain_id)
    nonce = zk_web3.zksync.get_transaction_count(account.address, EthBlockParams.PENDING.value)
    gas_price = zk_web3.zksync.gas_price

    erc_20_abi = get_abi('erc20.json')
    token_contract = zk_web3.eth.contract(address=token_address, abi=erc_20_abi)
    call_data = token_contract.encodeABI(fn_name="approve", args=[contract_address, allowance])
    print(f"call_data: {call_data}")

    paymaster_params = PaymasterParams(
        paymaster=HexStr(paymaster_address),
        paymaster_input=zk_web3.to_bytes(hexstr=HexStr(
            '949431dc0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf40000000000000000000000000000000000000000000000000000000077359400000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000'))
    )

    print(f"paymaster_params {paymaster_params}")

    tx_func_call = TxFunctionCall(
        chain_id=chain_id,
        nonce=nonce,
        from_=account_address,
        to=token_address,
        data=HexStr(call_data),
        gas_limit=300_0000,
        max_priority_fee_per_gas=0,
        gas_price=gas_price,
        paymaster_params=paymaster_params,
    )
    print(f"tx_func_call {tx_func_call.tx}")

    estimate_gas = zk_web3.zksync.eth_estimate_gas(tx_func_call.tx)
    global_logger.info(f"ESTIMATEDGAS {estimate_gas}")
    tx_712 = tx_func_call.tx712(estimate_gas)

    signed_message = signer.sign_typed_data(tx_712.to_eip712_struct())
    global_logger.info(f"WOOOOO {signed_message}")
    msg = tx_712.encode(signed_message)
    print(msg)
    tx_hash = zk_web3.zksync.send_raw_transaction(msg)
    print(tx_hash)
    r: TxReceipt = zk_web3.zksync.wait_for_transaction_receipt(tx_hash)
    global_logger.info(f'transaction hash: {zk_web3.to_hex(tx_hash)} \ntransaction status: {r}')

    return True

def get_idx_already_paymasters() -> List[int]:
    with open(path.join(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))), "main.md")) as f:
        lines = f.readlines()

    idxs: List[int] = []
    for line in lines:
        if 'paymaster' in line:
            res = re.match(r'idx#(\d+):', line)
            if not res:
                continue

            res = res.groups()
            if not res:
                continue

            idxs.append(int(res[0]))

    return idxs


async def main():
    idxs = get_idx_already_paymasters()
    print(idxs)

    choices = []
    choices.extend(list(range(0, 841)))
    choices.extend(list(range(1500, 1503)))
    choices.append(2012)
    choices.append('473f28e4557f4a5eaaac93fd8dbd1d75c289a663e40fd830a3f9627a7c4b825a')

    for _ in range(10):
        random.shuffle(choices)

    while choices:
        time.sleep(random.randint(1, 5))
        i = choices.pop()
        if i in idxs:
            print(f'skip approve# {i}')
            continue

        global_logger.info(f'{"*" * 50} check_balance {i} {"*" * 50}')
        if type(i) == int:
            t: LocalAccount = from_mnemonic(idx=i)
        else:
            t: LocalAccount = Account.from_key(i)

        try:
            done_tts = get_done_transaction_types_of_account(t)
            paymaster_tts = [item for item in done_tts if item.startswith('paymaster')]
            if paymaster_tts:
                continue

            print(f"=======idx: {i} =======")
            defi = random.choice(['syncswap', 'mute'])

            usdc_balance = int(ZksyncEraUtils.get_balance(t, token_address=usdc_token))
            print(f'usdc balance: {usdc_balance / 10 ** 6}')
            if usdc_balance / 10 ** 6 <= 1.5:
                print('balance<1.5, just skip...')
                continue

            res = False
            if defi == 'syncswap':
                res = await approve_syncswap(t)
                save_transaction_types_of_account(t, 'paymaster_syncswap_approve')
            elif defi == 'mute':
                res = await approve_mute(t)
                save_transaction_types_of_account(t, 'mute_syncswap_approve')

            save_transaction_time_of_account(t)
            if res:
                sleep_random_seconds()
        except Exception as e:
            print(f'exception {e}')
            time.sleep(5)
            # choices.append(i)
            continue

        global_logger.info(choices)


if __name__ == '__main__':
    asyncio.run(main())

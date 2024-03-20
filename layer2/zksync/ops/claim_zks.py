"""
用于领取这个项目的免费域名 https://zks.network/
现在域名项目有点泛滥，领了其实也没啥用
好在免费，就当刷交互数
"""

import asyncio
import random

from web3 import Web3
from web3.types import TxReceipt
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.assets.assets import get_abi
from eth_account.signers.local import LocalAccount
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.common import sleep_some_seconds


GAS_LIMIT_IN_ETHER = 0.00068


zks_claim_addr = '0xCBE2093030F485adAaf5b61deb4D9cA8ADEAE509'
zks_resolver_addr = '0xCc788c0495894C01F01cD328CF637c7C441Ee69E'
zks_claim_abi = get_abi("zks_network.json")
zks_resolver_abi = get_abi('zks_network_2.json')


w3 = ZksyncEraUtils.get_w3_cli()


def check_if_claimed(idx) -> bool:
    account: LocalAccount = from_mnemonic(idx)
    contract = w3.eth.contract(address=Web3.to_checksum_address(zks_claim_addr), abi=zks_claim_abi)
    claimed = contract.functions.claimed(Web3.to_checksum_address(account.address)).call()
    return claimed


def claim(idx):
    account: LocalAccount = from_mnemonic(idx)
    contract = w3.eth.contract(address=Web3.to_checksum_address(zks_claim_addr), abi=zks_claim_abi)
    resolver_contract = w3.eth.contract(address=Web3.to_checksum_address(zks_resolver_addr), abi=zks_resolver_abi)

    while True:
        res = resolver_contract.functions.getOwnedDomains(Web3.to_checksum_address(account.address)).call()
        if not len(res):
            global_logger.error('invalid...')
            sleep_some_seconds(10, 100)
            continue

        token_ids, names = res[0], res[1]
        if len(token_ids) or len(names):
            global_logger.info(f'idx#{idx} , address#{account.address} already registered...just skip...')
            primary_id = resolver_contract.functions.getPrimaryDomainId(Web3.to_checksum_address(account.address)).call()
            if not primary_id:
                tx_hash = resolver_contract.functions.setPrimaryDomain(token_ids[0]).build_transaction({
                    'value': 0,
                    'from': Web3.to_checksum_address(account.address),
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'gasPrice': w3.eth.gas_price,
                })
                gas_estimate = w3.eth.estimate_gas(tx_hash)
                gas_price = w3.eth.gas_price
                gas_fee = gas_estimate * gas_price
                global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

                if gas_fee > GAS_LIMIT_IN_ETHER*10**18:
                    global_logger.error('😤gas too high, just skip...')
                    break

                signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                global_logger.info(f'🚀transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
            else:
                global_logger.info(f'🚀-----skip idx#{idx}, domain claimed and primary domain set...--------')
            sleep_some_seconds(10, 100)
            break

        name = random.randint(0, 99999)
        name = f"{name}"
        if len(name) < 5:
            name = '0'*(5-len(name)) + name

        global_logger.info(f'choose name: {name}')
        res = contract.functions.canRegister(name, Web3.to_checksum_address(account.address)).call()
        if not res[0] or not res[1]:
            global_logger.info(res)
            sleep_some_seconds(1, 10)
            continue

        tx_hash = contract.functions.register(
            name,
            Web3.to_checksum_address(account.address),
            1
        ).build_transaction({
            'value': 0,
            'from': Web3.to_checksum_address(account.address),
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price,
        })

        gas_estimate = w3.eth.estimate_gas(tx_hash)
        gas_price = w3.eth.gas_price
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')
        if gas_fee > GAS_LIMIT_IN_ETHER*10**18:
            global_logger.error('😤gas too high, just skip...')
            break

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'🚀transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        sleep_some_seconds(10, 100)
        break


def claim_range():
    idxs = []
    idxs.extend(list(range(0, 841)))
    idxs.extend([1500, 1501, 1502, 2012])

    for _ in range(5):
        random.shuffle(idxs)

    while idxs:
        idx = idxs.pop()
        try:
            claim(idx)
            global_logger.info(idxs)
        except Exception as e:
            global_logger.error(e)
            global_logger.info(f"{'*'*100} {idx} {'*'*100}")


async def main():
    claim_range()


if __name__ == '__main__':
    asyncio.run(main())

"""
这项目(dogera)免费可以领空投
但代码没写好就抢完了，没有啥必要看
"""

from web3 import Web3
from web3.types import TxReceipt
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.assets.assets import get_abi
from eth_account.signers.local import LocalAccount
from layer2.consts import GAS_LIMIT_IN_ETHER
from layer2.zksync.zksync_era_utils import ZksyncEraUtils

ref_account = Web3.to_checksum_address('0x2A0CFDe00155b19a7Cf625c1c68d905e55adcf7b')
token_addresss = Web3.to_checksum_address('0xA59af353E423F54D47F2Ce5F85e3e265d95282Cd')
amount = 80000_00000


def claim(idx: int):
    w3 = ZksyncEraUtils.get_w3_cli()

    account: LocalAccount = from_mnemonic(idx)
    account_address = Web3.to_checksum_address(account.address)
    abi = get_abi('dogera.json')
    dogera_contract = w3.eth.contract(address=token_addresss, abi=abi)
    can_claim = dogera_contract.functions.canClaim(account_address).call()
    if not can_claim:
        global_logger.info(f'{idx}#{account_address} can not claim, just skip....')
        return

    claimed = dogera_contract.functions.claimed(account_address).call()
    if not claimed:
        global_logger.info(f'{idx}#{account_address} already claimed, just skip....')
        return

    global_logger.info(f'-----------------------start to claim {idx}#{account_address}-----------------------')

    tx_hash = dogera_contract.functions.mint(
        ref_account,

    ).build_transaction({
        'from': Web3.to_checksum_address(account.address),
        'nonce': w3.eth.get_transaction_count(account.address),
        'gasPrice': w3.eth.gas_price,
    })

    gas_estimate = w3.eth.estimate_gas(tx_hash)
    gas_price = w3.eth.gas_price
    gas_fee = gas_estimate * gas_price
    global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

    if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
        global_logger.error("gas price too high, just skip...")
        return False

    signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')


def main():
    for idx in range():
        pass


if __name__ == '__main__':
    main()

import random
from web3 import Web3
from web3.types import TxReceipt
from layer2.lib.l1_utils import from_mnemonic
from eth_account.signers.local import LocalAccount
from layer2.logger import global_logger
from layer2.assets.assets import get_abi
from layer2.l0.common import sleep_common_interaction_gap

arb_rpc = 'https://arbitrum-mainnet.infura.io/v3/786649a580e3441f996da22488a8742a'
arb_w3 = Web3(Web3.HTTPProvider(arb_rpc))

arb_bungee_refuel_contract = '0xc0e02aa55d10e38855e13b64a8e1387a04681a00'

bungee_abi = get_abi('l0/bungee.json')

celo_or_genosis_minimum_balance = 0.02 * 10 ** 18


def arb_refuel_to_gnosis(account: LocalAccount):
    account_address = Web3.to_checksum_address(account.address)
    bungee = arb_w3.eth.contract(Web3.to_checksum_address(arb_bungee_refuel_contract), abi=bungee_abi)
    gas_price = arb_w3.eth.gas_price

    random_amount = random.randint(500, 800) / 1000000
    random_amount_in_wei = int(random_amount * 10 ** 18)

    tx = bungee.functions.depositNativeToken(
        100,
        account_address
    ).build_transaction({
        'from': account_address,
        'nonce': arb_w3.eth.get_transaction_count(account_address),
        'gasPrice': int(gas_price * 1.005),
        'value': random_amount_in_wei
    })
    gas_estimate = arb_w3.eth.estimate_gas(tx)
    gas_fee = gas_estimate * gas_price
    global_logger.info(f'estimate gas: {gas_fee}')

    signed_tx = arb_w3.eth.account.sign_transaction(tx, private_key=account.key)
    tx_hash = arb_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    r: TxReceipt = arb_w3.eth.wait_for_transaction_receipt(tx_hash)
    global_logger.info(f'transaction hash: {arb_w3.to_hex(tx_hash)} , status: {r.status}')
    sleep_common_interaction_gap()


if __name__ == '__main__':
    arb_refuel_to_gnosis(from_mnemonic(200))

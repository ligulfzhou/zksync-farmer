import random, time
from web3 import Web3
from web3.types import TxReceipt
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from eth_account.signers.local import LocalAccount
from layer2.assets.assets import get_abi
from layer2.zksync.zksync_era_utils import ZksyncEraUtils

w3 = ZksyncEraUtils.get_w3_cli()

abi = get_abi("pixelcase.json")
contract_addr = '0x1ec43b024A1C8D084BcfEB2c0548b6661C528dfA'


def mint(account: LocalAccount):
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=abi)
    tx_hash = contract.functions.mint().build_transaction({
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


if __name__ == '__main__':
    choices = []
    choices.extend(list(range(1, 841)))
    choices.extend(list(range(1500, 1503)))
    choices.append(2012)

    for _ in range(5):
        random.shuffle(choices)

    while len(choices):
        i = choices.pop()
        if i in (175, 654, 355) or 500 <= i <= 599:
            continue

        account: LocalAccount = from_mnemonic(i)
        try:
            mint(account)
        except Exception as e:
            global_logger.error(f'idx#{i} failed with {e}')

        global_logger.info(choices)
        time.sleep(random.randint(1, 5))

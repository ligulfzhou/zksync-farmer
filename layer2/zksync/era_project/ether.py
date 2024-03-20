from web3 import Web3
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.consts import GAS_LIMIT_IN_ETHER, TokenAddress


class Ether:

    @classmethod
    def transfer_to_self(cls, account: LocalAccount, w3: Web3, value: int = int(0.05 * 10 ** 18)) -> bool:
        global_logger.info(f'{"*" * 10} transfer {value}(in wei) eth to self {"*" * 10}')

        account_address = Web3.to_checksum_address(account.address)
        weth_contract = w3.eth.contract(address=Web3.to_checksum_address(TokenAddress.weth.value), abi=weth_abi)

        gas_price = w3.eth.gas_price
        tx_hash = weth_contract.functions.deposit().build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'value': value,
            'gas': 1000000,
        })

        gas_estimate = w3.eth.estimate_gas(tx_hash)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')
        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.info("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

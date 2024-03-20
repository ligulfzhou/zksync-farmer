import random
from web3 import Web3
from web3.types import TxReceipt, HexStr
from eth_account.signers.local import LocalAccount
from eth_account import Account
from typing import Optional

from layer2.config.config import conf
from layer2.logger import global_logger
from layer2.assets.assets import get_abi
from layer2.consts import GAS_LIMIT_IN_ETHER


class AccountDeployer:
    CONTRACT_ADDRESS = '0x0000000000000000000000000000000000008006'

    @classmethod
    def deploy_account(cls, w3: Web3, account: Optional[LocalAccount] = None) -> bool:
        account_address = Web3.to_checksum_address(account.address)

        contract_address = w3.to_checksum_address(cls.CONTRACT_ADDRESS)
        contract_abi = get_abi('zksync_contract_deployer.json')

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        res = contract.functions.getNewAddressCreate(account_address, 0).call()
        print(res)

        gas_price = w3.eth.gas_price
        tx_hash = contract.functions.create(
            Web3.to_bytes(b"\0" * 32),
            Web3.to_bytes(hexstr=HexStr('0x01000021a88a3dee3b0944ff9cbf36cb51c26df19b404d38a115a2a2e3ee5b88')),
            b''
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'gas': random.randint(1700_0000, 2000_0000),
        })

        gas_estimate = w3.eth.estimate_gas(tx_hash)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True


if __name__ == '__main__':
    rpc_host = conf.get_zksync_rpc()
    # global_logger.info(f'choose zksync-era rpc host: {rpc_host}')
    w3 = Web3(Web3.HTTPProvider(rpc_host))
    w3.eth.account.enable_unaudited_hdwallet_features()

    AccountDeployer.deploy_account(
        account=Account.from_key('....'),
        w3=w3
    )

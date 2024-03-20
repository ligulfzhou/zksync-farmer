from web3 import Web3
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.lib.rs import get_ipfs_url
from layer2.assets.assets import get_abi
from layer2.consts import GAS_LIMIT_IN_ETHER


class MintSquare:

    @classmethod
    def mint_nft(cls, account: LocalAccount, w3: Web3) -> bool:
        contractAds = Web3.to_checksum_address('0x53eC17BD635F7A54B3551E76Fd53Db8881028fC3')
        abi = get_abi('mintsquare/mintsquare.json')

        mintContract = w3.eth.contract(address=contractAds, abi=abi)
        gas_price = w3.eth.gas_price

        ipfs_url = get_ipfs_url()
        tx_hash = mintContract.functions.mint(ipfs_url).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': gas_price,
            'gas': 3385066,
            "value": w3.to_wei(0, 'ether')
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

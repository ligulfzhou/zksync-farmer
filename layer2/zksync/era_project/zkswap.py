import pdb
import time
import random
from web3 import Web3
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.assets.assets import get_abi
from layer2.erc20_utils import Erc20Utils
from layer2.consts import GAS_LIMIT_IN_ETHER, TokenAddress


class Zkswap:
    router_address = '0x18381c0f738146Fb694DE18D1106BdE2BE040Fa4'

    @classmethod
    def eth_to_usdc(cls, account: LocalAccount, w3: Web3, value: int = 10 ** 16) -> bool:
        account_address = Web3.to_checksum_address(account.address)
        abi = get_abi('spacefi/spacefi.json')
        router_contract_address = w3.to_checksum_address(cls.router_address)
        router_contract = w3.eth.contract(address=router_contract_address, abi=abi)

        '''
        function swapExactETHForTokens(uint256 amountOutMin, route[] paths, address to, uint256 deadline)

        0x67ffb66a
        0000000000000000000000000000000000000000000000000000000000000000
        0000000000000000000000000000000000000000000000000000000000000080
        0000000000000000000000006cf6041f889f24e3ebf7344968ea21636fd729b6
        00000000000000000000000000000000000000000000000000000000649c4263
        0000000000000000000000000000000000000000000000000000000000000001
        0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4
        0000000000000000000000000000000000000000000000000000000000000000
        
        0x7ff36ab5
        00000000000000000000000000000000000000000000000000000000039fd6cf
        0000000000000000000000000000000000000000000000000000000000000080
        0000000000000000000000007a89db90dc3f2019bb1f9d71d7a5670cdb75b40d
        0000000000000000000000000000000000000000000000000000000065e832f9
        0000000000000000000000000000000000000000000000000000000000000002
        0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        000000000000000000000000493257fd37edb34451f62edf8d2a0c418852ba4c
        0x7ff36ab5
        0000000000000000000000000000000000000000000000000000000000000000
        0000000000000000000000000000000000000000000000000000000000000080
        000000000000000000000000235ecd79486fcb420ba536c197905d52360ed2f1
        0000000000000000000000000000000000000000000000000000000065e83072
        0000000000000000000000000000000000000000000000000000000000000002
        0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4
        '''
        gas_price = w3.eth.gas_price

        tx = router_contract.functions.swapExactETHForTokens(
            0,
            (
                Web3.to_checksum_address(TokenAddress.weth.value),
                Web3.to_checksum_address(TokenAddress.usdc.value)
            ),
            account_address,
            w3.to_wei(int(time.time()) + 1800, 'wei'),
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'value': value,
            'gas': 1000000,
        })

        gas_estimate = w3.eth.estimate_gas(tx)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Zkswap eth=>usdc: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def usdc_to_eth_bk(cls, account: LocalAccount, w3: Web3, value: int = 10 * 10 ** 6) -> bool:
        account_address = Web3.to_checksum_address(account.address)
        abi = get_abi('spacefi/spacefi.json')
        router_contract_address = w3.to_checksum_address(cls.router_address)
        router_contract = w3.eth.contract(address=router_contract_address, abi=abi)
        '''
        function swapExactTokensForETH(uint256 amountIn, uint256 amountOutMin, route[] calldata routes, address to, uint256 deadline)
        
        0x18cbafe5
        000000000000000000000000000000000000000000000000000000000155b3f3
        00000000000000000000000000000000000000000000000000318eac9b8c6d17
        00000000000000000000000000000000000000000000000000000000000000a0
        0000000000000000000000002a0cfde00155b19a7cf625c1c68d905e55adcf7b
        00000000000000000000000000000000000000000000000000000000650e55aa
        0000000000000000000000000000000000000000000000000000000000000002
        0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4
        0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        '''

        gas_price = w3.eth.gas_price
        tx = router_contract.functions.swapExactTokensForETH(
            value,
            (
                Web3.to_checksum_address(TokenAddress.usdc.value),
                Web3.to_checksum_address(TokenAddress.weth.value),
            ),
            account_address,
            w3.to_wei(int(time.time()) + 1800, 'wei'),
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'gas': 1000000,
        })

        gas_estimate = w3.eth.estimate_gas(tx)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Zkswap eth=>usdc: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def usdc_to_eth(cls, account: LocalAccount, w3: Web3, value: int = 10 * 10 ** 6) -> bool:
        account_address = Web3.to_checksum_address(account.address)
        abi = get_abi('zkswap/zkswap.json')
        router_contract_address = w3.to_checksum_address(cls.router_address)
        router_contract = w3.eth.contract(address=router_contract_address, abi=abi)
        '''
        function swapExactTokensForETH(uint256 amountIn, uint256 amountOutMin, route[] path, address to, uint256 deadline)
        
        0x18cbafe5
        000000000000000000000000000000000000000000000000000000000155b3f3
        00000000000000000000000000000000000000000000000000318eac9b8c6d17
        00000000000000000000000000000000000000000000000000000000000000a0
        0000000000000000000000002a0cfde00155b19a7cf625c1c68d905e55adcf7b
        00000000000000000000000000000000000000000000000000000000650e55aa
        0000000000000000000000000000000000000000000000000000000000000002
        0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4
        0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        function swapExactTokensForETH(uint amountIn,uint amountOutMin,address[] path,address to,uint deadline) external virtual override ensureNotExpired(deadline) returns (uint[] memory amounts)
        0x7ff36ab5
        00000000000000000000000000000000000000000000000000000000020c2d9f
        0000000000000000000000000000000000000000000000000000000000000080
        000000000000000000000000235ecd79486fcb420ba536c197905d52360ed2f1
        0000000000000000000000000000000000000000000000000000000065e82f09
        0000000000000000000000000000000000000000000000000000000000000002
        0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4
        '''

        gas_price = w3.eth.gas_price
        tx = router_contract.functions.swapExactTokensForETH(
            value,
            0,
            (
                Web3.to_checksum_address(TokenAddress.usdc.value),
                Web3.to_checksum_address(TokenAddress.weth.value),
            ),
            account_address,
            w3.to_wei(int(time.time()) + 1800, 'wei'),
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'gas': 1000000,
        })

        gas_estimate = w3.eth.estimate_gas(tx)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'Zkswap eth=>usdc: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=account.key)
        pdb.set_trace()
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def checking_token_approved(cls, account: LocalAccount, w3: Web3, token_address: str) -> (bool, int):
        return Erc20Utils.checking_token_approved(w3, account, token_address, cls.router_address)

    @classmethod
    def approve_token(cls, account: LocalAccount, w3: Web3, token_address: str, count: int = 0) -> bool:
        if not count:
            count = random.randint(100, 200) * 10 ** 6

        return Erc20Utils.approve_token(w3, account, token_address, cls.router_address, count)

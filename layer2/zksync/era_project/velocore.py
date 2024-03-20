import time
import random
from web3 import Web3
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.assets.assets import get_abi
from layer2.erc20_utils import Erc20Utils
from layer2.consts import GAS_LIMIT_IN_ETHER, TokenAddress


class Velocore:

    ROUTER_CONTRACT_ADDRESS = '0xd999E16e68476bC749A28FC14a0c3b6d7073F50c'
    @classmethod
    def eth_to_usdc(cls, account: LocalAccount, w3: Web3, value: int = 10 ** 16) -> bool:
        account_address = Web3.to_checksum_address(account.address)
        abi = get_abi('velocore/velocore.json')
        router_contract_address = w3.to_checksum_address(cls.ROUTER_CONTRACT_ADDRESS)
        router_contract = w3.eth.contract(address=router_contract_address, abi=abi)

        '''
        function swapExactETHForTokens(uint256 amountOutMin, route[] calldata routes, address to, uint256 deadline)

        0x67ffb66a
        0000000000000000000000000000000000000000000000000000000000000000
        0000000000000000000000000000000000000000000000000000000000000080
        0000000000000000000000006cf6041f889f24e3ebf7344968ea21636fd729b6
        00000000000000000000000000000000000000000000000000000000649c4263
        0000000000000000000000000000000000000000000000000000000000000001
        0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4
        0000000000000000000000000000000000000000000000000000000000000000
        '''
        gas_price = w3.eth.gas_price

        tx = router_contract.functions.swapExactETHForTokens(
            0,
            [[
                Web3.to_checksum_address(TokenAddress.weth.value),
                Web3.to_checksum_address(TokenAddress.usdc.value),
                False
            ]],
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
        global_logger.info(f'Velocore eth=>usdc: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

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
        abi = get_abi('velocore/velocore.json')
        router_contract_address = w3.to_checksum_address(cls.ROUTER_CONTRACT_ADDRESS)
        router_contract = w3.eth.contract(address=router_contract_address, abi=abi)
        '''
        Execute (Bytes32[], Int128[], Bytes32, Bytes32[], Bytes, [])
        0xd3115a8a
        0000000000000000000000000000000000000000000000000000000000000060
        00000000000000000000000000000000000000000000000000000000000000c0
        0000000000000000000000000000000000000000000000000000000000000120
        0000000000000000000000000000000000000000000000000000000000000002
        0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4
        eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
        0000000000000000000000000000000000000000000000000000000000000002
        000000000000000000000000000000000000000000000000000000000385793d
        0000000000000000000000000000000000000000000000000000000000000000
        0000000000000000000000000000000000000000000000000000000000000002
        0000000000000000000000000000000000000000000000000000000000000040
        0000000000000000000000000000000000000000000000000000000000000140
        00000000000000000000000042d106c4a1d0bc5c482c11853a3868d807a3781d
        0000000000000000000000000000000000000000000000000000000000000060
        00000000000000000000000000000000000000000000000000000000000000c0
        0000000000000000000000000000000000000000000000000000000000000002
        000200000000000000000000000000007fffffffffffffffffffffffffffffff
        010100000000000000000000000000007fffffffffffffffffffffffffffffff
        0000000000000000000000000000000000000000000000000000000000000001
        0000000000000000000000000000000000000000000000000000000000000000
        0500000000000000000000000000000000000000000000000000000000000000
        0000000000000000000000000000000000000000000000000000000000000060
        00000000000000000000000000000000000000000000000000000000000000a0
        0000000000000000000000000000000000000000000000000000000000000001
        01010000000000000000000000000000ffffffffffffffffffac037b41ebf96e
        0000000000000000000000000000000000000000000000000000000000000001
        0000000000000000000000000000000000000000000000000000000000000000
        
        function swapExactTokensForETH(uint256 amountIn, uint256 amountOutMin, route[] calldata routes, address to, uint256 deadline)
        0x18a13086
        00000000000000000000000000000000000000000000000000000000030a4fdd
        00000000000000000000000000000000000000000000000000600991145825ee
        00000000000000000000000000000000000000000000000000000000000000a0
        000000000000000000000000e10964ee60f1de3314b992720f78f4180c318715
        00000000000000000000000000000000000000000000000000000f5a16f75510
        0000000000000000000000000000000000000000000000000000000000000001
        0000000000000000000000003355df6d4c9c3035724fd0e3914de96a5a83aaf4
        0000000000000000000000005aea5775959fbc2557cc8789bc1bf90a239d9a91
        0000000000000000000000000000000000000000000000000000000000000001
        '''

        gas_price = w3.eth.gas_price
        tx = router_contract.functions.swapExactTokensForETH(
            value,
            0,
            [[
                Web3.to_checksum_address(TokenAddress.usdc.value),
                Web3.to_checksum_address(TokenAddress.weth.value),
                False
            ]],
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
        global_logger.info(f'Velocore eth=>usdc: Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

        if gas_fee > GAS_LIMIT_IN_ETHER * (10 ** 18):
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def checking_token_approved(cls, account: LocalAccount, w3: Web3, token_address: str) -> (bool, int):
        return Erc20Utils.checking_token_approved(w3, account, token_address, cls.ROUTER_CONTRACT_ADDRESS)

    @classmethod
    def approve_token(cls, account: LocalAccount, w3: Web3, token_address: str, count: int = 0) -> bool:
        if not count:
            count = random.randint(100, 200) * 10 ** 6

        return Erc20Utils.approve_token(w3, account, token_address, cls.ROUTER_CONTRACT_ADDRESS, count)

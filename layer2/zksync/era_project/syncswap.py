import random
import time
from web3 import Web3
from eth_abi import encode
from web3.types import TxReceipt
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.config.config import conf
from layer2.assets.assets import get_abi
from layer2.erc20_utils import Erc20Utils
from layer2.consts import GAS_LIMIT_IN_ETHER, TokenAddress


class SyncSwap:

    @classmethod
    def zkpepe_to_eth(cls, account: LocalAccount, w3: Web3, value: int = 10 * 10 ** 18) -> bool:
        account_address = Web3.to_checksum_address(account.address)
        # usdc_ads = Web3.to_checksum_address(TokenAddress.usdc.value)
        zkpepe_ads = Web3.to_checksum_address('0x7D54a311D56957fa3c9a3e397CA9dC6061113ab3')
        weth_ads = Web3.to_checksum_address(TokenAddress.weth.value)
        zero_ads = Web3.to_checksum_address(TokenAddress.eth.value)

        # contract addresses: https://syncswap.gitbook.io/api-documentation/resources/smart-contract
        routerAds = Web3.to_checksum_address(conf.syncswap['address']['SyncSwapRouter'])
        poolFactoryAds = Web3.to_checksum_address(conf.syncswap['address']['SyncSwapClassicPoolFactory'])

        # abi https://syncswap.gitbook.io/api-documentation/resources/abis
        router_abi = get_abi('syncswap/SyncSwapRouter.json')
        pool_factory_abi = get_abi('syncswap/SyncSwapClassicFactory.json')

        # Pool Factory
        poolFactoryContract = w3.eth.contract(address=poolFactoryAds, abi=pool_factory_abi)

        pool = poolFactoryContract.functions.getPool(weth_ads, zkpepe_ads).call()
        global_logger.info(f'get pool address: {pool}')

        withdraw_mode = 1
        swap_data = encode(
            ["address", "address", "uint8"],  # tokenIn, to, withdraw mode
            [zkpepe_ads, account_address, withdraw_mode],
        )

        # struct SwapStep
        swap_step = [(
            pool,  # pool
            swap_data,  # data
            zero_ads,  # callback
            '0x'  # callbackData
        )]

        # struct SwapPath
        swap_path = [(
            swap_step,
            zkpepe_ads,
            value
        )]

        router_contract = w3.eth.contract(address=routerAds, abi=router_abi)
        deadline = w3.to_wei(int(time.time()) + 1800, 'wei')
        gas_price = w3.eth.gas_price
        tx_hash = router_contract.functions.swap(swap_path, 0, deadline).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'gas': 2000000,
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


    @classmethod
    def zat_to_eth(cls, account: LocalAccount, w3: Web3, value: int = 10 * 10 ** 18) -> bool:
        account_address = Web3.to_checksum_address(account.address)
        # usdc_ads = Web3.to_checksum_address(TokenAddress.usdc.value)
        zat_ads = Web3.to_checksum_address(TokenAddress.zat.value)
        weth_ads = Web3.to_checksum_address(TokenAddress.weth.value)
        zero_ads = Web3.to_checksum_address(TokenAddress.eth.value)

        # contract addresses: https://syncswap.gitbook.io/api-documentation/resources/smart-contract
        routerAds = Web3.to_checksum_address(conf.syncswap['address']['SyncSwapRouter'])
        poolFactoryAds = Web3.to_checksum_address(conf.syncswap['address']['SyncSwapClassicPoolFactory'])

        # abi https://syncswap.gitbook.io/api-documentation/resources/abis
        router_abi = get_abi('syncswap/SyncSwapRouter.json')
        pool_factory_abi = get_abi('syncswap/SyncSwapClassicFactory.json')

        # Pool Factory
        poolFactoryContract = w3.eth.contract(address=poolFactoryAds, abi=pool_factory_abi)

        pool = poolFactoryContract.functions.getPool(weth_ads, zat_ads).call()
        global_logger.info(f'get pool address: {pool}')

        withdraw_mode = 1
        swap_data = encode(
            ["address", "address", "uint8"],  # tokenIn, to, withdraw mode
            [zat_ads, account_address, withdraw_mode],
        )

        # struct SwapStep
        swap_step = [(
            pool,  # pool
            swap_data,  # data
            zero_ads,  # callback
            '0x'  # callbackData
        )]

        # struct SwapPath
        swap_path = [(
            swap_step,
            zat_ads,
            value
        )]

        router_contract = w3.eth.contract(address=routerAds, abi=router_abi)
        deadline = w3.to_wei(int(time.time()) + 1800, 'wei')
        gas_price = w3.eth.gas_price
        tx_hash = router_contract.functions.swap(swap_path, 0, deadline).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'gas': 2000000,
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

    @classmethod
    def usdc_to_eth(cls, account: LocalAccount, w3: Web3, value: int = 10 * 10 ** 6) -> bool:
        # default 10 * 10**6 => 10 usdc
        account_address = Web3.to_checksum_address(account.address)
        usdc_ads = Web3.to_checksum_address(TokenAddress.usdc.value)
        weth_ads = Web3.to_checksum_address(TokenAddress.weth.value)
        zero_ads = Web3.to_checksum_address(TokenAddress.eth.value)

        # contract addresses: https://syncswap.gitbook.io/api-documentation/resources/smart-contract
        routerAds = Web3.to_checksum_address(conf.syncswap['address']['SyncSwapRouter'])
        poolFactoryAds = Web3.to_checksum_address(conf.syncswap['address']['SyncSwapClassicPoolFactory'])

        # abi https://syncswap.gitbook.io/api-documentation/resources/abis
        router_abi = get_abi('syncswap/SyncSwapRouter.json')
        pool_factory_abi = get_abi('syncswap/SyncSwapClassicFactory.json')

        # Pool Factory
        poolFactoryContract = w3.eth.contract(address=poolFactoryAds, abi=pool_factory_abi)

        pool = poolFactoryContract.functions.getPool(weth_ads, usdc_ads).call()
        global_logger.info(f'get pool address: {pool}')

        withdraw_mode = 1
        swap_data = encode(
            ["address", "address", "uint8"],  # tokenIn, to, withdraw mode
            [usdc_ads, account_address, withdraw_mode],
        )

        # struct SwapStep
        swap_step = [(
            pool,  # pool
            swap_data,  # data
            zero_ads,  # callback
            '0x'  # callbackData
        )]

        # struct SwapPath
        swap_path = [(
            swap_step,
            usdc_ads,
            value
        )]

        router_contract = w3.eth.contract(address=routerAds, abi=router_abi)
        deadline = w3.to_wei(int(time.time()) + 1800, 'wei')
        gas_price = w3.eth.gas_price
        tx_hash = router_contract.functions.swap(swap_path, 0, deadline).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': gas_price,
            'gas': 2000000,
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

    @classmethod
    def eth_to_usdc(cls, account: LocalAccount, w3: Web3, value: int = 10 ** 16) -> bool:
        # default 10**16 => 0.01eth
        account_address = Web3.to_checksum_address(account.address)
        usdc_ads = Web3.to_checksum_address(TokenAddress.usdc.value)
        weth_ads = Web3.to_checksum_address(TokenAddress.weth.value)
        zero_ads = Web3.to_checksum_address(TokenAddress.eth.value)

        # contract addresses: https://syncswap.gitbook.io/api-documentation/resources/smart-contract
        routerAds = Web3.to_checksum_address(conf.syncswap['address']['SyncSwapRouter'])
        poolFactoryAds = Web3.to_checksum_address(conf.syncswap['address']['SyncSwapClassicPoolFactory'])

        # abi: https://syncswap.gitbook.io/api-documentation/resources/abis
        router_abi = get_abi('syncswap/SyncSwapRouter.json')
        pool_factory_abi = get_abi('syncswap/SyncSwapClassicFactory.json')

        # Pool Factory
        poolFactoryContract = w3.eth.contract(address=poolFactoryAds, abi=pool_factory_abi)
        pool = poolFactoryContract.functions.getPool(weth_ads, usdc_ads).call()
        global_logger.info(pool)

        withdraw_mode = 2
        swap_data = encode(
            ["address", "address", "uint8"],
            [weth_ads, account_address, withdraw_mode],
        )

        # struct SwapStep
        swap_step = [(
            pool,
            swap_data,
            zero_ads,
            '0x'
        )]

        # struct SwapPath
        swap_path = [(
            swap_step,
            zero_ads,
            value
        )]

        # SyncSwapRouter
        router_contract = w3.eth.contract(address=routerAds, abi=router_abi)
        deadline = w3.to_wei(int(time.time()) + 1800, 'wei')
        gas_price = w3.eth.gas_price
        tx_hash = router_contract.functions.swap(swap_path, 0, deadline).build_transaction({
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
            global_logger.error("gas price too high, just skip...")
            return False

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        return True

    @classmethod
    def checking_token_approved(cls, account: LocalAccount, w3: Web3, token_address: str) -> (bool, int):
        return Erc20Utils.checking_token_approved(w3, account, token_address,
                                                  conf.syncswap['address']['SyncSwapRouter'])

    @classmethod
    def approve_token(cls, account: LocalAccount, w3: Web3, token_address: str, count: int = 0) -> bool:
        if not count:
            count = random.randint(500, 2000) * 10 ** 6
        return Erc20Utils.approve_token(w3, account, token_address, conf.syncswap['address']['SyncSwapRouter'], count)

    @classmethod
    def add_liquidity(cls, account: LocalAccount, w3: Web3, count: int = 5 * 10 ** 6) -> bool:
        return False

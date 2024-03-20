from web3 import Web3
from typing import Optional
from layer2.config.config import conf
from layer2.lib.l1_utils import from_mnemonic
from layer2.lib.rs import allow_sell_usdc, allow_sell_eth
from eth_account.signers.local import LocalAccount
from layer2.assets.assets import get_abi
from layer2.consts import TokenAddress
from layer2.common import sleep_common_interaction_gap

from layer2.zksync.era_project.mintsquare import MintSquare
from layer2.zksync.era_project.syncswap import SyncSwap
from layer2.zksync.era_project.mute import Mute
from layer2.zksync.era_project.velocore import Velocore
from layer2.zksync.era_project.zkswap import Zkswap
from layer2.zksync.era_project.spacefi import SpaceFi
from layer2.zksync.era_project.draculafi import Draculafi
from layer2.zksync.era_project.approve_tokens import ApproveToken
from layer2.zksync.era_project.weth_wrapper import WethWrapper
from layer2.zksync.era_project.account import AccountDeployer

eth_to_left_for_wrap = 0.0015 * 10 ** 18
floor_amount_for_wrap = 0.004 * 10 ** 18
floor_amount_for_swap_weth_to_usdc = 0.0038 * 10 ** 18


# zat已经全卖掉了，这些数字也已经没用了
# sell_zat_if_eth_less_than_high_bar = 0.015 * 10 ** 18
# sell_zat_if_eth_less_than = 0.003 * 10 ** 18


class ZksyncEraUtils:

    @classmethod
    def get_w3_cli(cls) -> Web3:
        rpc_host = conf.get_zksync_rpc()
        # global_logger.info(f'choose zksync-era rpc host: {rpc_host}')
        w3 = Web3(Web3.HTTPProvider(rpc_host))
        w3.eth.account.enable_unaudited_hdwallet_features()
        return w3

    # @classmethod
    # def deploy_multi_sig(cls, account: Optional[LocalAccount] = None, idx: int = 0):
    #     if not account:
    #         account = from_mnemonic(idx=idx)
    #     pass

    # @classmethod
    # def transfer(cls, account: Optional[LocalAccount] = None, idx: int = 0):
    #     if not account:
    #         account = from_mnemonic(idx=idx)
    #     w3 = cls.get_w3_cli()
    #     eth_balance = w3.eth.get_balance(account.address)

    @classmethod
    def get_balance(cls, account: Optional[LocalAccount] = None, idx: int = 0, token_address: str = '') -> int:
        if not account:
            account = from_mnemonic(idx=idx)

        w3 = cls.get_w3_cli()
        if not token_address:
            balance = w3.eth.get_balance(account.address)
        else:
            erc_20_abi = get_abi('erc20.json')
            token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
            balance = token.functions.balanceOf(account.address).call()  # returns int with balance, without decimals
        return balance

    @classmethod
    def mint_nft(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        if not account:
            account = from_mnemonic(idx=idx)

        usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
        if usdc_balance > 1 * 10 ** 6:
            # 有usdc就让它去走swap，要是mint玩，eth不够了就不好了
            return False

        return MintSquare.mint_nft(account, cls.get_w3_cli())

    @classmethod
    def mute_swap(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
        if usdc_balance > 1 * 10 ** 6:
            if not allow_sell_usdc():
                return False

            approved, allowance = Mute.checking_token_approved(account, w3, TokenAddress.usdc.value)
            if not approved or allowance < usdc_balance or allowance > 100 * 10 ** 6:
                success = Mute.approve_token(account, w3, TokenAddress.usdc.value, usdc_balance)
                if not success:
                    return success

                sleep_common_interaction_gap()

            # do usdc=> eth
            success = Mute.usdc_to_eth(account, w3, usdc_balance)
        else:
            if not allow_sell_eth():
                return False

            eth_balance = cls.get_balance(account=account)
            if eth_balance < floor_amount_for_swap_weth_to_usdc:
                success = cls.wrap_unwrap_weth(account)
            else:
                success = Mute.eth_to_usdc(account, w3, int(eth_balance / 3 * 2))
        return success

    @classmethod
    def syncswap_swap(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
        if usdc_balance > 1 * 10 ** 6:
            if not allow_sell_usdc():
                return False

            approved, allowance = SyncSwap.checking_token_approved(account, w3, TokenAddress.usdc.value)
            if not approved or allowance < usdc_balance or allowance > 100 * 10 ** 6:
                success = SyncSwap.approve_token(account, w3, TokenAddress.usdc.value, usdc_balance)
                if not success:
                    return success

                sleep_common_interaction_gap()

            # do usdc=> eth
            success = SyncSwap.usdc_to_eth(account, w3, usdc_balance)
        else:
            if not allow_sell_eth():
                return False
            eth_balance = cls.get_balance(account=account)
            if eth_balance < floor_amount_for_swap_weth_to_usdc:
                success = cls.wrap_unwrap_weth(account)
            else:
                success = SyncSwap.eth_to_usdc(account, w3, int(eth_balance / 3 * 2))
        return success

    @classmethod
    def draculafi_swap(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
        if usdc_balance > 1 * 10 ** 6:
            if not allow_sell_usdc():
                return False

            approved, allowance = Draculafi.checking_token_approved(account, w3, TokenAddress.usdc.value)
            if not approved or allowance < usdc_balance or allowance > 100 * 10 ** 6:
                success = Draculafi.approve_token(account, w3, TokenAddress.usdc.value, usdc_balance)
                if not success:
                    return success

                sleep_common_interaction_gap()

            # do usdc=> eth
            success = Draculafi.usdc_to_eth(account, w3, usdc_balance)
        else:
            if not allow_sell_eth():
                return False
            eth_balance = cls.get_balance(account=account)
            if eth_balance < floor_amount_for_swap_weth_to_usdc:
                success = cls.wrap_unwrap_weth(account)
            else:
                success = Draculafi.eth_to_usdc(account, w3, int(eth_balance / 3 * 2))
        return success

    @classmethod
    def velocore_swap(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        if True:
            return False

        usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
        if usdc_balance > 1 * 10 ** 6:
            if not allow_sell_usdc():
                return False

            approved, allowance = Velocore.checking_token_approved(account, w3, TokenAddress.usdc.value)
            if not approved or allowance < usdc_balance or allowance > 100 * 10 ** 6:
                success = Velocore.approve_token(account, w3, TokenAddress.usdc.value, usdc_balance)
                if not success:
                    return success

                sleep_common_interaction_gap()

            # do usdc=> eth
            success = Velocore.usdc_to_eth(account, w3, usdc_balance)
        else:
            if not allow_sell_eth():
                return False
            eth_balance = cls.get_balance(account=account)
            if eth_balance < floor_amount_for_swap_weth_to_usdc:
                success = cls.wrap_unwrap_weth(account)
            else:
                success = Velocore.eth_to_usdc(account, w3, int(eth_balance / 3 * 2))
        return success

    @classmethod
    def account_create(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        return AccountDeployer.deploy_account(account=account, w3=w3)

    @classmethod
    def zkswap_swap(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
        if usdc_balance > 1 * 10 ** 6:
            if not allow_sell_usdc():
                return False

            approved, allowance = Zkswap.checking_token_approved(account, w3, TokenAddress.usdc.value)
            if not approved or allowance < usdc_balance or allowance > 100 * 10 ** 6:
                success = Zkswap.approve_token(account, w3, TokenAddress.usdc.value, usdc_balance)
                if not success:
                    return success

                sleep_common_interaction_gap()

            # do usdc=> eth
            success = Zkswap.usdc_to_eth(account, w3, usdc_balance)
        else:
            if not allow_sell_eth():
                return False
            eth_balance = cls.get_balance(account=account)
            if eth_balance < floor_amount_for_swap_weth_to_usdc:
                success = cls.wrap_unwrap_weth(account)
            else:
                success = Zkswap.eth_to_usdc(account, w3, int(eth_balance / 3 * 2))
        return success

    @classmethod
    def spacefi_swap(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
        if usdc_balance > 1 * 10 ** 6:
            if not allow_sell_usdc():
                return False

            approved, allowance = SpaceFi.checking_token_approved(account, w3, TokenAddress.usdc.value)
            if not approved or allowance < usdc_balance or allowance > 100 * 10 ** 6:
                success = SpaceFi.approve_token(account, w3, TokenAddress.usdc.value, usdc_balance)
                if not success:
                    return success

                sleep_common_interaction_gap()

            # do usdc=> eth
            success = SpaceFi.usdc_to_eth(account, w3, usdc_balance)
        else:
            if not allow_sell_eth():
                return False
            eth_balance = cls.get_balance(account=account)
            if eth_balance < floor_amount_for_swap_weth_to_usdc:
                success = cls.wrap_unwrap_weth(account)
            else:
                success = SpaceFi.eth_to_usdc(account, w3, int(eth_balance / 3 * 2))
        return success

    @classmethod
    def random_approve_token(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        return ApproveToken.approve_token(w3, account)

    @classmethod
    def wrap_unwrap_weth(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        w3 = cls.get_w3_cli()
        if not account:
            account = from_mnemonic(idx=idx)

        usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
        weth_balance = cls.get_balance(account=account, token_address=TokenAddress.weth.value)

        # 有usdc就让它去走swap，要是mint玩，eth不够了就不好了
        # if usdc_balance > 5 * 10 ** 6 and not weth_balance:
        #     return False
        # elif usdc_balance > 5 * 10 ** 6 and weth_balance:
        #     return WethWrapper.withdraw(account, w3, value=weth_balance)
        if weth_balance:
            return WethWrapper.withdraw(account, w3, value=weth_balance)

        eth_balance = cls.get_balance(account=account)
        if eth_balance > floor_amount_for_wrap:
            success = WethWrapper.deposit(account, w3, int(eth_balance - eth_to_left_for_wrap))
            if not success:
                return False

            sleep_common_interaction_gap()

        weth_balance = cls.get_balance(account=account, token_address=TokenAddress.weth.value)
        return WethWrapper.withdraw(account, w3, value=weth_balance)

    @classmethod
    def get_last_transaction_timestamp_of_account(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> int:
        if not account:
            account = from_mnemonic(idx=idx)

        # try:
        #     res = requests.get(f'https://zksync2-mainnet-explorer.zksync.io/transactions?limit=1&direction=older&accountAddress={account.address}').json()
        #     total = res['total']
        #     transactions = res['list']
        #     if not transactions and not total:
        #         return 0

        #     transaction = transactions[0]
        #     global_logger.info(f'last date: {transaction["receivedAt"]}')
        #     dt = datetime.datetime.strptime(transaction['receivedAt'][:19], '%Y-%m-%dT%H:%M:%S')
        #     return int(dt.timestamp())
        # except Exception as e:
        #     global_logger.error(f'------get_last_transaction_timestamp_of_account-------: {e}')
        #     time.sleep(5)
        return -1

    @classmethod
    def sell_zat_token(cls, account: Optional[LocalAccount] = None, idx: int = 0, force: bool = False,
                       low_bar: bool = False) -> bool:
        return True

    # @classmethod
    # def sell_zat_token(cls, account: Optional[LocalAccount] = None, idx: int = 0, force: bool = False,
    #                    low_bar: bool = False) -> bool:
    #     """
    #     won't used anymore...
    #     """
    #     w3 = cls.get_w3_cli()
    #     if not account:
    #         account = from_mnemonic(idx=idx)
    #
    #     zat_balance = cls.get_balance(account=account, token_address=TokenAddress.zat.value)
    #     if zat_balance < 50 * 10 ** 18:
    #         global_logger.info(f'you do not have zat token, just skip...')
    #         return False
    #
    #     zat_sell_bar = sell_zat_if_eth_less_than_high_bar
    #     if low_bar:
    #         zat_sell_bar = sell_zat_if_eth_less_than
    #     if not force:
    #         rich = False
    #         eth_balance = cls.get_balance(account=account)
    #         if eth_balance > zat_sell_bar:
    #             global_logger.info(f'your balance > {zat_sell_bar}, you are rich...')
    #             rich = True
    #
    #         usdc_balance = cls.get_balance(account=account, token_address=TokenAddress.usdc.value)
    #         if usdc_balance > 18 * 10 ** 6:
    #             global_logger.info(f'your usdc balance > 12u, you are rich...')
    #             rich = True
    #
    #         r = random.randint(0, 9)
    #         if rich and r:
    #             global_logger.info(f'if rich, and hit 90% not to sell zat, the r is {r}, just return...')
    #             return False
    #
    #         global_logger.info(f'address#{account.address} is not rich, sell zat token...')
    #
    #     approved, allowance = SyncSwap.checking_token_approved(account, w3, TokenAddress.zat.value)
    #     if not approved or allowance < zat_balance:
    #         success = SyncSwap.approve_token(account, w3, TokenAddress.zat.value, zat_balance)
    #         if not success:
    #             global_logger.info(f'approve zat token to syncswap failed. just return..')
    #             return False
    #         sleep_common_interaction_gap()
    #
    #     success = SyncSwap.zat_to_eth(account, w3, value=zat_balance)
    #     global_logger.info(f'syncswap: zat=>eth, result: {success}')
    #     return success

    @classmethod
    def sell_zkpepe(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
        return True

    # @classmethod
    # def sell_zkpepe(cls, account: Optional[LocalAccount] = None, idx: int = 0) -> bool:
    #     token_addr = '0x7D54a311D56957fa3c9a3e397CA9dC6061113ab3'
    #
    #     w3 = cls.get_w3_cli()
    #     if not account:
    #         account = from_mnemonic(idx=idx)
    #
    #     zkpepe_balance = cls.get_balance(account=account, token_address=token_addr)
    #     if zkpepe_balance < 50 * 10 ** 18:
    #         global_logger.info(f'you do not have zkpepe token, just skip...')
    #         return False
    #
    #     approved, allowance = SyncSwap.checking_token_approved(account, w3, token_addr)
    #     if not approved or allowance < zkpepe_balance:
    #         success = SyncSwap.approve_token(account, w3, token_addr, zkpepe_balance)
    #         if not success:
    #             global_logger.info(f'approve zkpepe token to syncswap failed. just return..')
    #             return False
    #         sleep_some_seconds(0, 10)
    #
    #     success = SyncSwap.zkpepe_to_eth(account, w3, value=zkpepe_balance)
    #     global_logger.info(f'syncswap: zkpepe=>eth, result: {success}')
    #     return success

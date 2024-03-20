import pdb

from layer2.consts import TokenAddress
from eth_account import Account
from eth_account.signers.local import LocalAccount

from layer2.erc20_utils import Erc20Utils
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.zksync.era_project.mintsquare import MintSquare
from layer2.zksync.era_project.syncswap import SyncSwap
from layer2.zksync.era_project.spacefi import SpaceFi
from layer2.zksync.era_project.mute import Mute
from layer2.zksync.era_project.velocore import Velocore
from layer2.zksync.era_project.zkswap import Zkswap
from layer2.zksync.era_project.approve_tokens import ApproveToken
from layer2.zksync.era_project.weth_wrapper import WethWrapper
from layer2.zksync.era_project.account import AccountDeployer


# def test_syncswap():
#     # account: LocalAccount = Account.from_key('...')
#   account: LocalAccount = Account.from_key('...')
#
#     balance = ZksyncEraUtils.get_balance(account)
#     global_logger.info(f'eth balance of {account.address}: {balance}')
#     balance = ZksyncEraUtils.get_balance(account, token_address=conf.syncswap['address']['USDC'])
#     global_logger.info(f'usdc balance of {account.address}: {balance}')
#
#     # ZksyncEraUtils.syncswap_eth_to_usdc(account=account, value_in_wei=int(balance / 2))
#
#     approved = ZksyncEraUtils.syncswap_checking_token_approved(account=account, token_address=conf.syncswap['address']['USDC'])
#     pdb.set_trace()
#     if not approved:
#         pdb.set_trace()
#         ZksyncEraUtils.syncswap_approve_token(account=account, token_address=conf.syncswap['address']['USDC'])


# def test_deposit_era_testnet():
#     account: LocalAccount = Account.from_key('...')
#
#     gas_price = w3.eth.gas_price
#     global_logger.info(gas_price)
#
#     L1Utils.deposit_zksync_era_testnet(account, value=1000000000000000)


# def test_mint_nft():
#     i = 50
#
#     w3 = ZksyncEraUtils.get_w3_cli()
#
#     account: LocalAccount = from_mnemonic(i)
#     nonce = w3.eth.get_transaction_count(account.address)
#     global_logger.info(f'{account.address} nonce: {nonce}...')
#
#     balance = w3.eth.get_balance(account.address)
#     global_logger.info(f'{account.address} balance: {balance}')
#
#     gas_price = w3.eth.gas_price
#     global_logger.info(f'gas_price: {gas_price}')
#
#     global_logger.info(f'xyz3 gas_price: {gas_price}')
#
#     pdb.set_trace()
#     ZksyncEraUtils.mint_nft(account)


# def mint_nft():
#     i = 100
#     w3 = ZksyncEraUtils.get_w3_cli()
#
#     account: LocalAccount = from_mnemonic(i)
#     nonce = w3.eth.get_transaction_count(account.address)
#     global_logger.info(f'{account.address} nonce: {nonce}...')
#
#     balance = w3.eth.get_balance(account.address)
#     global_logger.info(f'{account.address} balance: {balance}')
#
#     ZksyncEraUtils.mint_nft(account)

def t_swap():
    # testnet
    # account: LocalAccount = Account.from_key('...')

    # mainnet:
    account: LocalAccount = Account.from_key('...')
    ZksyncEraUtils.zkswap_swap(account)

    # ZksyncEraUtils.mute_swap(account)
    # ZksyncEraUtils.syncswap_swap(account)
    # ZksyncEraUtils.spacefi_swap(account)
    # ZksyncEraUtils.velocore_swap(account)


def new_syncswap_cls():
    account: LocalAccount = Account.from_key('...')
    ZksyncEraUtils.syncswap_swap(account)


def test_eth_weth():
    account: LocalAccount = Account.from_key('...')
    # ZksyncEraUtils.syncswap_swap(account)
    ZksyncEraUtils.wrap_unwrap_weth(account)


def main():
    # syncswap
    # new_syncswap_cls()

    w3 = ZksyncEraUtils.get_w3_cli()
    account: LocalAccount = from_mnemonic(52)
    nonce = w3.eth.get_transaction_count(account.address)
    global_logger.info(nonce)
    global_logger.info(account.address)

    approved = Erc20Utils.checking_token_totally_approved(w3, account, TokenAddress.usdc.value,
                                                          '0x9B5def958d0f3b6955cBEa4D5B7809b2fb26b059')
    print(approved)
    approved = Erc20Utils.checking_token_totally_approved(w3, account, TokenAddress.usdc.value,
                                                          '0x8B791913eB07C32779a16750e3868aA8495F5964')
    print(approved)
    # balance = ZksyncEraUtils.get_balance(account, token_address=TokenAddress.usdc.value)
    # Velocore.eth_to_usdc(account, w3)
    # ZksyncEraUtils.mute_swap(account)
    # ZksyncEraUtils.spacefi_swap(account)
    # ZksyncEraUtils.account_create(idx=460)
    # ZksyncEraUtils.zkswap_swap(account)
    # ZksyncEraUtils.velocore_swap(account)
    # Velocore.usdc_to_eth(account, w3, balance)
    # ZksyncEraUtils.sell_zat_token(account)
    # t_swap()
    # test_eth_weth()
    # t_swap()

    # test_deposit_era_testnet()

    # test_syncswap()

    # mint_nft()
    # test_mint_nft()

    # account: LocalAccount = Account.from_key('...')
    # ZKSyncLiteUtils.tranfer_nft_to_self(account=account)
    # ZKSyncLiteUtils.mint_nft(account=account)
    #
    # pdb.set_trace()
    #
    # layer_account = ZKSyncLiteUtils.get_account(idx=i)
    # ZKSyncLiteUtils.tranfer_nft_to_self(idx=i)
    # # pdb.set_trace()
    # ZKSyncLiteUtils.transfer_to_self(idx=i, value_in_eth=0)
    # ZKSyncLiteUtils.mint_nft(idx=i)
    # nonce = ZKSyncLiteUtils.get_nonce(idx=100)
    # global_logger.info(f'nonce: {nonce}')


if __name__ == '__main__':
    main()

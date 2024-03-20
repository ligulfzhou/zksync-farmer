"""
..abandoned..
"""
import asyncio
from eth_account import Account
from eth_account.signers.local import LocalAccount
from fractions import Fraction
from decimal import Decimal
from zksync_sdk.types import RatioType
from zksync_sdk import ZkSyncProviderV01, HttpJsonRPCTransport, network, ZkSync, EthereumProvider, Wallet, \
    ZkSyncSigner, EthereumSignerWeb3, ZkSyncLibrary

from layer2.lib.l1_utils import from_mnemonic, w3
from layer2.logger import global_logger
from layer2.config.config import conf


library = ZkSyncLibrary()
provider = ZkSyncProviderV01(provider=HttpJsonRPCTransport(network=network.mainnet))



# async def do_swap():
#     orderA = await walletA.get_order('USDT', 'ETH', Fraction(1500, 1), RatioType.token, Decimal('10.0'))
#     orderB = await walletB.get_order('ETH', 'USDT', Fraction(1, 1200), RatioType.token, Decimal('0.007'))
#     tx = await submitter.swap((orderA, orderB), 'ETH')
#     status = await tx.await_committed()


async def do_swap(account: LocalAccount):
    global_logger.info(account)

    ethereum_signer = EthereumSignerWeb3(account=account)
    global_logger.info(ethereum_signer)

    main_contract = conf.contract_address
    zksync = ZkSync(account=account, web3=w3, zksync_contract_address=main_contract)
    ethereum_provider = EthereumProvider(w3, zksync)

    signer = ZkSyncSigner.from_account(account, library, network.mainnet.chain_id)
    wallet = Wallet(ethereum_provider=ethereum_provider, zk_signer=signer,
                    eth_signer=ethereum_signer, provider=provider)
    global_logger.info(wallet)

    ordera = await wallet.get_order(
        'ETH',
        'USDT',
        Fraction(1, 1500),
        RatioType.token,
        Decimal('0.0003'))
    global_logger.info(ordera)

    # tx: Transaction = await wallet.mint_nft(ipfs_hash, t.address, "ETH")
    # global_logger.info(tx)
    # status: TransactionResult = await tx.await_committed()
    # global_logger.info(status)
    # global_logger.info(f'status: {status.status}')
    # if status.status == TransactionStatus.FAILED:
    #     global_logger.info(f'mint nft for {t.address}, try again after 1 second')


def main():
    global_logger.info(f'........start. {conf.env} ......')
    s: LocalAccount = Account.from_key(conf.source_key)
    global_logger.info(f'source: {s.address}')

    for i in range(1500, 1503):
        t = from_mnemonic(idx=i)
        asyncio.run(do_swap(t))
        break


if __name__ == '__main__':
    main()

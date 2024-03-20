import asyncio
import pdb

from eth_account import Account
from layer2.logger import global_logger
from eth_account.signers.local import LocalAccount
from layer2.zksync.zksync_lite_utils import ZKSyncLiteUtils


async def main():
    i = 380

    account: LocalAccount = Account.from_key('...')
    # await ZKSyncLiteUtils.tranfer_nft_to_self(account=account)
    await ZKSyncLiteUtils.mint_nft(account=account)

    pdb.set_trace()

    layer_account = await ZKSyncLiteUtils.get_account(idx=i)
    await ZKSyncLiteUtils.tranfer_nft_to_self(idx=i)
    # pdb.set_trace()
    await ZKSyncLiteUtils.transfer_to_self(idx=i, value_in_eth=0)
    await ZKSyncLiteUtils.mint_nft(idx=i)
    nonce = ZKSyncLiteUtils.get_nonce(idx=100)
    global_logger.info(f'nonce: {nonce}')


if __name__ == '__main__':
    asyncio.run(main())

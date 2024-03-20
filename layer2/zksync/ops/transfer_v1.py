import asyncio
import random
from layer2.zksync.zksync_lite_utils import ZKSyncLiteUtils


# todo: to check if the amount if valid.
def random_amount() -> float:
    n = random.randint(1000, 2000)
    return n / 10000000


async def main():
    await ZKSyncLiteUtils.transfer(idx=219, target_idx=218, value_in_eth='0.007')
    # for i in range(46, 50):
    #
    #     if i % 3 == 0:
    #         await ZKSyncLiteUtils.transfer(idx=i, target_idx=i + 1, value_in_eth=random_amount())
    #     elif i % 3 == 1:
    #         await ZKSyncLiteUtils.transfer(idx=i, target_idx=i - 1, value_in_eth=random_amount())
    #     else:
    #         await ZKSyncLiteUtils.transfer_to_self(idx=i, value_in_eth=0)


if __name__ == '__main__':
    asyncio.run(main())

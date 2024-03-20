# import asyncio
# import time
#
# from layer2.zksync.zksync_lite_utils import ZKSyncLiteUtils
#
#
# async def main():
#     for i in range(834, 841):
#         success: bool = await ZKSyncLiteUtils.activate(idx=i)
#         global_logger.info(f'activation {"success.." if success else "failed.."}')
#         time.sleep(10)
#
#
# if __name__ == '__main__':
#     asyncio.run(main())

import random

from layer2.lib.l1_utils import from_mnemonic
from layer2.consts import TokenAddress
from eth_account.signers.local import LocalAccount
from layer2.common import sleep_common_interaction_gap
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.zksync.era_project.mute import Mute
from layer2.zksync.era_project.syncswap import SyncSwap


w3 = ZksyncEraUtils.get_w3_cli()


def sell_usdc(account: LocalAccount):
    usdc_balance = ZksyncEraUtils.get_balance(account=account, token_address=TokenAddress.usdc.value)
    if usdc_balance > 5 * 10 ** 6:
        if random.randint(0, 1):
            approved, allowance = Mute.checking_token_approved(account, w3, TokenAddress.usdc.value)
            if not approved or allowance <= usdc_balance:
                success = Mute.approve_token(account, w3, TokenAddress.usdc.value)
                if not success:
                    return success

                sleep_common_interaction_gap()

            success = Mute.usdc_to_eth(account, w3, usdc_balance)
            if success:
                sleep_common_interaction_gap()
        else:
            approved, allowance = SyncSwap.checking_token_approved(account, w3, TokenAddress.usdc.value)
            if not approved or allowance <= usdc_balance:
                success = SyncSwap.approve_token(account, w3, TokenAddress.usdc.value)
                if not success:
                    return success

                sleep_common_interaction_gap()

            success = SyncSwap.usdc_to_eth(account, w3, usdc_balance)
            if success:
                sleep_common_interaction_gap()


def main():
    choices = []
    choices.extend(list(range(0, 841)))
    choices.extend(list(range(1500, 1503)))
    choices.append(2012)
    choices.append('473f28e4557f4a5eaaac93fd8dbd1d75c289a663e40fd830a3f9627a7c4b825a')

    for _ in range(5):
        random.shuffle(choices)

    while choices:
        idx = choices.pop()
        account = from_mnemonic(idx)

        try:
            sell_usdc(account)
        except Exception as e:
            global_logger.info(f'sell usdc of account#{account.address} failed with {e}')


if __name__ == '__main__':
    main()

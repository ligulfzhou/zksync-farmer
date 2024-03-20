import random
from typing import List
from web3 import Web3
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.erc20_utils import Erc20Utils
from layer2.common import sleep_common_interaction_gap


class ApproveToken:
    usdc_token: str = '0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4'  # usdc

    to_defi_address: List[str] = [
        # '0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d',  # spacefi
        # '0xd999E16e68476bC749A28FC14a0c3b6d7073F50c',  # velocore
        '0x9B5def958d0f3b6955cBEa4D5B7809b2fb26b059',  # syncswap
        '0x8B791913eB07C32779a16750e3868aA8495F5964',  # mute
    ]

    @classmethod
    def approve_token(cls, w3: Web3, account: LocalAccount) -> bool:
        success_cnt = 0
        usdc_token = cls.usdc_token

        to_defi_addresses = cls.to_defi_address
        random.shuffle(to_defi_addresses)

        for to_address in to_defi_addresses:
            approved, _ = Erc20Utils.checking_token_approved(w3, account, usdc_token, to_address)
            if not approved:
                count = random.randint(500, 2000) * 10 ** 6
                success = Erc20Utils.approve_token(w3, account, usdc_token, to_address, count)
                if success:
                    success_cnt += 1
                    if success_cnt < 2:
                        global_logger.info(f'before approving another token, lets take a break')
                        sleep_common_interaction_gap()
        return True


if __name__ == '__main__':
    from eth_account import Account

    account = Account.from_key('...')
    pass

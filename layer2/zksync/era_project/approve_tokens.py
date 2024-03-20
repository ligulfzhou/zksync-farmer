import random
from typing import List
from web3 import Web3
from eth_account.signers.local import LocalAccount

from layer2.logger import global_logger
from layer2.erc20_utils import Erc20Utils
from layer2.common import sleep_common_interaction_gap


class ApproveToken:
    common_tokens: List[str] = [
        # '0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4',  # usdc
        '0x2039bb4116b4efc145ec4f0e2ea75012d6c0f181',  # busd
        '0xd0ea21ba66b67be636de1ec4bd9696eb8c61e9aa',  # ot: onchain trading
        '0x8e86e46278518efc1c5ced245cba2c7e3ef11557',  # usd+
        '0x7400793aad94c8ca801aa036357d10f5fd0ce08f',  # cBNB: Celer Network BNB
        '0x28a487240e4d45cff4a2980d334cc933b7483842',  # cMATIC: Celer Network MATIC
        '0x47ef4a5641992a72cfd57b9406c9d9cefee8e0c4',  # zat token
        '0xd599da85f8fc4877e61f547dfacffe1238a7149e',  # cheems
        '0x6068ad384b4d330d4de77f47041885956c9f32a3',  # array
        '0xbbd1ba24d589c319c86519646817f2f153c9b716',  # DVF
    ]
    to_defi_address: List[str] = [
        '0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d',  # spacefi
        '0xd999E16e68476bC749A28FC14a0c3b6d7073F50c',  # velocore
        '0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295',  # syncswap
        '0x8B791913eB07C32779a16750e3868aA8495F5964',  # mute
    ]

    @classmethod
    def approve_token(cls, w3: Web3, account: LocalAccount) -> bool:
        success_cnt = 0
        token_addresses = cls.common_tokens
        random.shuffle(token_addresses)

        to_defi_addresses = cls.to_defi_address
        random.shuffle(to_defi_addresses)

        approve_counts = 2 if random.randint(0, 1) else 1

        for token_address in token_addresses:
            for to_address in to_defi_addresses:
                if success_cnt >= approve_counts:
                    return True

                approved, _ = Erc20Utils.checking_token_approved(w3, account, token_address, to_address)
                if not approved:
                    count = random.randint(500, 2000) * 10 ** 6
                    success = Erc20Utils.approve_token(w3, account, token_address, to_address, count)
                    if success:
                        success_cnt += 1
                        if success_cnt < 2:
                            global_logger.info(f'before approving another token, lets take a break')
                            sleep_common_interaction_gap()
        return False

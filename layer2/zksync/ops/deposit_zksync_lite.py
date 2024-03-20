import random
import time
from layer2.lib.l1_utils import L1Utils, get_gasprice, get_max_gas_price
from layer2.config.config import conf


def random_amount() -> int:
    r = random.randint(conf.deposits[0], conf.deposits[-1])
    l = len(str(r))
    return r - r % (10 ** (l - random.randint(2, 4)))


def main():
    gas_price = get_gasprice()
    for i in reversed(range(504, 823)):
        max_gasprice = get_max_gas_price()
        gas_price_ = max_gasprice if max_gasprice < gas_price else max_gasprice
        L1Utils.deposit_zksync_lite(idx=i, value=random_amount(), gas_price=gas_price_)
        time.sleep(random.randint(10, 90))


if __name__ == '__main__':
    main()

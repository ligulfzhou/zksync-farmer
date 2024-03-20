from layer2.logger import global_logger
from layer2.config.config import conf
from layer2.lib.l1_utils import from_mnemonic


def main():
    global_logger.info(f'for mnemonic code: {conf.mnemonic_code}')

    for idx in range(0, 1001):
        from_mnemonic(idx=idx)


if __name__ == '__main__':
    main()

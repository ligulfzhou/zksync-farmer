from layer2.lib.rs import rs
from layer2.lib.l1_utils import from_mnemonic


def main():
    indexes = []
    indexes.extend(list(range(421, 500)))
    for index in indexes:
        account = from_mnemonic(index)
        key = f'l0_{account.address}'
        if rs.exists(key):
            print(f'delete key: l0_{account.address}')
            rs.delete(key)


if __name__ == '__main__':
    main()

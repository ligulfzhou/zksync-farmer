import datetime
from layer2.lib.rs import rs
from layer2.lib.l1_utils import from_mnemonic


def main():
    indexes = [
        # 53, 56, 59, 66, 54, 90, 125, 131, 139, 60, 57, 433, 227, 770, 780, 634, 774, 640, 790, 753, 65, 50, 168, 219,
        # 181, 154, 495, 243, 75, 116, 306, 140, 115, 290, 492, 182, 443, 256, 478, 143, 72, 328, 241, 76, 150, 255, 368
        # 269, 119, 482, 195, 273, 160, 335, 409, 248, 376, 89, 93, 86, 81, 268, 107, 69, 96, 305, 157, 124, 454, 372
        # 453, 318, 272, 455, 52, 471, 675, 560, 685, 149, 336, 783, 191, 190, 207, 163, 745, 130, 134, 141, 80, 772,
        # 583, 412, 542, 246, 522, 734, 406, 396, 120, 117, 113, 120, 376, 213, 63, 649, 668, 189, 324, 384, 100, 614
        # 118, 695, 2, 432, 590, 186, 521, 525, 800, 331, 393, 518, 494, 658, 757, 558, 595, 350, 838, 760, 43, 729,
        # 653, 321, 587, 570, 532, 739, 320, 575, 802, 536, 374, 704, 553, 791, 198, 361, 267, 689
    ]
    for index in indexes:
        account = from_mnemonic(index)

        ts = int(datetime.datetime.now().timestamp())
        rs.set(f"{account.address}_last_transaction_timestamp", ts)


if __name__ == '__main__':
    main()

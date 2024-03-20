from layer2.lib.l1_utils import from_mnemonic
from layer2.l0.cron.go_through_l0 import execute
from layer2.l0.ops.arb_dfk_klaytn import execute_on_account as arb_dfk_hlaytn
from layer2.l0.ops.arb_celo_gnosis import execute_on_account as arb_celo_gnosis
from layer2.l0.ops.arb_celo_gnosis import bridge_ageur_from_gnosis_to_celo


def main():
    # execute(idx=70, force=True)
    # arb_dfk_hlaytn(idx=70, exec_count=1)
    arb_celo_gnosis(idx=416, exec_count=1)

    account = from_mnemonic(idx=416)
    bridge_ageur_from_gnosis_to_celo(account=account, exec_count=1)


if __name__ == '__main__':
    main()

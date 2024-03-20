import random
from typing import Optional

import web3.constants
from web3 import Web3
from web3.types import TxReceipt
from layer2.lib.l1_utils import from_mnemonic
from eth_abi.packed import encode_packed
from eth_account.signers.local import LocalAccount
from layer2.logger import global_logger
from layer2.erc20_utils import Erc20Utils
from layer2.assets.assets import get_abi
from layer2.l0.common import sleep_common_interaction_gap
from layer2.l0.ops.distribute_celo import withdraw_celo
from layer2.l0.ops.arb_refuel_to_gnosis import arb_refuel_to_gnosis

eth_address = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
usdc_e_address = '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'

erc_20_abi = get_abi('erc20.json')

arb_weth_contract = '0x82af49447d8a07e3bd95bd0d56f35241523fbab1'
arb_ageur_contract = '0xFA5Ed56A203466CbBC2430a43c66b9D8723528E7'
arb_angel_swap_contract = '0x1111111254eeb25477b68fb85ed929f73a960582'
arb_usdc_e_address = '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'
angel_bridger_contract = '0x16cd38b1B54E7abf307Cb2697E2D9321e843d5AA'

angel_swap_abi = get_abi('l0/angel_swap.json')
angel_bridger_abi = get_abi('l0/angel_bridger.json')

arb_rpc = 'https://arbitrum-mainnet.infura.io/v3/786649a580e3441f996da22488a8742a'
arb_w3 = Web3(Web3.HTTPProvider(arb_rpc))

celo_rpc = 'https://celo-mainnet.infura.io/v3/786649a580e3441f996da22488a8742a'
celo_w3 = Web3(Web3.HTTPProvider(celo_rpc))
celo_angel_bridger_contract = '0xf1ddcaca7d17f8030ab2eb54f2d9811365efe123'
celo_ageur_contract = '0xC16B81Af351BA9e64C1a069E3Ab18c244A1E3049'

gnosis_rpc = 'https://rpc.gnosischain.com/'
gnosis_w3 = Web3(Web3.HTTPProvider(gnosis_rpc))
gnosis_angel_bridger_contract = '0xfa5ed56a203466cbbc2430a43c66b9d8723528e7'
gnosis_ageur_contract = '0x4b1E2c2762667331Bc91648052F646d1b0d35984'

celo_or_genosis_minimum_balance = 0.02 * 10 ** 18
ageur_minimum_balance = 0.1 * 10 ** 18


def _have_ageur_on_celo(account: LocalAccount) -> (bool, int):
    ageur_token = celo_w3.eth.contract(address=Web3.to_checksum_address(celo_ageur_contract), abi=erc_20_abi)
    ageur_balance = ageur_token.functions.balanceOf(account.address).call()
    global_logger.info(f'{account.address} have {ageur_balance} ageur on celo, or {ageur_balance / 10 ** 18}')
    if ageur_balance and ageur_balance > 0.1 * 10 ** 18:
        return True, ageur_balance

    return False, ageur_balance


def _have_ageur_on_gnosis(account: LocalAccount) -> (bool, int):
    ageur_token = gnosis_w3.eth.contract(address=Web3.to_checksum_address(gnosis_ageur_contract), abi=erc_20_abi)
    ageur_balance = ageur_token.functions.balanceOf(account.address).call()
    global_logger.info(f'{account.address} have {ageur_balance} ageur on gnosis, or {ageur_balance / 10 ** 18}')
    if ageur_balance and ageur_balance > 0.1 * 10 ** 18:
        return True, ageur_balance

    return False, ageur_balance


def _have_ageur_on_arb(account: LocalAccount) -> (bool, int):
    ageur_token = arb_w3.eth.contract(address=Web3.to_checksum_address(arb_ageur_contract), abi=erc_20_abi)
    ageur_balance = ageur_token.functions.balanceOf(account.address).call()

    global_logger.info(f'{account.address} have {ageur_balance} ageur on arb, or {ageur_balance / 10 ** 18}')
    if ageur_balance and ageur_balance > 0.1 * 10 ** 18:
        return True, ageur_balance

    return False, ageur_balance


def trade_arb_for_ageur_from_angel(account: LocalAccount):
    '''
    FUNCTION TYPE: UniswapV3Swap (Uint256, Uint256, Uint256[])
    amount, minReturn, pools
    https://arbiscan.io/tx/0xa9730e570b998db2161a848fab3874ff454a87a602e7c3a22d4c2c6b42881516
    '''
    global_logger.info("=============trade_arb_for_ageur_from_angel============")
    random_amount = random.randint(730, 873) / 1000000
    random_amount_in_wei = int(random_amount * 10 ** 18)
    gas_price = arb_w3.eth.gas_price
    account_address = Web3.to_checksum_address(account.address)

    angel_swaper = arb_w3.eth.contract(address=Web3.to_checksum_address(arb_angel_swap_contract), abi=angel_swap_abi)
    tx = angel_swaper.functions.uniswapV3Swap(
        random_amount_in_wei,
        0,
        [
            28948022309329048855892746253492638602143065513233424506533206619652420808033,
            57896044618658097711785492505650464937654216909779526252521498549352264191271
        ]
    ).build_transaction({
        'from': account_address,
        'nonce': arb_w3.eth.get_transaction_count(account_address),
        'gasPrice': int(gas_price * 1.05),
        'value': random_amount_in_wei
    })
    gas_estimate = arb_w3.eth.estimate_gas(tx)
    gas_fee = gas_estimate * gas_price
    global_logger.info(f'estimate gas: {gas_fee}')

    signed_tx = arb_w3.eth.account.sign_transaction(tx, private_key=account.key)
    tx_hash = arb_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    r: TxReceipt = arb_w3.eth.wait_for_transaction_receipt(tx_hash)
    global_logger.info(f'transaction hash: {arb_w3.to_hex(tx_hash)} , status: {r.status}')
    sleep_common_interaction_gap()


def bridge_ageur_from_arb_to_celo(account: LocalAccount):
    # 1: approve
    '''
    0x095ea7b3
    00000000000000000000000016cd38b1b54e7abf307cb2697e2d9321e843d5aa
    0000000000000000000000000000000000000000000000001304f85fd45ed123
    '''
    global_logger.info("=============bridge_ageur_from_arb_to_celo============")

    account_address = Web3.to_checksum_address(account.address)
    ageur_token = arb_w3.eth.contract(address=Web3.to_checksum_address(arb_ageur_contract), abi=erc_20_abi)
    ageur_balance = ageur_token.functions.balanceOf(account_address).call()
    if ageur_balance:
        approved, count = Erc20Utils.checking_token_approved(arb_w3, account, arb_ageur_contract,
                                                             angel_bridger_contract, min_approve=0)
        if not approved or count < ageur_balance:
            Erc20Utils.approve_token(arb_w3, account, arb_ageur_contract, angel_bridger_contract, ageur_balance,
                                     limit_on_gas=False, multiply_gas=1.05)
            sleep_common_interaction_gap()

    # 2: bridge
    # FUNCTION TYPE: Send(Uint16, Bytes, Uint256, Address, Address, Bytes)
    '''
    Function: send(
        uint16 _dstChainId,
        bytes _toAddress,
        uint256 _amount,
        address _refundAddress,
        address _zroPaymentAddress,
        bytes _adapterParams
    )
    '''
    gas_price = arb_w3.eth.gas_price

    if ageur_balance:
        angel_bridger = arb_w3.eth.contract(address=Web3.to_checksum_address(angel_bridger_contract),
                                            abi=angel_bridger_abi)
        adapter_params = encode_packed(
            ['uint16', 'uint256'],
            [1, 200000]
        )
        to_address = encode_packed(
            ['address'],
            [account_address]
        )

        # 2.1 estimate fee
        estimate_fee = angel_bridger.functions.estimateSendFee(
            125,
            to_address,
            ageur_balance,
            False,
            adapter_params
        ).call()
        global_logger.info(f'estimatedFee: {estimate_fee}')

        tx = angel_bridger.functions.send(
            125,  # celo
            to_address,
            ageur_balance,
            account_address,
            web3.constants.ADDRESS_ZERO,
            adapter_params
        ).build_transaction({
            'from': account_address,
            'nonce': arb_w3.eth.get_transaction_count(account_address),
            'gasPrice': int(gas_price * 1.05),
            'value': estimate_fee[0],
        })

        gas_estimate = arb_w3.eth.estimate_gas(tx)
        gas_fee = gas_estimate * gas_price
        global_logger.info(f'estimate gas: {gas_fee}')

        signed_tx = arb_w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = arb_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = arb_w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'bridge ageur arb=> celo, transaction hash: {arb_w3.to_hex(tx_hash)} , status: {r.status}')

        sleep_common_interaction_gap()


def bridge_ageur_from_celo_to_gnosis(account: LocalAccount, exec_count: int = 2):
    # 1: approve
    '''
    0x095ea7b3
    000000000000000000000000f1ddcaca7d17f8030ab2eb54f2d9811365efe123
    00000000000000000000000000000000000000000000000011bcbdf93c210d1c
    '''
    global_logger.info(f"=============bridge_ageur_from_celo_to_gnosis={exec_count}===========")
    account_address = Web3.to_checksum_address(account.address)
    ageur_token = celo_w3.eth.contract(address=Web3.to_checksum_address(celo_ageur_contract), abi=erc_20_abi)
    ageur_balance = ageur_token.functions.balanceOf(account_address).call()
    if ageur_balance:
        approved, count = Erc20Utils.checking_token_approved(celo_w3, account, celo_ageur_contract,
                                                             celo_angel_bridger_contract, min_approve=0)
        if not approved or count < ageur_balance:
            Erc20Utils.approve_token(celo_w3, account, celo_ageur_contract, celo_angel_bridger_contract, ageur_balance,
                                     limit_on_gas=False, multiply_gas=1.05)
            sleep_common_interaction_gap()

    # 2: bridge
    # FUNCTION TYPE: Send(Uint16, Bytes, Uint256, Address, Address, Bytes)
    gas_price = celo_w3.eth.gas_price

    if ageur_balance:
        for _ in range(exec_count):
            # if ageur_balance <= ageur_minimum_balance:
            #     global_logger.info("😤 ageur exhausted. just return...")
            #     return

            angel_bridger = celo_w3.eth.contract(address=Web3.to_checksum_address(celo_angel_bridger_contract),
                                                 abi=angel_bridger_abi)
            adapter_params = encode_packed(
                ['uint16', 'uint256'],
                [1, 200000]
            )
            to_address = encode_packed(
                ['address'],
                [account_address]
            )

            random_ageur_value_to_bridge = random.randint(1000, 1200) / 10000
            random_ageur_value_to_bridge_in_wei = int(random_ageur_value_to_bridge * 10 ** 18)
            if random_ageur_value_to_bridge_in_wei > ageur_balance:
                random_ageur_value_to_bridge_in_wei = ageur_balance

            # 2.1 estimate fee
            estimate_fee = angel_bridger.functions.estimateSendFee(
                145,  # gnosis
                to_address,
                random_ageur_value_to_bridge_in_wei,
                False,
                adapter_params
            ).call()
            global_logger.info(f'estimatedFee: {estimate_fee}')

            tx = angel_bridger.functions.send(
                145,  # gnosis
                to_address,
                random_ageur_value_to_bridge_in_wei,
                account_address,
                web3.constants.ADDRESS_ZERO,
                adapter_params
            ).build_transaction({
                'from': account_address,
                'nonce': celo_w3.eth.get_transaction_count(account_address),
                'gasPrice': int(gas_price * (1 + random.randint(30, 80) / 1000)),
                'value': int(estimate_fee[0] * (1 + random.randint(100, 1200) / 100000)),
            })

            gas_estimate = celo_w3.eth.estimate_gas(tx)
            gas_fee = gas_estimate * gas_price
            global_logger.info(f'estimate gas: {gas_fee}')

            signed_tx = celo_w3.eth.account.sign_transaction(tx, private_key=account.key)
            tx_hash = celo_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            r: TxReceipt = celo_w3.eth.wait_for_transaction_receipt(tx_hash)
            global_logger.info(
                f'bridge ageur celo-> gnosis: transaction hash: {celo_w3.to_hex(tx_hash)} , status: {r.status}')

            ageur_balance -= random_ageur_value_to_bridge_in_wei
            sleep_common_interaction_gap()


def bridge_ageur_from_gnosis_to_celo(account: LocalAccount, exec_count: int = 2):
    # 1: approve
    '''
    0x095ea7b3
    000000000000000000000000f1ddcaca7d17f8030ab2eb54f2d9811365efe123
    00000000000000000000000000000000000000000000000011bcbdf93c210d1c
    '''
    global_logger.info(f"=============bridge_ageur_from_gnosis_to_celo={exec_count}===========")
    account_address = Web3.to_checksum_address(account.address)
    ageur_token = gnosis_w3.eth.contract(address=Web3.to_checksum_address(gnosis_ageur_contract), abi=erc_20_abi)
    ageur_balance = ageur_token.functions.balanceOf(account_address).call()
    if ageur_balance:
        approved, count = Erc20Utils.checking_token_approved(gnosis_w3, account, gnosis_ageur_contract,
                                                             gnosis_angel_bridger_contract, min_approve=0)
        if not approved or count < ageur_balance:
            Erc20Utils.approve_token(gnosis_w3, account, gnosis_ageur_contract, gnosis_angel_bridger_contract,
                                     ageur_balance, limit_on_gas=False, multiply_gas=1.05)
            sleep_common_interaction_gap()

    # 2: bridge
    # FUNCTION TYPE: Send(Uint16, Bytes, Uint256, Address, Address, Bytes)
    gas_price = gnosis_w3.eth.gas_price

    if ageur_balance:
        for _ in range(exec_count):
            angel_bridger = gnosis_w3.eth.contract(address=Web3.to_checksum_address(gnosis_angel_bridger_contract),
                                                   abi=angel_bridger_abi)
            adapter_params = encode_packed(
                ['uint16', 'uint256'],
                [1, 200000]
            )
            to_address = encode_packed(
                ['address'],
                [account_address]
            )

            random_ageur_value_to_bridge = random.randint(1000, 1200) / 10000
            random_ageur_value_to_bridge_in_wei = int(random_ageur_value_to_bridge * 10 ** 18)
            if random_ageur_value_to_bridge_in_wei > ageur_balance:
                random_ageur_value_to_bridge_in_wei = ageur_balance

            # 2.1 estimate fee
            estimate_fee = angel_bridger.functions.estimateSendFee(
                125,  # celo
                to_address,
                random_ageur_value_to_bridge_in_wei,
                False,
                adapter_params
            ).call()
            global_logger.info(f'estimatedFee: {estimate_fee}')

            tx = angel_bridger.functions.send(
                125,  # celo
                to_address,
                random_ageur_value_to_bridge_in_wei,
                account_address,
                web3.constants.ADDRESS_ZERO,
                adapter_params
            ).build_transaction({
                'from': account_address,
                'nonce': gnosis_w3.eth.get_transaction_count(account_address),
                'gasPrice': int(gas_price * (1 + random.randint(30, 80) / 1000)),
                'value': int(estimate_fee[0] * (1 + random.randint(100, 1200) / 100000)),
            })

            gas_estimate = gnosis_w3.eth.estimate_gas(tx)
            gas_fee = gas_estimate * gas_price
            global_logger.info(f'estimate gas: {gas_fee}')

            signed_tx = gnosis_w3.eth.account.sign_transaction(tx, private_key=account.key)
            tx_hash = gnosis_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            r: TxReceipt = gnosis_w3.eth.wait_for_transaction_receipt(tx_hash)
            global_logger.info(
                f'bridge ageur gnosis-> celo: transaction hash: {gnosis_w3.to_hex(tx_hash)} , status: {r.status}')

            ageur_balance -= random_ageur_value_to_bridge_in_wei
            sleep_common_interaction_gap()


def bridge_ageur_between_celo_and_gnosis(account: LocalAccount, exec_count: int = 2) -> bool:
    # 1: 先判断celo余额和celo链上的ageur余额
    global_logger.info(f'===================bridge_ageur_between_celo_and_gnosis={exec_count}==================')
    account_address = Web3.to_checksum_address(account.address)

    celo_balance = celo_w3.eth.get_balance(account_address)
    celo_ageur_token = celo_w3.eth.contract(address=Web3.to_checksum_address(celo_ageur_contract), abi=erc_20_abi)
    celo_ageur_balance = celo_ageur_token.functions.balanceOf(account_address).call()
    global_logger.info(
        f'{account.address} have {celo_ageur_balance / 10 ** 18} ageur on celo, and {celo_balance / 10 ** 18}eth')

    gnosis_balance = gnosis_w3.eth.get_balance(account_address)
    gnosis_ageur_token = gnosis_w3.eth.contract(address=Web3.to_checksum_address(gnosis_ageur_contract), abi=erc_20_abi)
    gnosis_ageur_balance = gnosis_ageur_token.functions.balanceOf(account_address).call()
    global_logger.info(
        f'{account.address} have {gnosis_ageur_balance / 10 ** 18} ageur on gnosis, or {gnosis_balance / 10 ** 18}eth')

    refuel_or_withdrawed = False
    if random.randint(0, 1):
        if gnosis_balance < celo_or_genosis_minimum_balance:
            global_logger.info('😤========refuel gnosis========')
            arb_refuel_to_gnosis(account)
            refuel_or_withdrawed = True

        if celo_balance < celo_or_genosis_minimum_balance:
            global_logger.info('😤========withdraw celo========')
            withdraw_celo(account)
            refuel_or_withdrawed = True
    else:
        if celo_balance < celo_or_genosis_minimum_balance:
            global_logger.info('😤========withdraw celo========')
            withdraw_celo(account)
            refuel_or_withdrawed = True

        if gnosis_balance < celo_or_genosis_minimum_balance:
            global_logger.info('😤========refuel gnosis========')
            arb_refuel_to_gnosis(account)
            refuel_or_withdrawed = True

    if refuel_or_withdrawed:
        return False

    count, t_round = 0, 0
    while True:
        t_round += 1
        if t_round > exec_count * 3:
            break

        if random.randint(0, 1) and gnosis_ageur_balance > ageur_minimum_balance \
                and gnosis_balance > celo_or_genosis_minimum_balance:
            bridge_ageur_from_gnosis_to_celo(account, 1)
            count += 1
        if count >= exec_count:
            break

        if random.randint(0, 1) and celo_ageur_balance > ageur_minimum_balance \
                and celo_balance > celo_or_genosis_minimum_balance:
            bridge_ageur_from_celo_to_gnosis(account, 1)
            count += 1
        if count >= exec_count:
            break
    return True


def execute_on_account(idx: int = 0, account: Optional[LocalAccount] = None, exec_count: int = 2) -> bool:
    if not account:
        account = from_mnemonic(idx)

    try:
        have_ageur_on_celo, _ = _have_ageur_on_celo(account)
        have_ageur_on_gnosis, _ = _have_ageur_on_gnosis(account)
        # 如果已经有ageur了，就不需要处理 arb相关的事了
        if not have_ageur_on_celo and not have_ageur_on_gnosis:
            have_ageur_on_arb, _ = _have_ageur_on_arb(account)
            if not have_ageur_on_arb:
                trade_arb_for_ageur_from_angel(account)

            bridge_ageur_from_arb_to_celo(account)
            return False

        # 然后直接是在celo和gnosis之间相互转
        return bridge_ageur_between_celo_and_gnosis(account, exec_count=exec_count)
    except Exception as e:
        global_logger.error(f'failed with {e}')
        return False


if __name__ == '__main__':
    for i in (65,):
        # account = Account.from_key('...')
        # bridge_ageur_from_gnosis_to_celo(account)
        execute_on_account(i)

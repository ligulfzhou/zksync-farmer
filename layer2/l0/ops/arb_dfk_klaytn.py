import random, time
from typing import Optional
from web3 import Web3
from web3.types import TxReceipt
from layer2.lib.l1_utils import from_mnemonic
from eth_account.signers.local import LocalAccount
from layer2.logger import global_logger
from layer2.erc20_utils import Erc20Utils
from layer2.assets.assets import get_abi
from layer2.l0.common import sleep_common_interaction_gap

eth_address = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
usdc_e_address = '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'
synapse_address = '0x37f9ae2e0ea6742b9cad5abcfb6bbc3475b3862b'
rpc = 'https://arbitrum-mainnet.infura.io/v3/786649a580e3441f996da22488a8742a'
router = '0x6947A425453D04305520E612F0Cb2952E4D07d62'

erc_20_abi = get_abi('erc20.json')
arbswap_abi = get_abi('l0/arbswap.json')
synapse_abi = get_abi('l0/synapse.json')
bridge_abi = get_abi('l0/bridge_gold.json')

w3 = Web3(Web3.HTTPProvider(rpc))

# dfk_rpc = 'https://subnets.avax.network/defi-kingdoms/dfk-chain/rpc'
# dfk_rpc = 'https://avax-dfk.gateway.pokt.network/v1/lb/6244818c00b9f0003ad1b619/ext/bc/q2aTwKuyzgs8pynF7UXBZCU7DejbZbZ6EUyHr3JQzYgwNPUPi/rpc'
# dfk_rpc = 'https://dfkchain.api.onfinality.io/public'
# dfk_rpc = 'https://avax-pokt.nodies.app/ext/bc/q2aTwKuyzgs8pynF7UXBZCU7DejbZbZ6EUyHr3JQzYgwNPUPi/rpc'
dfk_rpc_list = [
    'https://subnets.avax.network/defi-kingdoms/dfk-chain/rpc',
    # 'https://avax-dfk.gateway.pokt.network/v1/lb/6244818c00b9f0003ad1b619/ext/bc/q2aTwKuyzgs8pynF7UXBZCU7DejbZbZ6EUyHr3JQzYgwNPUPi/rpc',
    'https://dfkchain.api.onfinality.io/public',
    'https://avax-pokt.nodies.app/ext/bc/q2aTwKuyzgs8pynF7UXBZCU7DejbZbZ6EUyHr3JQzYgwNPUPi/rpc'
]
# dfk_w3 = Web3(Web3.HTTPProvider(dfk_rpc))
dfk_defikingdom_contract = '0x3C351E1afdd1b1BC44e931E12D4E05D6125eaeCa'
dfk_defikingdom_gold_approver_contract = '501cdc4ef10b63219704bf6adb785dfccb06dee2'
dfk_abi = get_abi('l0/dfk_swap.json')
dfk_usdc_contract = '0x3AD9DFE640E1A9Cc1D9B0948620820D975c3803a'
dfk_gold_contract = '0x576C260513204392F0eC0bc865450872025CB1cA'
dfk_bridge_contract = '0x501CdC4ef10b63219704Bf6aDb785dfccb06deE2'
dfk_weth_contract = '0xCCb93dABD71c8Dad03Fc4CE5559dC3D89F67a260'


def do_bridge_on_dfk(account: LocalAccount, dfk_w3: Web3, exec_count: int = 2):
    global_logger.info("==========do_bridge_on_dfk===========")

    account_address = Web3.to_checksum_address(account.address)
    jewel_balance = dfk_w3.eth.get_balance(account_address)

    gold_token = dfk_w3.eth.contract(address=Web3.to_checksum_address(dfk_gold_contract), abi=erc_20_abi)
    gold_balance = gold_token.functions.balanceOf(account_address).call()  # returns int with balance, without decimals
    global_logger.info(f'gold_balance: {gold_balance}')

    gas_price = dfk_w3.eth.gas_price

    if jewel_balance < 1*10**18:
        # 1: approve usdc
        # 0x095ea7b3
        # 0000000000000000000000003c351e1afdd1b1bc44e931e12d4e05d6125eaeca
        # 0000000000000000000000000000000000000000000000000ac0f556592cba17
        usdc_token = dfk_w3.eth.contract(address=Web3.to_checksum_address(dfk_usdc_contract), abi=erc_20_abi)
        usdc_balance = usdc_token.functions.balanceOf(account.address).call()  # returns int with balance, without decimals
        if usdc_balance:
            approved, count = Erc20Utils.checking_token_approved(dfk_w3, account, dfk_usdc_contract,
                                                                 dfk_defikingdom_contract, 0)
            if not approved:
                Erc20Utils.approve_token(dfk_w3, account, dfk_usdc_contract, dfk_defikingdom_contract, usdc_balance,
                                         limit_on_gas=False, multiply_gas=1.05)
                sleep_common_interaction_gap()

        # 2: swap usdc => jewel
        # FUNCTION TYPE: SwapExactTokensForETH (Uint256, Uint256, Address[], Address, Uint256)
        if usdc_balance and not gold_balance:
            global_logger.info("buy gold with usdc...")
            path = (
                Web3.to_checksum_address(dfk_usdc_contract),
                Web3.to_checksum_address(dfk_weth_contract)
            )

            swap_contract = dfk_w3.eth.contract(address=Web3.to_checksum_address(dfk_defikingdom_contract), abi=dfk_abi)
            tx = swap_contract.functions.swapExactTokensForETH(
                usdc_balance,
                0,
                path,
                account_address,
                dfk_w3.to_wei(int(time.time()) + 1800, 'wei'),
            ).build_transaction({
                'from': account_address,
                'nonce': dfk_w3.eth.get_transaction_count(account_address),
                'gasPrice': int(gas_price * 1.05),
            })

            signed_tx = dfk_w3.eth.account.sign_transaction(tx, private_key=account.key)
            tx_hash = dfk_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            r: TxReceipt = dfk_w3.eth.wait_for_transaction_receipt(tx_hash)
            global_logger.info(f'usdc=> jewel: transaction hash: {w3.to_hex(tx_hash)} , {r.status}')
            sleep_common_interaction_gap()

    # 3: swap jewel=> gold
    # FUNCTION TYPE: SwapETHForExactTokens (Uint256, Address[], Address, Uint256)
    if not gold_balance:
        '''
        0xfb3bdb41
        000000000000000000000000000000000000000000000000000000000000c350
        0000000000000000000000000000000000000000000000000000000000000080
        0000000000000000000000005c86e7409c18d96ea343203cf0fc86a0146f922c
        00000000000000000000000000000000000000000000000000000188fd87f9fb
        0000000000000000000000000000000000000000000000000000000000000002
        000000000000000000000000ccb93dabd71c8dad03fc4ce5559dc3d89f67a260
        000000000000000000000000576c260513204392f0ec0bc865450872025cb1ca
        '''
        path = (
            Web3.to_checksum_address(dfk_weth_contract),
            Web3.to_checksum_address(dfk_gold_contract)
        )
        swap_contract = dfk_w3.eth.contract(address=Web3.to_checksum_address(dfk_defikingdom_contract), abi=dfk_abi)

        random_amount = int(random.randint(50, 76) * 1000)
        random_value = int((random_amount * random.randint(277, 300)) * 10 ** 18 * 0.000001 / 1000)
        tx = swap_contract.functions.swapETHForExactTokens(
            random_amount,
            path,
            account_address,
            dfk_w3.to_wei(int(time.time()) + 1800, 'wei'),
        ).build_transaction({
            'value': random_value,
            'from': account_address,
            'nonce': dfk_w3.eth.get_transaction_count(account_address),
            'gasPrice': int(gas_price * 1.05),
        })

        signed_tx = dfk_w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = dfk_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = dfk_w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'jewel=> gold transaction hash: {w3.to_hex(tx_hash)} , {r.status}')
        sleep_common_interaction_gap()

    # 4: approve gold:
    # 0x095ea7b3
    # 000000000000000000000000501cdc4ef10b63219704bf6adb785dfccb06dee2000000000000000000000000000000000000000000000000000000000000f618
    # 0x095ea7b3000000000000000000000000501cdc4ef10b63219704bf6adb785dfccb06dee2000000000000000000000000000000000000000000000000000000000000e290
    '''
    0x095ea7b3
    000000000000000000000000501cdc4ef10b63219704bf6adb785dfccb06dee2
    000000000000000000000000000000000000000000000000000000000000d354
    '''
    gold_token = dfk_w3.eth.contract(address=Web3.to_checksum_address(dfk_gold_contract), abi=erc_20_abi)
    gold_balance = gold_token.functions.balanceOf(account.address).call()  # returns int with balance, without decimals
    global_logger.info(f'gold_balance: {gold_balance} or {gold_balance//1000}')
    if gold_balance:
        approved, count = Erc20Utils.checking_token_approved(dfk_w3, account, dfk_gold_contract,
                                                             dfk_defikingdom_gold_approver_contract, 0)
        if not approved:
            Erc20Utils.approve_token(dfk_w3, account, dfk_gold_contract, dfk_defikingdom_gold_approver_contract,
                                     gold_balance, limit_on_gas=False, multiply_gas=1.05)
            sleep_common_interaction_gap()

    # 5: bridge gold from celo=> klaytn via layerzero.
    # Function type: SendERC20 (uint16, address, address, uint256)
    if gold_balance:
        for _ in range(exec_count):
            bridge_contract = dfk_w3.eth.contract(address=Web3.to_checksum_address(dfk_bridge_contract), abi=bridge_abi)

            random_amount = random.choice([1, 1, 1, 1, 1, 1, 1, 2, 2, 3])
            random_value = int(random.randint(25396378, 28782329) / 100000000 * 10 ** 18)
            if random_amount * 1000 > gold_balance:
                random_amount = gold_balance // 1000

            global_logger.info(f'random_value: {random_value}')
            tx = bridge_contract.functions.sendERC20(
                150,
                account_address,
                Web3.to_checksum_address(dfk_gold_contract),
                int(random_amount * 1000),
            ).build_transaction({
                'value': int(random_value * 2),
                'from': account_address,
                'nonce': dfk_w3.eth.get_transaction_count(account_address),
                'gasPrice': int(gas_price * 1.05),
            })

            signed_tx = dfk_w3.eth.account.sign_transaction(tx, private_key=account.key)
            tx_hash = dfk_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            r: TxReceipt = dfk_w3.eth.wait_for_transaction_receipt(tx_hash)
            global_logger.info(f'bridge gold transaction hash: {w3.to_hex(tx_hash)} , {r.status}')
            time.sleep(random.randint(10, 100))

            gold_balance -= int(random_amount*1000)


def bridge_usdc_to_dfk_via_synapse(account: LocalAccount):
    global_logger.info("===============swap usdc_e from arbitrum to dfk via synapse===============")
    token = w3.eth.contract(address=Web3.to_checksum_address(usdc_e_address), abi=erc_20_abi)
    balance = token.functions.balanceOf(account.address).call()  # returns int with balance, without decimals
    global_logger.info(f'usdc_e token on arbitrum: {balance}')
    if balance:
        approved, count = Erc20Utils.checking_token_approved(w3, account, usdc_e_address, synapse_address,
                                                             min_approve=1)
        if not approved or count < balance:
            Erc20Utils.approve_token(w3, account, usdc_e_address, synapse_address, balance, limit_on_gas=False,
                                     multiply_gas=1.05)

    if balance:
        account_address = Web3.to_checksum_address(account.address)
        contract = w3.eth.contract(address=Web3.to_checksum_address(synapse_address), abi=synapse_abi)
        gas_price = w3.eth.gas_price
        tx_hash = contract.functions.swapAndRedeem(
            account_address,
            53935,
            Web3.to_checksum_address('0x2913e812cf0dcca30fb28e6cac3d2dcff4497688'),
            1,
            0,
            balance,
            0,
            w3.to_wei(int(time.time()) + 1800, 'wei')
        ).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': int(gas_price * (1 + random.randint(30, 80) / 1000)),
            # 'gasPrice': int(gas_price * 1.08),
        })

        signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} , transaction status: {r.status}')


def _have_usdc_on_dfk(account: LocalAccount, dfk_w3: Web3) -> bool:
    usdc_token = dfk_w3.eth.contract(address=Web3.to_checksum_address(dfk_usdc_contract), abi=erc_20_abi)
    usdc_balance = usdc_token.functions.balanceOf(Web3.to_checksum_address(account.address)).call()
    global_logger.info(f'usdc balance on dfk is {usdc_balance}, or {usdc_balance/10**18}')
    if usdc_balance:
        return True
    return False


def _have_jewel_on_dfk(account: LocalAccount, dfk_w3: Web3) -> bool:
    jewel_balance = dfk_w3.eth.get_balance(account.address)
    # 至少有一个jewel
    global_logger.info(f'jewel balance on dfk is {jewel_balance}, {jewel_balance/10**18}')
    if jewel_balance and jewel_balance > 1 * 10**18:
        return True

    return False


def _have_gold_on_dfk(account: LocalAccount, dfk_w3: Web3) -> bool:
    gold_token = dfk_w3.eth.contract(address=Web3.to_checksum_address(dfk_gold_contract), abi=erc_20_abi)
    gold_balance = gold_token.functions.balanceOf(Web3.to_checksum_address(account.address)).call()
    # 至少有一个gold
    global_logger.info(f'gold balance on dfk is {gold_balance}, {gold_balance//1000}')
    if gold_balance and gold_balance > 1 * 1000:
        return True

    return False


def _have_usdc_on_arb(account: LocalAccount) -> bool:
    account_address = Web3.to_checksum_address(account.address)
    token = w3.eth.contract(address=Web3.to_checksum_address(usdc_e_address), abi=erc_20_abi)
    balance = token.functions.balanceOf(account_address).call()
    if balance:
        return True
    return False


def swap_usdc_e_with_eth_on_arbitrum(account: LocalAccount):
    global_logger.info("===============swap eth=> usdc_e on arbitrum===============")
    account_address = Web3.to_checksum_address(account.address)
    contract = w3.eth.contract(address=Web3.to_checksum_address(router), abi=arbswap_abi)
    value = int((random.randint(60, 90) / 100000) * 10 ** 18)
    gas_price = w3.eth.gas_price
    tx_hash = contract.functions.swap(
        Web3.to_checksum_address(eth_address),
        Web3.to_checksum_address(usdc_e_address),
        value,
        0,
        1
    ).build_transaction({
        'from': account_address,
        'nonce': w3.eth.get_transaction_count(account_address),
        'gasPrice': int(gas_price * 1.05),
        'value': value,
    })
    gas_estimate = w3.eth.estimate_gas(tx_hash)
    gas_fee = gas_estimate * gas_price
    global_logger.info(f'estimate gas: {gas_fee}')

    signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} , transaction status: {r.status}')


def execute_on_account(idx: int = 0, account: Optional[LocalAccount] = None, exec_count: int = 2) -> bool:
    dfk_rpc = random.choice(dfk_rpc_list)
    global_logger.info(f'random picked dfk rpc: {dfk_rpc}')
    dfk_w3 = Web3(Web3.HTTPProvider(dfk_rpc))

    if not account:
        account = from_mnemonic(idx)

    try:
        have_gold_on_dfk = _have_gold_on_dfk(account, dfk_w3)
        have_usdc_on_dfk = _have_usdc_on_dfk(account, dfk_w3)
        have_jewel_on_dfk = _have_jewel_on_dfk(account, dfk_w3)

        if not have_gold_on_dfk and not have_usdc_on_dfk and not have_jewel_on_dfk:
            have_usdc_on_arb = _have_usdc_on_arb(account)
            if not have_usdc_on_arb:
                swap_usdc_e_with_eth_on_arbitrum(account)
                time.sleep(random.randint(10, 30))

            bridge_usdc_to_dfk_via_synapse(account)
            time.sleep(random.randint(30, 100))
            return False

        do_bridge_on_dfk(account, dfk_w3, exec_count=exec_count)
        time.sleep(random.randint(1, 10))
        return True
    except Exception as e:
        global_logger.error(f'failed with {e}')
        return False


if __name__ == '__main__':
    # for i in (97, ):
    for i in (271,):
        execute_on_account(i, exec_count=50)

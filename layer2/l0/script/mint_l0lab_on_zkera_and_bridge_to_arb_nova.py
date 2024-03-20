import random, time
from web3 import Web3
from web3.types import TxReceipt
from layer2.lib.l1_utils import from_mnemonic
from eth_account.signers.local import LocalAccount
from layer2.logger import global_logger
from layer2.assets.assets import get_abi
from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from layer2.lib.rs import get_nft_id, add_nft_id_for_address, remove_nft_id_for_address

w3 = ZksyncEraUtils.get_w3_cli()

abi = get_abi("l0lab.json")
contract_addr = '0xA0d89276f66aAAaAfa2B0bb3b3CE11a4D95b76d2'

arb_nova_chain_id = 175

def bridge_nft(account: LocalAccount, nft_id: int, target_chain_id: int):
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=abi)
    try:
        estimate_fee = contract.functions.estimateFees(target_chain_id, nft_id).call()
        global_logger.info(estimate_fee)
        estimate_fee = int(estimate_fee*1.05)
    except Exception as e:
        estimate_fee = 0.00015 * 10**18
        global_logger.error(e)

    gas_price = w3.eth.gas_price
    global_logger.info(f'gas_price: {gas_price}, target_chain_id: {target_chain_id}, nft_id: {nft_id}')
    tx_hash = contract.functions.crossChain(target_chain_id, nft_id).build_transaction({
        'from': Web3.to_checksum_address(account.address),
        'nonce': w3.eth.get_transaction_count(account.address),
        'gasPrice': gas_price,
        'value': estimate_fee
    })

    gas_estimate = w3.eth.estimate_gas(tx_hash)
    gas_fee = gas_estimate * gas_price
    global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

    signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
    remove_nft_id_for_address(account.address)


def mint(account: LocalAccount) -> int:
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=abi)
    nft_id = get_nft_id(address=account.address)
    if nft_id:
        try:
            xyz = contract.functions.tokenURI(nft_id).call()
            global_logger.info(f'tokenURI: {xyz}')
            return nft_id
        except Exception as e:
            global_logger.error(e)
            remove_nft_id_for_address(address=account.address)

    tx_hash = contract.functions.mint().build_transaction({
        'from': Web3.to_checksum_address(account.address),
        'nonce': w3.eth.get_transaction_count(account.address),
        'gasPrice': w3.eth.gas_price,
        'value': 300000000000000
    })

    gas_estimate = w3.eth.estimate_gas(tx_hash)
    gas_price = w3.eth.gas_price
    gas_fee = gas_estimate * gas_price
    global_logger.info(f'Estimated gas fee: {w3.from_wei(gas_fee, "ether")} ETH')

    signed_tx = w3.eth.account.sign_transaction(tx_hash, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    while True:
        r: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        global_logger.info(f'transaction hash: {w3.to_hex(tx_hash)} \ntransaction status: {r.status}')
        tx_receipt = r.__dict__
        logs = tx_receipt.get('logs', [])
        if not logs:
            global_logger.info(f'transaction not finalized, still wait for it...')
            time.sleep(1)
            continue

        log = logs[2]
        topics = log.__dict__['topics']
        if len(topics) <= 3:
            global_logger.info('likely won"t happen..')
            continue

        nft_id = int(topics[3].hex(), 16)
        add_nft_id_for_address(account.address, nft_id)
        return nft_id


if __name__ == '__main__':
    choices = []
    choices.extend(list(range(48, 841)))
    choices.extend(list(range(1500, 1503)))
    choices.append(2012)

    for _ in range(5):
        random.shuffle(choices)

    while len(choices):
        i = choices.pop()
        if i in (241, 392, 740, 335) or 500 <= i <= 599:
            continue

        account: LocalAccount = from_mnemonic(i)
        if i > 500:
            balance = ZksyncEraUtils.get_balance(account)
            if balance < 0.01 * 10 ** 18:
                global_logger.info(f'idx#{i} does not have enough balance: {balance / (10 ** 18)}')
                continue

        try:
            nft_id = mint(account)
            global_logger.info(f'idx#{i}, address#{account.address}, get nft#{nft_id}')
            time.sleep(random.randint(10, 60))
            bridge_nft(account, nft_id, arb_nova_chain_id)
        except Exception as e:
            global_logger.info(f'idx#{i} failed with {e}')

        global_logger.info(choices)
        time.sleep(random.randint(60, 5 * 60))

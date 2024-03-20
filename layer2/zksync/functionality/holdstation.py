import pdb
import random

from web3.types import HexStr

from layer2.zksync.zksync_era_utils import ZksyncEraUtils
from eth_account import Account
from eth_account.signers.local import LocalAccount


# 0xa7e1e47b000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002a638e78a7677a8c2205c667de13968228fa70d0000000000000000000000000000000000000000000000000000000000000000

# 0xa7e1e47b
# 0000000000000000000000000000000000000000000000000000000000000000
# 00000000000000000000000073a83cfdf89e465170a4351ace39e9d581d415da
# 0000000000000000000000000000000000000000000000000000000000000000

# 0xa7e1e47b
# 0000000000000000000000000000000000000000000000000000000000000000
# 000000000000000000000000ad05982DeD012900eFE5bB489ab0e8820D5bB69B
# 0000000000000000000000000000000000000000000000000000000000000000

# 0xa7e1e47b
# 0000000000000000000000000000000000000000000000000000000000000000
# 0000000000000000000000006500e1b36d53982edd4b4d11af6597de71170e09
# 0000000000000000000000000000000000000000000000000000000000000000
# 0xa7e1e47b
# 0000000000000000000000000000000000000000000000000000000000000000
# 000000000000000000000000ad05982ded012900efe5bb489ab0e8820d5bb69b
# 0000000000000000000000000000000000000000000000000000000000000000

def deploy_holdstation_aa_wallet(account: LocalAccount):
    web3 = ZksyncEraUtils.get_w3_cli()

    address = web3.to_checksum_address(account.address)
    # Contract address
    contract_address = web3.to_checksum_address('0xE17043160bE1A13bd15B1Eb105f47A8968DE0c27')

    print(web3.to_checksum_address(account.address))
    # Function signature (this is what you'd need to determine)
    function_signature = f'0xa7e1e47b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000{account.address[2:].lower()}0000000000000000000000000000000000000000000000000000000000000000'
    # function_signature = HexStr(f'0xa7e1e47b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000{account.address[2:].lower()}0000000000000000000000000000000000000000000000000000000000000000')
    # function_signature = web3.to_bytes(hexstr=HexStr(f'0xa7e1e47b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000{account.address[2:].lower()}0000000000000000000000000000000000000000000000000000000000000000'))
    print(function_signature)

    gas_price = web3.eth.gas_price
    gas = random.randint(500_0000, 600_0000)

    # Raw transaction data
    raw_transaction = {
        'to': contract_address,
        'data': function_signature,
        'gas': gas,
        'gasPrice': gas_price,
        'from': address,
        'nonce': web3.eth.get_transaction_count(web3.to_checksum_address(account.address))
    }

    # Sign and send the transaction
    signed_txn = web3.eth.sign_transaction(raw_transaction, account.key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    gas_estimate = web3.eth.estimate_gas(tx_hash)
    pdb.set_trace()

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    print("Transaction receipt:", tx_receipt)


if __name__ == '__main__':
    account = Account.from_key('...')
    deploy_holdstation_aa_wallet(account)

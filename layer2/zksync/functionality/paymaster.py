import pdb
import random
import datetime
from web3 import Web3
from eth_account import Account
from typing import Optional
from eth_account.signers.local import LocalAccount
from decimal import Decimal
from pathlib import Path
from unittest import TestCase, skip
from eth_typing import HexStr
from eth_utils import keccak, remove_0x_prefix
from web3 import Web3
from zksync2.manage_contracts.contract_encoder_base import (
    ContractEncoder,
    JsonConfiguration,
)
from zksync2.manage_contracts.deploy_addresses import ZkSyncAddresses
from zksync2.manage_contracts.paymaster_utils import PaymasterFlowEncoder
from zksync2.manage_contracts.precompute_contract_deployer import (
    PrecomputeContractDeployer,
)
from zksync2.manage_contracts.utils import nonce_holder_abi_default
from zksync2.module.module_builder import ZkSyncBuilder
from zksync2.core.types import Token, EthBlockParams, ZkBlockParams, PaymasterParams
from eth_account import Account
from eth_account.signers.local import LocalAccount
from zksync2.signer.eth_signer import PrivateKeyEthSigner
from zksync2.transaction.transaction_builders import (
    TxFunctionCall,
    TxCreate2Contract,
    TxCreateAccount,
)
from layer2.assets.assets import get_abi
from layer2.config.config import conf
from layer2.consts import TokenAddress


def deploy_paymaster(account: LocalAccount, token_address: str = TokenAddress.usdc.value):
    web3 = ZkSyncBuilder.build(conf.get_zksync_rpc())
    if not hasattr(web3, 'zksync'):
        return

    chain_id = web3.zksync.chain_id
    signer = PrivateKeyEthSigner(account, chain_id)
    # self.custom_paymaster = ContractEncoder.from_json(self.web3, contract_path("CustomPaymaster.json"))

    # directory = Path(__file__).parent
    # path = directory / Path("../contracts/Paymaster.json")
    abi = get_abi('paymaster.json')

    token_address = web3.to_checksum_address(token_address)
    constructor_arguments = {"_erc20": token_address}

    nonce = web3.zksync.get_transaction_count(
        account.address, EthBlockParams.PENDING.value
    )
    nonce_holder = web3.zksync.contract(
        address=ZkSyncAddresses.NONCE_HOLDER_ADDRESS.value,
        abi=nonce_holder_abi_default(),
    )
    deployment_nonce = nonce_holder.functions.getDeploymentNonce(
        account.address
    ).call({"from": account.address})
    deployer = PrecomputeContractDeployer(web3)
    precomputed_address = deployer.compute_l2_create_address(
        account.address, deployment_nonce
    )
    token_contract = ContractEncoder(web3, abi['abi'], abi['bytecode'])

    directory = Path(__file__).parent
    path = directory / Path("../contracts/Token.json")

    token_contract = ContractEncoder.from_json(
        web3, path.resolve(), JsonConfiguration.STANDARD
    )
    # token_contract = ContractEncoder.from_json(
    #     web3, path.resolve(), JsonConfiguration.STANDARD
    # )

    encoded_constructor = token_contract.encode_constructor(**constructor_arguments)
    gas_price = web3.zksync.gas_price
    create_account = TxCreateAccount(
        web3=web3,
        chain_id=chain_id,
        nonce=nonce,
        from_=account.address,
        gas_price=gas_price,
        bytecode=token_contract.bytecode,
        call_data=encoded_constructor,
    )
    estimate_gas = web3.zksync.eth_estimate_gas(create_account.tx)
    pdb.set_trace()
    tx_712 = create_account.tx712(estimate_gas)
    signed_message = signer.sign_typed_data(tx_712.to_eip712_struct())
    msg = tx_712.encode(signed_message)
    tx_hash = web3.zksync.send_raw_transaction(msg)
    tx_receipt = web3.zksync.wait_for_transaction_receipt(
        tx_hash, timeout=240, poll_latency=0.5
    )
    return tx_receipt["contractAddress"]


if __name__ == '__main__':
    account = Account.from_key('...')
    deploy_paymaster(account, TokenAddress.usdc.value)

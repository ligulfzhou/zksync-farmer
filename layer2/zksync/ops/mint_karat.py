"""
代码抄自：
https://ptb.discord.com/channels/1089245263425699971/1089245263929024534/1108533905042194493
"""
import random, time, requests
from web3 import Web3, HTTPProvider
from layer2.logger import global_logger
from layer2.lib.l1_utils import from_mnemonic
from eth_account.signers.local import LocalAccount

ZksRPC = 'https://mainnet.era.zksync.io'
web3 = Web3(HTTPProvider(ZksRPC))


def randomSleep(intervalMin, intervalMax):
    sTime = random.randint(intervalMin, intervalMax)
    global_logger.info('karat兔子--随机间隔--等待...', sTime)
    time.sleep(sTime)


def karat_process(walletAddress, private_key):
    global_logger.info(f'karat兔子 开始执行, walletAddress={walletAddress}')
    while True:
        try:
            karat_mint(Web3.to_checksum_address(walletAddress), private_key, random.randint(0, 150))
            return
        except Exception as ex:
            randomSleep(50, 100)
            global_logger.info(ex)


def karat_mint(walletAddress, private_key, validatorTokenId):
    url = 'https://api.karatdao.com/network/action'
    postData = {
        "method": "claimer/requestMintClaimerSignature",
        "params": {
            "walletAddress": walletAddress,
            "validatorTokenId": validatorTokenId,
            "lieutenantAddr": "0x0000000000000000000000000000000000000000"
        }
    }
    signResponse = requests.post(url, json=postData)
    role = signResponse.json().get('result').get('message').get('role')
    score = signResponse.json().get('result').get('message').get('score')
    sign = signResponse.json().get('result').get('signedMessage')
    global_logger.info(f'role={role},score={score},sign={sign},validatorTokenId={validatorTokenId}')
    validatorTokenIdHex = Web3.to_hex(validatorTokenId)[2:].zfill(64)
    requestData = f'0xd221bd26000000000000000000000000{walletAddress[2:]}{validatorTokenIdHex}{Web3.to_hex(score)[2:].zfill(64)}0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000{role}00000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000041{sign[2:]}00000000000000000000000000000000000000000000000000000000000000'
    tx_hash = {
        'from': walletAddress,
        'to': '0x112E5059a4742ad8b2baF9C453fDA8695c200454',
        'nonce': web3.eth.get_transaction_count(walletAddress),
        'gasPrice': web3.eth.gas_price,  # 设置gasPrice
        'value': 0,
        'gas': 4000000 + random.randint(100000, 200000),  # 设置gas限制
        "data": requestData,
        'chainId': 324
    }
    # 预估所需的gas
    gas_estimate = web3.eth.estimate_gas(tx_hash)
    # 获取预估gas价格
    gas_price = web3.eth.gas_price
    gas_fee = gas_estimate * gas_price
    eth_fee = web3.from_wei(gas_fee, 'ether')
    global_logger.info('预估 gas fee: {} ETH'.format(eth_fee))
    # 私钥导入 这里切记保护好自己的私钥 不要暴露
    signed_tx = web3.eth.account.sign_transaction(tx_hash, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    global_logger.info('交易已发送，交易哈希值：', web3.to_hex(tx_hash))


if __name__ == '__main__':
    # karat_process('0x2A0CFDe00155b19a7Cf625c1c68d905e55adcf7b', binascii.unhexlify('473f28e4557f4a5eaaac93fd8dbd1d75c289a663e40fd830a3f9627a7c4b825a'.encode()))
    choices = []
    choices.extend(list(range(1, 841)))
    choices.extend(list(range(1500, 1503)))
    choices.append(2012)

    for _ in range(5):
        random.shuffle(choices)

    while len(choices):
        i = choices.pop()

        account: LocalAccount = from_mnemonic(i)
        karat_process(account.address, account.key)

        global_logger.info(choices)
        randomSleep(5, 50)

# zkSync lite and era

0: 开发环境

web3==6.0.0
python-okx==0.1.9 (用于okx提币)

zksync lite:
https://github.com/zksync-sdk/zksync-python.git
只能从源码安装，最好是改一下源码，省的lite和era需要不同的虚拟环境
把源码里的waitForTransactionReceipt=> wait_for_transaction_receipt
        toChecksumAddress=> to_checksum_address
python3 setup.py install

并需要下载crypto library:
文档： https://docs.zksync.io/api/sdk/python/tutorial/
下载地址 https://github.com/zksync-sdk/zksync-crypto-c/releases

zksync era:
pip3 install zksync2


1: 创建eth账号
- 可以随机生成 私钥-地址 对

```python
import secrets
from eth_account import Account
from eth_account.signers.local import LocalAccount
def generate_random_account()-> LocalAccount:
  # or simply return Account.create(), 随机性可能不行
  return Account.from_key(f'0x{secrets.token_hex(32)}')
```


- 可以先生成 助记词，然后通过助记词生成 私钥-地址 对 
   (优点：可以只记录助记词就行了)

生成助记词
```python
# generate mnemonic code
from eth_account import Account
Account.enable_unaudited_hdwallet_features()

def gen_mnemonic_code() -> str:
    _, mnemonic = Account.create_with_mnemonic()
    return mnemonic

测试:
gen_mnemonic_code()
=> 'length pact reason inside limb soon main agree broken sentence inquiry narrow'
```

助记词 + 数字(N)，就回返回该助记词的第N对私钥+地址
```python
from web3 import Web3
from eth_account.signers.local import LocalAccount
from eth_account.hdaccount import ETHEREUM_DEFAULT_PATH

# infura可免费注册，后面也会用到
rpc_url = 'https://mainnet.infura.io/v3/<your-infura-key>'
w3 = Web3(Web3.HTTPProvider(rpc_url))
w3.eth.account.enable_unaudited_hdwallet_features()

def from_mnemonic(mnemonic: str, idx: int = 0) -> LocalAccount:
    account: LocalAccount = w3.eth.account.from_mnemonic(
        mnemonic,
        account_path=f'{ETHEREUM_DEFAULT_PATH}/{idx}'
    )
    return account

测试：
from_mnemonic('length pact reason inside limb soon main agree broken sentence inquiry narrow', 0)
from_mnemonic('length pact reason inside limb soon main agree broken sentence inquiry narrow', 1)
from_mnemonic('length pact reason inside limb soon main agree broken sentence inquiry narrow', 2)

可以从一个非常大的数字开始，这样子就算别人知道了助记词，它也不一定能找得到你的币
```


2: 从交易网站 将eth提到 zkSync Lite 和 zkSync Era 上

现在okx已经支持直接提到 这两条链了，所以不需要走 跨链了
（跨链： 如 把eth从 以太坊主网，发送到 zkSync Lite上来，或者从Optimism=> zkSync Era,等）
跨链过可能会多给点积分，然后多点空投，但跨链成本相对较高（4，5刀起步）,看个人抉择

官方的跨链桥, ethereum => zkSync lite (https://lite.zksync.io/transaction/deposit)
            ethereum => zkSync era (https://portal.zksync.io/bridge)

```text
    okx ------提币--------> ethereum ----------跨链-----------> zkSync lite
    |
    |
    |跨链
    |
    |
    V
    zkSync era
```

```text
  okx ------直接提币--------> zkSync lite 
   |
   | 
   |直接提币
   |
   |
   V
 zkSync era
```

```text
   okx ------直接提币--------> zkSync lite/era
                                  |
                                  |
                                  |通过orbiter/multichain等跨链
                                  |
                                  |
                                  V
                           zkSync era/lite
```



怎样都行，反正最省的肯定是直接提到zksync lite和era上

```python
# distribute eth from okx
from okx import Funding
api_key = "<YOUR-API-KEY>"
secret_key = "<YOUR-SECRET-KEY>"
passphrase = "<YOUR-PASSPHRASE>"
flag = '0'

fundingAPI = Funding.FundingAPI(api_key, secret_key, passphrase, False, flag)

# withdraw eth in ether
withdraw_amount = "1"

# 下面的 0.0002，0.0003, 0.001456可能会变，需要去okx查,或者调 fundingAPI.get_currencies() 获取

# withdraw to zkSync lite
res = fundingAPI.withdrawal("ETH", withdraw_amount, "4", address, "0.0002", "ETH-zkSync Era")

# withdraw to zkSync era
res = fundingAPI.withdrawal("ETH", withdraw_amount, "4", address, "0.0003", "ETH-zkSync Lite")

# withdraw to ethereum mainnet
res = fundingAPI.withdrawal("ETH", withdraw_amount, "4", address, "0.001456")
```


3: 做链上交互(得改代码)
```shell
env=lite PYTHONPATH=. /python layer2/zksync/cron/go_through_lite.py
```

```shell
env=era PYTHONPATH=. /python layer2/zksync/cron/go_through_era.py
```


# layerzero

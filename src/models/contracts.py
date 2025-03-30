from dataclasses import dataclass


@dataclass
class ERC20:
    abi: str = open('./assets/abi/erc20.json', 'r').read()


@dataclass
class WrapData:
    abi: str = open('./assets/abi/eth.json', 'r').read()


@dataclass
class RelayData:
    address: str = None
    abi: str = None


@dataclass
class BeanExchangeData:
    address: str = '0xCa810D095e90Daae6e867c19DF6D9A8C56db2c89'
    abi: str = open('./assets/abi/bean_swap.json', 'r').read()


@dataclass
class SHMonadData:
    address: str = '0x3a98250F98Dd388C211206983453837C8365BDc1'
    abi: str = None


@dataclass
class MonadTestnetLifeData:
    address: str = '0x00000000009a1E02f00E280dcfA4C81c55724212'
    abi: str = open('./assets/abi/mint_fun.json', 'r').read()


@dataclass
class ChogStarData:
    address: str = '0xb33D7138c53e516871977094B249C8f2ab89a4F4'
    abi: str = open('./assets/abi/nft.json', 'r').read()


class APRioData:
    address: str = '0xb2f82D0f38dc453D596Ad40A37799446Cc89274A'


@dataclass
class OrbiterData:
    address: str = '0xB5AADef97d81A77664fcc3f16Bfe328ad6CEc7ac'
    abi: str | None = None


@dataclass
class TestnetBridgeData:
    address: str = '0xfcA99F4B5186D4bfBDbd2C542dcA2ecA4906BA45'
    address_op: str = '0x8352C746839699B1fc631fddc0C3a00d4AC71A17'
    abi: str = open('./assets/abi/testnet_bridge.json', 'r').read()


@dataclass
class NadDomainsData:
    address: str = '0x758D80767a751fc1634f579D76e1CcaAb3485c9c'
    abi: str = open('./assets/abi/nad_domains.json', 'r').read()
from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

def test_usdt_1(usdt,stratms, ibCurvePool,Strategy, accounts, ib3CRV,ibyvault, orb,rewards,chain,strategy_usdt_ib,live_usdt_vault, ychad, gov,strategist, interface):
    gov = stratms
    vault = live_usdt_vault
    strategy = strategy_usdt_ib
    currency = usdt
    yvault = ibyvault
    amount = 1000*1e6
    amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    print("slip: ", strategy._checkSlip(amount))
    print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 **256 -1 , {'from': yvault.governance()})
    #print("real: ", ibCurvePool.calc_token_amount(amounts, True))

    idl = Strategy.at(vault.withdrawalQueue(0))
    vault.updateStrategyDebtRatio(idl, 0 , {"from": gov})
    debt_ratio = 9500
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    idl.harvest({'from': gov})

    strategy.harvest({'from': strategist})
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)

    ibcrvStrat = Strategy.at(ibyvault.withdrawalQueue(0))
    vGov = accounts.at(ibyvault.governance(), force=True)
    chain.sleep(201600)
    chain.mine(1)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

def test_migrate(usdt,stratms, ibCurvePool,Strategy, accounts, ib3CRV,ibyvault, orb,rewards,chain,strategy_usdt_ib,live_usdt_vault, ychad, gov,strategist, interface):
    gov = stratms
    vault = live_usdt_vault
    strategy = strategy_usdt_ib
    currency = usdt
    yvault = ibyvault
    
    yvault.setDepositLimit(2 **256 -1 , {'from': yvault.governance()})
    #print("real: ", ibCurvePool.calc_token_amount(amounts, True))

    idl = Strategy.at(vault.withdrawalQueue(0))
    vault.updateStrategyDebtRatio(idl, 0 , {"from": gov})
    debt_ratio = 9500
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    idl.harvest({'from': gov})

    strategy.harvest({'from': strategist})
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)

    ibcrvStrat = Strategy.at(ibyvault.withdrawalQueue(0))
    vGov = accounts.at(ibyvault.governance(), force=True)
    chain.sleep(201600)
    chain.mine(1)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    
    strategy.harvest({'from': strategist})

    tx = strategy.cloneSingleSidedCurve(vault, strategist, strategist, strategist, 500_000*1e6, 3600, 500, ibCurvePool, ib3CRV, ibyvault,3, True)
    new_strategy = Strategy.at(tx.return_value)

    vault.migrateStrategy(strategy, new_strategy, {'from': gov})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    new_strategy.harvest({'from': strategist})
    assert yvault.balanceOf(new_strategy) > 0
    assert yvault.balanceOf(strategy) == 0
    assert strategy.estimatedTotalAssets() == 0
    assert new_strategy.estimatedTotalAssets() > 0
    genericStateOfStrat(new_strategy, currency, vault)
    genericStateOfVault(vault, currency)
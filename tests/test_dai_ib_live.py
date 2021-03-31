from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import (
    genericStateOfStrat,
    genericStateOfVault,
    genericStateOfStrat030,
)
import random
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")


def test_dai_1(
    usdt,
    stratms,
    whale,
    Strategy,
    ibCurvePool,
    strategy_dai_ib,
    accounts,
    ib3CRV,
    ibyvault,
    orb,
    rewards,
    chain,
    strategy_usdt_ib,
    live_vault_dai,
    ychad,
    gov,
    strategist,
    interface,
):

    vault = live_vault_dai
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_dai_ib

    yvault = ibyvault
    # amount = 1000*1e6
    # amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    # print("slip: ", strategy._checkSlip(amount))
    # print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 ** 256 - 1, {"from": yvault.governance()})
    # print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    idl = Strategy.at(vault.withdrawalQueue(1))
    vault.updateStrategyDebtRatio(idl, 0, {"from": gov})
    debt_ratio = 2000
    # v0.3.0
    vault.addStrategy(strategy, debt_ratio, 0, 1000, {"from": gov})
    idl.harvest({"from": gov})
    idl.harvest({"from": gov})

    strategy.harvest({"from": strategist})
    ppsB = strategy.estimatedTotalAssets()
    print("est ", strategy.estimatedTotalAssets() / 1e18)
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)

    ibcrvStrat = Strategy.at(ibyvault.withdrawalQueue(0))

    vGov = accounts.at(ibyvault.governance(), force=True)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(604800)
    chain.mine(1)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    print(
        "profit ", (((strategy.estimatedTotalAssets() - ppsB) * 52) / ppsB) * 100, "%"
    )

    strategy.harvest({"from": strategist})
    print(vault.strategies(strategy))
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.updateDontInvest(True, {"from": strategist})
    strategy.harvest({"from": strategist})
    strategy.harvest({"from": strategist})
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)


def test_migrate(
    usdt,
    stratms,
    whale,
    Strategy,
    strategy_dai_ib,
    accounts,
    ibCurvePool,
    ib3CRV,
    ibyvault,
    orb,
    rewards,
    chain,
    strategy_usdt_ib,
    live_vault_dai,
    ychad,
    gov,
    strategist,
    interface,
):

    vault = live_vault_dai
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_dai_ib

    yvault = ibyvault
    # amount = 1000*1e6
    # amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    # print("slip: ", strategy._checkSlip(amount))
    # print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 ** 256 - 1, {"from": yvault.governance()})
    # print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    idl = Strategy.at(vault.withdrawalQueue(1))
    vault.updateStrategyDebtRatio(idl, 0, {"from": gov})
    debt_ratio = 2000
    # v0.3.0
    vault.addStrategy(strategy, debt_ratio, 0, 1000, {"from": gov})
    idl.harvest({"from": gov})
    idl.harvest({"from": gov})

    strategy.harvest({"from": strategist})
    ppsB = strategy.estimatedTotalAssets()
    print("est ", strategy.estimatedTotalAssets() / 1e18)
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)

    ibcrvStrat = Strategy.at(ibyvault.withdrawalQueue(0))

    vGov = accounts.at(ibyvault.governance(), force=True)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(604800)
    chain.mine(1)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    print(
        "profit ", (((strategy.estimatedTotalAssets() - ppsB) * 52) / ppsB) * 100, "%"
    )

    strategy.harvest({"from": strategist})

    tx = strategy.cloneSingleSidedCurve(
        vault,
        strategist,
        strategist,
        strategist,
        1 * 1e30,
        0,
        500,
        ibCurvePool,
        ib3CRV,
        ibyvault,
        3,
        True,
        {"from": strategist},
    )
    new_strat = Strategy.at(tx.return_value)

    vault.migrateStrategy(strategy, new_strat, {"from": gov})
    assert strategy.estimatedTotalAssets() == 0

    assert new_strat.estimatedTotalAssets() > 0
    new_strat.harvest({"from": strategist})

    ppsB = new_strat.estimatedTotalAssets()

    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(604800)
    chain.mine(1)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    print(
        "profit ", (((new_strat.estimatedTotalAssets() - ppsB) * 52) / ppsB) * 100, "%"
    )
    new_strat.harvest({"from": strategist})

    genericStateOfStrat030(new_strat, currency, vault)
    genericStateOfVault(vault, currency)

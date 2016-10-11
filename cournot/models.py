import math
from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
from random import randint

doc = """
In Cournot competition, firms simultaneously decide the units of products to
manufacture. The unit selling price depends on the total units produced. In
this implementation, there are 2 firms competing for 1 period.
"""


class Constants(BaseConstants):
    name_in_url = 'cournot'
    players_per_group = 3
    num_rounds = 4

    instructions_template = 'cournot/Instructions.html'

    base_points = 50
    # Total production capacity of all players
    total_capacity = 60

    R = 1000
    p = 2000
    pR = p * R


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(
        doc="""Unit price: P = T - \sum U_i, where T is total capacity and U_i is the number of units produced by player i"""
    )

    total_units = models.PositiveIntegerField(
        doc="""Total units produced by all players"""
    )

    def set_payoffs(self):
        Bank.make_decision(self.get_players())


class Player(BasePlayer):
    FITNESS_FUNCTIONS = [
        dict(function=lambda x: x * x, func_to_string="x^2"),
        dict(function=lambda x: x * x * 2, func_to_string="2 * x^2"),
        dict(function=lambda x: x * x * 4, func_to_string="4 * x^2")
    ]

    fitness_function = None

    units = models.PositiveIntegerField(
        min=0, max=Constants.p,
        doc="""Quantity of units to produce"""
    )

    def get_fitness_function_to_string(self):
        return self.get_fitness_function().get('func_to_string')

    def get_fitness_function(self):
        if self.fitness_function is None:
            self.fitness_function = Player.FITNESS_FUNCTIONS[self.id_in_group - 1]

        return self.fitness_function

    def other_player(self):
        return self.get_others_in_group()[0]

    def get_fitness_function_value(self):
        return c(Constants.pR - self.get_fitness_function().get('function')(self.payoff))


class Bank():
    @staticmethod
    def make_decision(players):
        pool = Bank.divide_resources(players)
        Bank.divide_remained_resources(pool, players)

    @staticmethod
    def divide_resources(players):
        sorted_players_list = sorted(players, key=lambda player: player.units)
        players_count = len(sorted_players_list)
        pool = Constants.R
        avg = int(round(pool / players_count))
        for player in sorted_players_list:
            if player.units <= avg:
                player.payoff = player.units
            else:
                player.payoff = avg
            pool -= player.payoff
            players_count -= 1
            if players_count > 0:
                avg = int(round(pool / players_count))
        return pool

    @staticmethod
    def divide_remained_resources(pool, players):
        if pool > 0:
            avg = int(round(pool / len(players)))
            for player in players:
                player.payoff += avg
